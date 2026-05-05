"""
reranker.py — Cross-encoder rerank dùng AITeamVN/Vietnamese_Reranker (fp16 trên GPU).

Dùng `transformers.AutoModelForSequenceClassification` trực tiếp thay vì
`sentence_transformers.CrossEncoder` để né lỗi `Unrecognized processing class`
(CrossEncoder gọi AutoProcessor nội bộ, không tương thích với một số reranker VN).

Pipeline:
  1. Nhận list[Hit] thô từ Qdrant + query
  2. Tokenize cặp (query, content) → model.logits → score
  3. Dedup theo `article` (= neo4j_id) — 1 article giữ chunk có score cao nhất
  4. Trả top_k đã sort theo rerank score giảm dần
"""
from __future__ import annotations

from typing import Any, List

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Reranker:
    """Lazy-load cross-encoder fp16."""

    MODEL_NAME = "AITeamVN/Vietnamese_Reranker"
    MAX_LENGTH = 512
    BATCH_SIZE = 16

    def __init__(self, device: str = "gpu", use_half: bool = True):
        self.device = self._resolve_device(device)
        self.use_half = use_half and self.device.startswith("cuda")
        self._tok = None
        self._mdl = None

    @staticmethod
    def _resolve_device(device: str) -> str:
        d = (device or "").strip().lower()
        if d in {"gpu", "cuda", "cuda:0"}:
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA không khả dụng. Truyền device='cpu' nếu chạy không GPU."
                )
            return "cuda"
        return d or "cpu"

    def _load(self) -> None:
        if self._mdl is not None:
            return
        kwargs: dict[str, Any] = {"trust_remote_code": True}
        if self.use_half:
            kwargs["torch_dtype"] = torch.float16
        self._tok = AutoTokenizer.from_pretrained(self.MODEL_NAME, trust_remote_code=True)
        self._mdl = AutoModelForSequenceClassification.from_pretrained(
            self.MODEL_NAME, **kwargs
        ).eval().to(self.device)

    # ────────────────────────────────────────────────────────────────
    @torch.no_grad()
    def _score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        self._load()
        scores: list[float] = []
        for i in range(0, len(pairs), self.BATCH_SIZE):
            batch = pairs[i:i + self.BATCH_SIZE]
            qs = [p[0] for p in batch]
            ds = [p[1] for p in batch]
            inputs = self._tok(
                qs, ds,
                padding=True, truncation=True,
                max_length=self.MAX_LENGTH,
                return_tensors="pt",
            ).to(self.device)
            logits = self._mdl(**inputs).logits.float()
            # Cả hai trường hợp đều chuẩn hoá về [0, 1]:
            #  • 1 output  → sigmoid(logit)
            #  • 2 outputs → softmax(logits)[:, positive_class]
            if logits.shape[-1] == 1:
                batch_scores = torch.sigmoid(logits.view(-1))
            else:
                batch_scores = torch.softmax(logits, dim=-1)[:, -1]
            scores.extend(batch_scores.cpu().tolist())
        return scores

    # ────────────────────────────────────────────────────────────────
    def rerank(
        self,
        query: str,
        hits: list,
        top_k: int = 5,
        dedup_by_article: bool = True,
    ) -> List[dict]:
        if not hits:
            return []

        pairs = [(query, _payload(h).get("content", "")) for h in hits]
        scores = self._score_pairs(pairs)

        scored: list[dict] = []
        for h, s in zip(hits, scores):
            p = _payload(h)
            # Cosine với vector đã normalize → clamp về [0, 1] để đồng bộ
            dense = float(getattr(h, "score", 0.0))
            dense = max(0.0, min(1.0, dense))
            scored.append({
                "score":       float(s),       # đã ∈ [0, 1]
                "dense_score": dense,           # ∈ [0, 1]
                "neo4j_id":    p.get("article", ""),    # cầu sang Graph RAG
                "chunk_id":    p.get("chunk_id", ""),
                "chunk_type":  p.get("chunk_type", ""),
                "law_id":      p.get("law_id", ""),
                "article":     p.get("article", ""),
                "clause":      p.get("clause"),
                "points":      p.get("points", []),
                "content":     p.get("content", ""),
                "refs":        p.get("refs", []),
                "metadata":    p.get("metadata", {}),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        if dedup_by_article:
            seen: set[str] = set()
            deduped: list[dict] = []
            for r in scored:
                k = r["neo4j_id"] or r["chunk_id"]
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(r)
            scored = deduped

        return scored[:top_k]


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def _payload(hit: Any) -> dict:
    """Hỗ trợ cả Qdrant ScoredPoint object lẫn dict."""
    if isinstance(hit, dict):
        return hit.get("payload", {}) or {}
    return getattr(hit, "payload", {}) or {}


def format_context_for_llm(reranked: List[dict]) -> str:
    """Format các chunks đã rerank thành context string cho LLM."""
    parts: list[str] = []
    for i, r in enumerate(reranked, 1):
        meta = r.get("metadata", {}) or {}
        article_label = meta.get("article_label") or r.get("article", "")
        clause_label  = meta.get("clause_label")
        header = f"[{i}] {r.get('law_id', '')} | {article_label}"
        if clause_label:
            header += f" — {clause_label}"
        parts.append(f"{header}\n{r['content']}")
    return "\n\n---\n\n".join(parts)
