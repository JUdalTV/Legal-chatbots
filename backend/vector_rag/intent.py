"""
intent.py — Heuristic phân loại query intent → top_k.

  lookup     k=4   "Điều 15 nói gì?", "Khoản 2 Điều 11..."
  thematic   k=5   "trách nhiệm doanh nghiệp viễn thông"
  compare    k=6   "khác nhau giữa", "trường hợp", "nếu/thì"
  cross_law  k=6   "theo Luật ... và Luật ..."

Default `thematic` (k=10) — chủ đề rộng là tình huống phổ biến nhất.
"""
from __future__ import annotations

import re


_K_BY_INTENT = {
    "lookup":    4,
    "thematic":  6,
    "compare":   6,
    "cross_law": 6,
}

_RX_LOOKUP = re.compile(
    r"\b("
    r"điều\s+\d+|khoản\s+\d+|điểm\s+[a-zđ]\b"
    r"|chương\s+(?:[ivx]+|\d+)"
    r"|mục\s+\d+"
    r"|phụ\s+lục"
    r")\b",
    re.IGNORECASE,
)

_RX_COMPARE = re.compile(
    r"\b("
    r"so\s+sánh|khác\s+nhau|khác\s+biệt|phân\s+biệt"
    r"|trường\s+hợp\s+nào|nếu.+thì|trong\s+khi|còn\s+nếu"
    r"|điều\s+kiện\s+(?:nào|gì)|được\s+phép\s+hay"
    r")\b",
    re.IGNORECASE,
)

# 2 lần "Luật" trở lên trong cùng query, hoặc có "liên quan đến"/"theo cả" + multiple law mentions
_RX_LAW_MENTION = re.compile(r"\bluật\s+\w+", re.IGNORECASE)
_RX_CROSS_LAW_HINT = re.compile(
    r"\b(liên\s+quan\s+đến|kết\s+hợp|đối\s+chiếu|theo\s+cả|cùng\s+với)\b",
    re.IGNORECASE,
)


def classify_intent(query: str) -> str:
    """Heuristic — không gọi LLM."""
    q = query.strip()
    if not q:
        return "thematic"

    # cross_law thắng trước nếu thấy ≥ 2 mention "Luật X" hoặc cụm so sánh + Luật
    law_hits = len(_RX_LAW_MENTION.findall(q))
    if law_hits >= 2 or (law_hits >= 1 and _RX_CROSS_LAW_HINT.search(q)):
        return "cross_law"

    if _RX_LOOKUP.search(q):
        return "lookup"

    if _RX_COMPARE.search(q):
        return "compare"

    return "thematic"


def get_k(intent: str) -> int:
    return _K_BY_INTENT.get(intent, _K_BY_INTENT["thematic"])


def extract_article_number(query: str) -> str | None:
    """Return the article number from lookup queries such as 'Điều 10'."""
    m = re.search(r"\bđiều\s+(\d+[a-z]?)\b", query.strip(), re.IGNORECASE)
    return m.group(1) if m else None
