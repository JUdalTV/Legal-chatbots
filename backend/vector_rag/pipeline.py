"""
pipeline.py — Vector RAG search pipeline.

  query
    → classify_intent → top_k
    → embedder.encode (fp16)
    → vector_store.search_dense (int8 + rescore với fp32 raw)
        ← Qdrant lấy oversample×top_k_search candidates ở int8, rescore fp32
    → reranker.rerank (cross-encoder fp16, dedup theo article)
    → list[dict]
"""
from __future__ import annotations

from typing import Any, Optional

from .embedder import Embedder
from .intent import classify_intent, extract_article_number, get_k
from .reranker import Reranker, format_context_for_llm
from .vector_store import VectorStore


class VectorRAGPipeline:
    """Embed → search int8 + rescore → cross-encoder rerank."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        device: str = "gpu",
        rerank_candidate_multiplier: int = 3,   # search top_k * 3 → rerank
        oversampling: float = 2.0,              # Qdrant int8 oversampling
        min_rerank_score: float = 0.0,
    ):
        self.embedder = Embedder(device=device)
        self.reranker = Reranker(device=device)
        self.store    = VectorStore(host=qdrant_host, port=qdrant_port)
        self.rerank_candidate_multiplier = rerank_candidate_multiplier
        self.oversampling = oversampling
        self.min_rerank_score = min_rerank_score

    # ────────────────────────────────────────────────────────────────
    def search(
        self,
        query: str,
        *,
        law_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
        top_k: Optional[int] = None,            # override get_k
        min_rerank_score: Optional[float] = None,
    ) -> dict:
        """
        Trả dict:
          { intent, top_k, results: [reranked dicts], context: formatted-string }
        """
        intent = classify_intent(query)
        k = top_k or get_k(intent)

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

        # Embed query
        q_vec = self.embedder.encode([query], show_progress=False)[0]

        # Dense search (int8 → rescore fp32). Lấy nhiều hơn top_k để rerank chọn lại
        n_candidates = max(k * self.rerank_candidate_multiplier, k + 5)
        hits = self.store.search_dense(
            query_vector=q_vec,
            top_k=n_candidates,
            law_id=law_id,
            chunk_type=chunk_type,
            oversampling=self.oversampling,
        )

        # Cross-encoder rerank + dedup theo article. Return all candidates first so
        # score filtering does not keep weak chunks just because they were in top_k.
        reranked_all = self.reranker.rerank(
            query, hits, top_k=n_candidates, dedup_by_article=True
        )
        threshold = self.min_rerank_score if min_rerank_score is None else min_rerank_score
        reranked = [r for r in reranked_all if r["score"] >= threshold][:k]

        return {
            "intent":  intent,
            "top_k":   k,
            "results": reranked,
            "context": format_context_for_llm(reranked),
        }


def _payload(point: Any) -> dict:
    return getattr(point, "payload", {}) or {}


def _point_to_result(point: Any) -> dict:
    p = _payload(point)
    return {
        "score":       float(getattr(point, "score", 999.0) or 999.0),
        "dense_score": float(getattr(point, "score", 0.0) or 0.0),
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
        return (order.get(p.get("chunk_type", ""), 9), _natural_clause_key(str(clause)), p.get("chunk_id", ""))

    return sorted(points, key=key)


def _natural_clause_key(value: str) -> tuple[int, str]:
    import re

    m = re.search(r"\d+", value)
    return (int(m.group(0)) if m else 0, value)
