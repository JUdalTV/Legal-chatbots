"""
fusion.py — RRF (Reciprocal Rank Fusion) + MMR (Maximal Marginal Relevance).

  rrf_fuse(rankings)   → list[Hit] đã merge & sort theo RRF score
  mmr_select(items, …) → top_k items đa dạng theo cosine
"""
from __future__ import annotations

import math
from typing import Any, Callable, Iterable, Sequence


# ════════════════════════════════════════════════════════════════════
# RRF
# ════════════════════════════════════════════════════════════════════
def rrf_fuse(
    rankings: Sequence[Sequence[Any]],
    *,
    k: int = 60,
    id_fn: Callable[[Any], str] | None = None,
) -> list[Any]:
    """
    Reciprocal Rank Fusion. `rankings` là list các ranking — mỗi ranking đã
    sort theo độ liên quan giảm dần. Trả ranking duy nhất, dedup theo id.

    Mỗi item nhận điểm:
        rrf_score = Σ 1 / (k + rank_in_list_i)   (rank 1-based)
    """
    if id_fn is None:
        id_fn = _default_id_fn

    score: dict[str, float] = {}
    repr_obj: dict[str, Any] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            iid = id_fn(item)
            if not iid:
                continue
            score[iid] = score.get(iid, 0.0) + 1.0 / (k + rank)
            # giữ object đại diện đầu tiên (thường đến từ nguồn xếp cao hơn)
            repr_obj.setdefault(iid, item)

    fused = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    return [repr_obj[iid] for iid, _ in fused]


def _default_id_fn(hit: Any) -> str:
    if isinstance(hit, dict):
        p = hit.get("payload", {}) or {}
        return p.get("chunk_id") or hit.get("chunk_id") or hit.get("id") or ""
    p = getattr(hit, "payload", {}) or {}
    return p.get("chunk_id") or str(getattr(hit, "id", "") or "")


# ════════════════════════════════════════════════════════════════════
# MMR
# ════════════════════════════════════════════════════════════════════
def mmr_select(
    items: Sequence[dict],
    vectors: Sequence[Sequence[float]],
    *,
    top_k: int,
    lambda_: float = 0.5,
    relevance_key: str = "score",
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn top_k items vừa relevant vừa đa dạng.

      mmr(d) = λ·rel(d) − (1−λ)·max_{s∈selected} cos(d, s)

    Giả định `vectors[i]` là dense embedding (đã L2-normalize HOẶC tự normalize).
    """
    if not items or top_k <= 0:
        return []
    if len(items) <= top_k:
        return list(items)

    # Normalize 1 lần
    vecs = [_l2_normalize(v) for v in vectors]
    rels = [float(it.get(relevance_key, 0.0)) for it in items]

    selected_idx: list[int] = []
    candidate_idx: list[int] = list(range(len(items)))

    while candidate_idx and len(selected_idx) < top_k:
        if not selected_idx:
            best = max(candidate_idx, key=lambda i: rels[i])
        else:
            def mmr_score(i: int) -> float:
                max_sim = max(_dot(vecs[i], vecs[s]) for s in selected_idx)
                return lambda_ * rels[i] - (1 - lambda_) * max_sim
            best = max(candidate_idx, key=mmr_score)
        selected_idx.append(best)
        candidate_idx.remove(best)

    return [items[i] for i in selected_idx]


def _l2_normalize(v: Sequence[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def dedup_by_article(
    items: Iterable[dict],
    key: str = "article",
    *,
    by_clause: bool = True,
) -> list[dict]:
    """Giữ chunk score cao nhất per (article, clause).

    Items phải đã sort theo score giảm dần. Khi `by_clause=True`, hai chunk
    cùng article nhưng khác `clause` (vd Khoản 1 vs Khoản 2 của Điều 3) đều
    được giữ lại — fix cho câu hỏi cần phân biệt khoản trong cùng Điều.
    """
    seen: set = set()
    out: list[dict] = []
    for it in items:
        primary = it.get(key) or it.get("neo4j_id") or it.get("chunk_id")
        if not primary:
            continue
        dedup_key = (primary, it.get("clause") or "") if by_clause else primary
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        out.append(it)
    return out
