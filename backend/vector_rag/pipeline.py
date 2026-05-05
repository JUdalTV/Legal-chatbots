"""
pipeline.py — Vector RAG search pipeline.

  query
    → classify_intent → top_k
    → (intent=lookup + law_id) ⇒ direct article fetch (skip search)
    ↓
    → embed query (dense, GPU) ┐
    → encode query (sparse BM25, CPU) ┘ song song
    ↓
    → search_dense (int8 + rescore) ┐
    → search_sparse (BM25)          ┘ song song
    ↓
    → RRF fuse (k=60)
    → CrossEncoder rerank ([0,1] sigmoid)
    → threshold filter
    → MMR diversity (λ=0.5)  hoặc dedup_by_article
    → list[dict]
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from .embedder import Embedder
from .fusion import dedup_by_article, mmr_select, rrf_fuse
from .intent import classify_intent, extract_article_number, get_k
from .reranker import Reranker, format_context_for_llm
from .sparse_encoder import DEFAULT_BM25_PATH, BM25Encoder
from .vector_store import VectorStore


class VectorRAGPipeline:
    """Hybrid dense+sparse → RRF → rerank → MMR."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        device: str = "gpu",
        rerank_candidate_multiplier: int = 4,
        oversampling: float = 2.0,
        min_rerank_score: float = 0.0,
        bm25_path: str | Path = DEFAULT_BM25_PATH,
        rrf_k: int = 60,
        mmr_enabled: bool = True,
        mmr_lambda: float = 0.5,
    ):
        self.embedder = Embedder(device=device)
        self.reranker = Reranker(device=device)
        self.store    = VectorStore(host=qdrant_host, port=qdrant_port)
        self.rerank_candidate_multiplier = rerank_candidate_multiplier
        self.oversampling = oversampling
        self.min_rerank_score = min_rerank_score
        self.rrf_k = rrf_k
        self.mmr_enabled = mmr_enabled
        self.mmr_lambda  = mmr_lambda

        # Lazy-load BM25 state. Nếu không có file → sparse search bị skip.
        self.bm25: Optional[BM25Encoder] = None
        self._bm25_path = Path(bm25_path)
        if self._bm25_path.exists():
            try:
                self.bm25 = BM25Encoder().load(self._bm25_path)
            except Exception as ex:
                print(f"[pipeline] không load được BM25 state: {ex}")
                self.bm25 = None

    # ════════════════════════════════════════════════════════════════
    def search(
        self,
        query: str,
        *,
        law_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
        top_k: Optional[int] = None,
        min_rerank_score: Optional[float] = None,
    ) -> dict:
        """Trả {intent, top_k, results, context}."""
        intent = classify_intent(query)
        k = top_k or get_k(intent)

        # ── Direct lookup theo article id ──────────────────────────
        if intent == "lookup" and law_id:
            article_no = extract_article_number(query)
            if article_no:
                article_id = f"{law_id}_dieu_{article_no}"
                points = self.store.get_by_article(article_id, law_id=law_id)
                if points:
                    results = [_point_to_result(p) for p in _sort_article_points(points)]
                    return {
                        "intent":  intent,
                        "top_k":   len(results),
                        "results": results,
                        "context": format_context_for_llm(results),
                    }

        # ── Encode query: dense (GPU) + sparse (CPU) song song ────
        with ThreadPoolExecutor(max_workers=2) as ex:
            dense_fut = ex.submit(self.embedder.encode, [query], show_progress=False)
            sparse_fut = ex.submit(
                self.bm25.encode_query, query
            ) if self.bm25 else None

            q_dense = dense_fut.result()[0]
            q_sparse = sparse_fut.result() if sparse_fut else ([], [])

        # ── Search dense + sparse song song ───────────────────────
        n_candidates = max(k * self.rerank_candidate_multiplier, k + 8)
        with ThreadPoolExecutor(max_workers=2) as ex:
            dense_fut = ex.submit(
                self.store.search_dense,
                query_vector=q_dense, top_k=n_candidates,
                law_id=law_id, chunk_type=chunk_type,
                oversampling=self.oversampling,
                with_vectors=self.mmr_enabled,
            )
            sparse_hits: list = []
            if q_sparse[0]:
                sparse_fut = ex.submit(
                    self.store.search_sparse,
                    indices=q_sparse[0], values=q_sparse[1],
                    top_k=n_candidates, law_id=law_id, chunk_type=chunk_type,
                )
            else:
                sparse_fut = None

            dense_hits  = dense_fut.result()
            sparse_hits = sparse_fut.result() if sparse_fut else []

        # ── RRF fuse 2 rankings ──────────────────────────────────
        fused = rrf_fuse([dense_hits, sparse_hits], k=self.rrf_k)
        if not fused:
            return {"intent": intent, "top_k": k, "results": [], "context": ""}

        # ── Cross-encoder rerank (giữ nguyên candidates, chưa dedup) ──
        reranked_all = self.reranker.rerank(
            query, fused, top_k=len(fused), dedup_by_article=False,
        )

        # ── Threshold filter (rerank score đã ∈ [0,1]) ─────────────
        threshold = (
            self.min_rerank_score if min_rerank_score is None else min_rerank_score
        )
        candidates = [r for r in reranked_all if r["score"] >= threshold]
        if not candidates:
            return {"intent": intent, "top_k": k, "results": [], "context": ""}

        # ── MMR diversity, OR dedup by article ─────────────────────
        if self.mmr_enabled and len(candidates) > k:
            vecs = self._candidate_vectors(candidates, dense_hits)
            final = mmr_select(
                candidates, vecs, top_k=k, lambda_=self.mmr_lambda,
            )
        else:
            final = dedup_by_article(candidates)[:k]

        return {
            "intent":  intent,
            "top_k":   k,
            "results": final,
            "context": format_context_for_llm(final),
        }

    # ────────────────────────────────────────────────────────────────
    def _candidate_vectors(
        self,
        candidates: list[dict],
        dense_hits: list,
    ) -> list[list[float]]:
        """
        Lấy dense vector cho từng candidate cho MMR.
        Strategy:
          1. Map từ chunk_id → vector trong dense_hits (nếu có with_vectors=True)
          2. Candidate nào không có → re-embed content (1 batch nhỏ)
        """
        vec_map: dict[str, list[float]] = {}
        for h in dense_hits:
            v = getattr(h, "vector", None)
            if v is None:
                continue
            if isinstance(v, dict):
                v = v.get("dense") or v.get("default")
            if v is None:
                continue
            payload = getattr(h, "payload", {}) or {}
            cid = payload.get("chunk_id") or str(getattr(h, "id", ""))
            vec_map[cid] = list(v)

        out: list[list[float]] = []
        missing_idx: list[int] = []
        for i, c in enumerate(candidates):
            v = vec_map.get(c.get("chunk_id"))
            if v:
                out.append(v)
            else:
                out.append([])
                missing_idx.append(i)

        if missing_idx:
            texts = [candidates[i]["content"] for i in missing_idx]
            fresh = self.embedder.encode(texts, show_progress=False)
            for i, v in zip(missing_idx, fresh):
                out[i] = list(v)

        return out


# ════════════════════════════════════════════════════════════════════
# Helpers cho lookup-mode
# ════════════════════════════════════════════════════════════════════
def _payload(point: Any) -> dict:
    return getattr(point, "payload", {}) or {}


def _point_to_result(point: Any) -> dict:
    p = _payload(point)
    raw_dense = float(getattr(point, "score", 0.0) or 0.0)
    dense = max(0.0, min(1.0, raw_dense))
    return {
        "score":       1.0,    # direct match — coi như chắc chắn
        "dense_score": dense,
        "neo4j_id":    p.get("article", ""),
        "chunk_id":    p.get("chunk_id", ""),
        "chunk_type":  p.get("chunk_type", ""),
        "law_id":      p.get("law_id", ""),
        "article":     p.get("article", ""),
        "clause":      p.get("clause"),
        "points":      p.get("points", []),
        "content":     p.get("content", ""),
        "refs":        p.get("refs", []),
        "metadata":    p.get("metadata", {}),
    }


def _sort_article_points(points: list) -> list:
    order = {"article_summary": 0, "clause": 1, "point_group": 2}

    def key(point: Any) -> tuple:
        p = _payload(point)
        meta = p.get("metadata", {}) or {}
        clause = p.get("clause") or meta.get("clause_no") or ""
        return (
            order.get(p.get("chunk_type", ""), 9),
            _natural_clause_key(str(clause)),
            p.get("chunk_id", ""),
        )

    return sorted(points, key=key)


def _natural_clause_key(value: str) -> tuple[int, str]:
    m = re.search(r"\d+", value)
    return (int(m.group(0)) if m else 0, value)
