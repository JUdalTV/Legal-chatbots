"""
Rule-based extractor cho quan hệ THAM_CHIEU (REFERS_TO)
giữa các Điều của cùng một luật hoặc liên luật.

Patterns nhận diện:
  - "theo Điều X" -> cùng luật
  - "quy định tại khoản N Điều X"
  - "căn cứ Điều X Luật Y số NN/YYYY/QH" -> liên luật
"""

from __future__ import annotations

import re

# Pattern Điều cùng luật
_REF_LOCAL = re.compile(
    r"(?:theo\s+quy\s+định\s+tại|quy\s+định\s+tại|căn\s+cứ\s+vào|căn\s+cứ|theo|tại)\s+"
    r"(?:khoản\s+\d+(?:[,\s]*(?:và\s+khoản\s+\d+)?)?\s+)?"
    r"[ĐĐđ]iều\s+(\d+[a-z]?)",
    re.IGNORECASE,
)

# Pattern Điều + Luật khác (số hiệu)
_REF_CROSS = re.compile(
    r"[ĐĐđ]iều\s+(\d+[a-z]?)\s+"
    r"(?:của\s+)?(?:Luật|Nghị\s+định|Pháp\s+lệnh|Nghị\s+quyết)"
    r"[^\n,;.]{0,80}?\s+số\s+(\d+/\d{4}/\w+)",
    re.IGNORECASE,
)


def extract_tham_chieu(content: str, from_dieu_so: str, law_name: str) -> list[dict]:
    """
    Trích các quan hệ tham chiếu từ nội dung 1 Điều.

    Trả list dict:
      {
        "from_id":     "<law_name>_dieu_<from_dieu_so>",
        "to_dieu_so":  "<số Điều đích>",
        "to_law_id":   "<law_name>" hoặc số hiệu nếu liên luật,
        "cross_law":   bool,
        "context":     "<đoạn text 60 ký tự quanh match>",
      }
    """
    refs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    matched_ranges: list[tuple[int, int]] = []

    # Match cross-law trước vì regex specific hơn. Claim span dù ref bị dedupe,
    # để local extractor không ăn lại cùng vùng text.
    for match in _REF_CROSS.finditer(content):
        span = (match.start(), match.end())
        matched_ranges.append(span)

        to_dieu_so = match.group(1)
        to_so_hieu = match.group(2)
        key = (to_so_hieu, to_dieu_so)
        if key in seen:
            continue

        seen.add(key)
        refs.append(
            {
                "from_id": f"{law_name}_dieu_{from_dieu_so}",
                "to_dieu_so": to_dieu_so,
                "to_law_id": to_so_hieu,
                "cross_law": True,
                "context": _ctx(content, match.start(), match.end()),
            }
        )

    # Local chỉ nhận các span chưa bị cross-law hoặc local trước đó claim.
    for match in _REF_LOCAL.finditer(content):
        span = (match.start(), match.end())
        if _has_overlap(span, matched_ranges):
            continue

        to_dieu_so = match.group(1)
        if to_dieu_so == from_dieu_so:
            continue

        key = (law_name, to_dieu_so)
        if key in seen:
            continue

        seen.add(key)
        matched_ranges.append(span)
        refs.append(
            {
                "from_id": f"{law_name}_dieu_{from_dieu_so}",
                "to_dieu_so": to_dieu_so,
                "to_law_id": law_name,
                "cross_law": False,
                "context": _ctx(content, match.start(), match.end()),
            }
        )

    return refs


def _ctx(text: str, start: int, end: int, pad: int = 60) -> str:
    s = max(0, start - pad)
    e = min(len(text), end + pad)
    return text[s:e].replace("\n", " ").strip()


def _has_overlap(span: tuple[int, int], ranges: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < other_end and other_start < end for other_start, other_end in ranges)
