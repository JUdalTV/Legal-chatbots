"""
intent.py — Heuristic phân loại query intent → top_k.

Factual (trích nguyên văn — scaffold chặt):
  lookup        k=4   "Điều 15 nói gì?", "Khoản 2 Điều 11..."
  cross_law     k=6   "theo Luật ... và Luật ..."
  compare       k=6   "khác nhau giữa", "phân biệt"
  penalty       k=6   "mức phạt", "xử phạt thế nào", "chế tài"
  procedure     k=8   "thủ tục", "quy trình", "các bước"
  definition    k=4   "là gì", "định nghĩa", "khái niệm"
  authority     k=6   "cơ quan nào", "ai có thẩm quyền"
  obligation    k=7   "nghĩa vụ", "phải làm gì", "buộc phải"
  liability     k=7   "chịu trách nhiệm", "trách nhiệm pháp lý"

Reasoning (suy luận — scaffold IRAC + practical impact):
  applicability k=7   "có thể... được không", "có áp dụng cho", "có được phép"
  gap_analysis  k=8   "luật có quy định rõ về X không", "có cơ chế giám sát"
  conclusion    k=6   "tổng hợp lại", "đánh giá chung", "kết luận"
  thematic      k=7   chủ đề rộng — default
"""
from __future__ import annotations

import re


_K_BY_INTENT = {
    "lookup":        4,
    "cross_law":     6,
    "compare":       6,
    "penalty":       6,
    "procedure":     8,
    "definition":    4,
    "authority":     6,
    "obligation":    7,
    "liability":     7,
    "applicability": 7,
    "gap_analysis":  8,
    "conclusion":    6,
    "thematic":      7,
}


# ─────────────────────────────────────────────────────────────────────
# Patterns (sắp theo priority — match trước thắng)
# ─────────────────────────────────────────────────────────────────────

_RX_LOOKUP = re.compile(
    r"\b("
    r"điều\s+\d+|khoản\s+\d+|điểm\s+[a-zđ]\b"
    r"|chương\s+(?:[ivx]+|\d+)"
    r"|mục\s+\d+"
    r"|phụ\s+lục"
    r")\b",
    re.IGNORECASE,
)

_RX_LAW_MENTION = re.compile(r"\bluật\s+\w+", re.IGNORECASE)
_RX_CROSS_LAW_HINT = re.compile(
    r"\b(liên\s+quan\s+đến|kết\s+hợp|đối\s+chiếu|theo\s+cả|cùng\s+với)\b",
    re.IGNORECASE,
)

_RX_DEFINITION = re.compile(
    r"("
    r"\blà\s+gì\b"
    r"|\bđịnh\s+nghĩa\b"
    r"|\bkhái\s+niệm\b"
    r"|\bđược\s+hiểu\s+là\b"
    r"|\bthế\s+nào\s+là\b"
    r"|\bnghĩa\s+(?:của|là)\b"
    r")",
    re.IGNORECASE,
)

_RX_AUTHORITY = re.compile(
    r"("
    r"\bcơ\s+quan\s+nào\b"
    r"|\bai\s+có\s+thẩm\s+quyền\b"
    r"|\bdo\s+ai\b"
    r"|\bthuộc\s+thẩm\s+quyền\b"
    r"|\bcơ\s+quan\s+(?:có\s+thẩm\s+quyền|quản\s+lý)"
    r"|\bgiao\s+cho\s+(?:cơ\s+quan|đơn\s+vị|ai)"
    r")",
    re.IGNORECASE,
)

_RX_PENALTY = re.compile(
    r"("
    r"\bxử\s+phạt\b"
    r"|\bmức\s+phạt\b"
    r"|\bphạt\s+(?:tiền|bao\s+nhiêu|là)\b"
    r"|\bchế\s+tài\b"
    r"|\bbiện\s+pháp\s+khắc\s+phục\b"
    r"|\bxử\s+lý\s+vi\s+phạm\b"
    r"|\bbị\s+phạt\b"
    r")",
    re.IGNORECASE,
)

_RX_LIABILITY = re.compile(
    r"("
    r"\bchịu\s+trách\s+nhiệm\b"
    r"|\btrách\s+nhiệm\s+(?:pháp\s+lý|hình\s+sự|dân\s+sự|hành\s+chính|bồi\s+thường|liên\s+đới)"
    r"|\bphải\s+bồi\s+thường\b"
    r"|\bliên\s+đới\s+(?:chịu|trách\s+nhiệm)\b"
    r")",
    re.IGNORECASE,
)

_RX_OBLIGATION = re.compile(
    r"("
    r"\bnghĩa\s+vụ\b"
    r"|\bphải\s+(?:làm\s+gì|thực\s+hiện)\b"
    r"|\bbuộc\s+phải\b"
    r"|\bbắt\s+buộc\b"
    r"|\bcó\s+trách\s+nhiệm\s+(?:thực\s+hiện|làm|báo\s+cáo|đảm\s+bảo)"
    r"|\byêu\s+cầu\s+đối\s+với\b"
    r")",
    re.IGNORECASE,
)

_RX_PROCEDURE = re.compile(
    r"("
    r"\bthủ\s+tục\b"
    r"|\bquy\s+trình\b"
    r"|\btrình\s+tự\b"
    r"|\bcác\s+bước\b"
    r"|\bhồ\s+sơ\s+(?:gồm|bao\s+gồm|cần)\b"
    r"|\bcách\s+thức\s+thực\s+hiện\b"
    r"|\bthực\s+hiện\s+(?:như\s+thế\s+nào|ra\s+sao)\b"
    r")",
    re.IGNORECASE,
)

_RX_GAP_ANALYSIS = re.compile(
    r"("
    r"\bluật\s+có\s+quy\s+định\s+(?:rõ|cụ\s+thể|chi\s+tiết)?\s*(?:về|cho)?\b"
    r"|\bcó\s+(?:cơ\s+chế|chế\s+tài|quy\s+định)\s+(?:nào\s+)?(?:cụ\s+thể\s+)?(?:về\s+)?\S+\s+(?:hay\s+)?không"
    r"|\bcó\s+(?:đầy\s+đủ|rõ\s+ràng|chi\s+tiết)\b"
    r"|\bcòn\s+(?:thiếu|chưa\s+có|chưa\s+rõ)\b"
    r"|\bkhoảng\s+trống\b"
    r"|\bbỏ\s+ngỏ\b"
    r")",
    re.IGNORECASE,
)

_RX_APPLICABILITY = re.compile(
    r"("
    r"có\s+(?:thể|phải|được)\s+\S+(?:\s+\S+){0,5}\s+(?:được\s+)?(?:hay\s+)?không"
    r"|có\s+(?:thuộc|nằm\s+trong|coi\s+là|tính\s+là|xem\s+là)\b"
    r"|(?:có\s+)?(?:được\s+phép|cho\s+phép|được\s+quyền)\b"
    r"|có\s+áp\s+dụng\b"
    r"|có\s+vi\s+phạm\b"
    r"|làm\s+\S+(?:\s+\S+){0,4}\s+được\s+không"
    r"|từ\s+\S+(?:\s+\S+){0,6}\s+có\s+thể\b"
    r")",
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

_RX_CONCLUSION = re.compile(
    r"("
    r"\btổng\s+hợp\s+(?:lại\b|chung\b)?"
    r"|\btổng\s+kết\b"
    r"|\bđánh\s+giá\s+(?:chung|tổng\s+thể)\b"
    r"|\bkết\s+luận\b"
    r"|\bnhìn\s+chung\b"
    r"|\btóm\s+lại\b"
    r")",
    re.IGNORECASE,
)


def classify_intent(query: str) -> str:
    """Heuristic — không gọi LLM. Priority: factual cụ thể → reasoning → default."""
    q = query.strip()
    if not q:
        return "thematic"

    # 1. Cross-law: ≥ 2 mention "Luật X" hoặc cụm liên kết + Luật.
    law_hits = len(_RX_LAW_MENTION.findall(q))
    if law_hits >= 2 or (law_hits >= 1 and _RX_CROSS_LAW_HINT.search(q)):
        return "cross_law"

    # 2. Lookup: chỉ rõ Điều/Khoản/Điểm → factual lookup.
    if _RX_LOOKUP.search(q):
        return "lookup"

    # 3. Definition: "X là gì", "định nghĩa X" — cần trích nguyên văn.
    if _RX_DEFINITION.search(q):
        return "definition"

    # 4. Authority: "cơ quan nào", "ai có thẩm quyền".
    if _RX_AUTHORITY.search(q):
        return "authority"

    # 5. Penalty trước liability: "xử phạt"/"mức phạt" cụ thể hơn "trách nhiệm".
    if _RX_PENALTY.search(q):
        return "penalty"

    # 6. Liability: "chịu trách nhiệm pháp lý/hình sự/dân sự".
    if _RX_LIABILITY.search(q):
        return "liability"

    # 7. Obligation: "nghĩa vụ", "phải thực hiện".
    if _RX_OBLIGATION.search(q):
        return "obligation"

    # 8. Procedure: "thủ tục", "quy trình", "các bước".
    if _RX_PROCEDURE.search(q):
        return "procedure"

    # 9. Gap analysis: "có quy định rõ về X không", "có cơ chế giám sát".
    if _RX_GAP_ANALYSIS.search(q):
        return "gap_analysis"

    # 10. Applicability: "có thể... được không", "có áp dụng cho".
    if _RX_APPLICABILITY.search(q):
        return "applicability"

    # 11. Compare: "so sánh", "khác nhau".
    if _RX_COMPARE.search(q):
        return "compare"

    # 12. Conclusion: "tổng hợp lại", "đánh giá chung".
    if _RX_CONCLUSION.search(q):
        return "conclusion"

    # 13. Default.
    return "thematic"


def get_k(intent: str) -> int:
    return _K_BY_INTENT.get(intent, _K_BY_INTENT["thematic"])


def extract_article_number(query: str) -> str | None:
    """Return the article number from lookup queries such as 'Điều 10'."""
    m = re.search(r"\bđiều\s+(\d+[a-z]?)\b", query.strip(), re.IGNORECASE)
    return m.group(1) if m else None
