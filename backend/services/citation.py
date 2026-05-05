"""
citation.py — Trích citations dạng `[Điều X, Khoản Y]` từ answer của LLM
và map sang sources retrieved (vector_results).

Output mỗi citation:
  {
    "raw":         "Điều 15 Khoản 2",
    "law_id":      "LuatAnNinhMang2025",
    "article":     "LuatAnNinhMang2025_dieu_15",
    "article_no":  "15",
    "clause_no":   "2",
    "matched":     bool,        # có nằm trong sources không
    "char_start":  int,
    "char_end":    int,
  }

Dùng để UI highlight + verify.
"""
from __future__ import annotations

import re
from typing import Iterable


# "Điều 15", "điều 15", "Điều 15 Khoản 2", "Khoản 2 Điều 15"
_RX_ART_FIRST = re.compile(
    r"[ĐĐđ]iều\s+(?P<a>\d+[a-z]?)(?:\s*,?\s*[Kk]ho[ảa]n\s+(?P<k>\d+))?",
    re.IGNORECASE,
)
_RX_CLAUSE_FIRST = re.compile(
    r"[Kk]ho[ảa]n\s+(?P<k>\d+)\s*[Đđ]iều\s+(?P<a>\d+[a-z]?)",
    re.IGNORECASE,
)


def extract_citations(
    answer: str,
    sources: Iterable[dict],
    *,
    default_law_id: str | None = None,
) -> list[dict]:
    """Trích Điều/Khoản từ answer, map sang sources qua field 'article'."""
    src_articles: dict[str, dict] = {}
    for s in sources:
        aid = s.get("article") or s.get("neo4j_id")
        if aid:
            src_articles[aid] = s

    citations: list[dict] = []
    seen_spans: list[tuple[int, int]] = []

    # Khoản X Điều Y match trước (specific hơn)
    for m in _RX_CLAUSE_FIRST.finditer(answer):
        _emit_citation(m, "k", "a", answer, src_articles, default_law_id,
                       citations, seen_spans)
    for m in _RX_ART_FIRST.finditer(answer):
        if _overlap(m.span(), seen_spans):
            continue
        _emit_citation(m, "k", "a", answer, src_articles, default_law_id,
                       citations, seen_spans)

    # Sắp theo vị trí xuất hiện
    citations.sort(key=lambda c: c["char_start"])
    return citations


def _emit_citation(
    m: re.Match, k_grp: str, a_grp: str,
    answer: str,
    src_articles: dict[str, dict],
    default_law_id: str | None,
    out: list[dict],
    seen_spans: list[tuple[int, int]],
) -> None:
    a = m.group(a_grp)
    k = m.groupdict().get(k_grp)
    if not a:
        return
    span = m.span()

    # Suy luận law_id: ưu tiên explicit từ context xung quanh
    law_id = _detect_law_id_around(answer, span) or default_law_id
    article_id = f"{law_id}_dieu_{a}" if law_id else None

    matched_src = src_articles.get(article_id) if article_id else None
    out.append({
        "raw":        m.group(0),
        "law_id":     law_id,
        "article":    article_id,
        "article_no": a,
        "clause_no":  k,
        "matched":    matched_src is not None,
        "char_start": span[0],
        "char_end":   span[1],
    })
    seen_spans.append(span)


# Heuristic suy luận law_id từ tên luật xung quanh trong answer
_LAW_NAME_RX = [
    (re.compile(r"Lu[âậ]t\s+An\s+ninh\s+m[ạa]ng",  re.IGNORECASE), "LuatAnNinhMang2025"),
    (re.compile(r"Lu[âậ]t\s+Vi[ễê]n\s+th[ôo]ng",   re.IGNORECASE), "LuatVienThong2023"),
    (re.compile(r"Lu[âậ]t\s+C[ôo]ng\s+ngh[ệe]\s+th[ôo]ng\s+tin", re.IGNORECASE), "LuatCNTT2006"),
]


def _detect_law_id_around(text: str, span: tuple[int, int], pad: int = 60) -> str | None:
    s, e = span
    window = text[max(0, s - pad): min(len(text), e + pad)]
    for rx, lid in _LAW_NAME_RX:
        if rx.search(window):
            return lid
    return None


def _overlap(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    s, e = span
    return any(s < e2 and s2 < e for s2, e2 in spans)


# ────────────────────────────────────────────────────────────────────
def annotate_answer(answer: str, citations: list[dict]) -> str:
    """Append [✓] cho citation matched, [?] cho không match → user thấy ngay."""
    if not citations:
        return answer
    # Insert markers từ phải sang trái (giữ char_start cũ vẫn đúng)
    out = list(answer)
    for c in sorted(citations, key=lambda x: x["char_end"], reverse=True):
        marker = " [✓]" if c["matched"] else " [?]"
        out.insert(c["char_end"], marker)
    return "".join(out)
