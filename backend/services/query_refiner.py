"""
query_refiner.py — LLM-driven query refinement (intent-aware).

Mục tiêu:
  - "Doanh nghiệp viễn thông phải làm gì?"
    → "Trách nhiệm và nghĩa vụ của doanh nghiệp viễn thông theo Luật Viễn thông
       2023 và Luật An ninh mạng 2025"
  - "điều 15"
    → "Nội dung Điều 15 Luật An ninh mạng 2025"

Trả về dict:
  { "refined": str, "objective": str }
- `refined` dùng cho retrieval (dense + sparse)
- `objective` (1-2 câu) dùng làm tín hiệu trong prompt LLM cuối
"""
from __future__ import annotations

import json
import re
from typing import Optional

from .llm_client import LLMClient


_LAW_DISPLAY: dict[str, str] = {
    "LuatAnNinhMang2025":  "Luật An ninh mạng số 116/2025/QH15",
    "LuatCNTT2025":        "Luật Công nghệ thông tin (văn bản hợp nhất 2025)",
    "LuatCNTT2006":        "Luật Công nghệ thông tin số 67/2006/QH11",
    "LuatVienThong2023":   "Luật Viễn thông số 24/2023/QH15",
}


_SYSTEM_BASE = """Bạn là chuyên gia tinh chỉnh câu hỏi pháp lý.
Nhiệm vụ:
1. Xác định MỤC TIÊU thực sự của người hỏi (1-2 câu, dùng cho hướng dẫn LLM trả lời).
2. Viết lại câu hỏi rõ ràng, đầy đủ keyword cho retrieval (giữ thuật ngữ pháp lý gốc, bổ sung context bị thiếu).

Các quy tắc:
- KHÔNG bịa số Điều/Khoản chưa được nhắc.
- Giữ số Điều/Khoản nếu có trong câu gốc.
- Câu refined phải ngắn gọn (<= 50 từ), chứa nhiều keyword pháp lý hữu ích.
- Trả về JSON thuần, KHÔNG markdown:
  {"objective": "...", "refined": "..."}"""


_LAW_RULE_FREE = """
QUY TẮC TUYỆT ĐỐI VỀ TÊN LUẬT (free mode — user chưa chọn luật cụ thể):
- Nếu câu gốc nêu RÕ tên luật (vd: "Luật CNTT", "Luật An ninh mạng", "Luật Viễn thông") → BẮT BUỘC giữ NGUYÊN tên luật đó. CẤM thay bằng luật khác.
- Nếu câu gốc KHÔNG nêu tên luật → KHÔNG được tự gắn tên luật cụ thể vào refined.
- Viết tắt được mở rộng: CNTT = Công nghệ thông tin, ANM = An ninh mạng, VT = Viễn thông."""


def _law_rule_locked(law_display: str) -> str:
    return f"""
QUY TẮC TUYỆT ĐỐI VỀ TÊN LUẬT (locked mode — user ĐÃ chọn luật cụ thể):
- LUẬT ĐANG TRA CỨU: "{law_display}".
- BẮT BUỘC viết refined bắt đầu bằng "Theo {law_display}, ..." HOẶC chèn cụm "trong {law_display}" làm context.
- TUYỆT ĐỐI CẤM nhắc tới bất kỳ luật KHÁC trong refined (kể cả khi câu gốc có nhắc).
  Vd: nếu câu gốc nói "so sánh Luật A và Luật B" mà luật đang tra cứu là "{law_display}" thì refined chỉ giữ phần liên quan đến "{law_display}".
- Giữ số Điều/Khoản từ câu gốc."""


def _build_system(law_id: Optional[str]) -> str:
    display = _LAW_DISPLAY.get(law_id or "")
    if display:
        return _SYSTEM_BASE + _law_rule_locked(display)
    return _SYSTEM_BASE + _LAW_RULE_FREE


def refine_query(
    query: str,
    *,
    intent: Optional[str] = None,
    law_id: Optional[str] = None,
    llm: Optional[LLMClient] = None,
    max_tokens: int = 256,
) -> dict:
    """Trả {original, intent, objective, refined}. Fail-soft: lỗi LLM → original.

    Nếu `law_id` được truyền, kích hoạt LOCKED MODE: refined bắt buộc nhắc tới
    đúng tên luật, KHÔNG được mention luật khác.
    """
    llm = llm or LLMClient()
    locked_display = _LAW_DISPLAY.get(law_id or "") if law_id else None
    user = f"Intent: {intent or 'unknown'}\nCâu hỏi gốc: {query}"
    messages = [
        {"role": "system", "content": _build_system(law_id)},
        {"role": "user",   "content": user},
    ]
    try:
        raw = llm.chat(
            messages, temperature=0.0, max_tokens=max_tokens,
            enable_thinking=False,
        )
        data = _extract_json(raw)
        refined   = (data.get("refined")   or "").strip() or query
        objective = (data.get("objective") or "").strip()
        # Safeguard 1: locked mode → refined PHẢI chứa luật được lock + KHÔNG có luật khác
        if locked_display and not _refined_locked_ok(refined, law_id):
            print(f"[query_refiner] locked mode vi phạm (law_id={law_id}) → ép prefix")
            refined = f"Theo {locked_display}, {query}"
        # Safeguard 2: free mode → catch khi LLM đổi/tự gắn luật
        elif not locked_display and _law_name_changed(query, refined):
            print(f"[query_refiner] free mode đổi tên luật → revert về query gốc")
            refined = query
    except Exception as ex:
        print(f"[query_refiner] fail-soft → dùng query gốc: {ex}")
        refined, objective = query, ""

    return {
        "original":  query,
        "intent":    intent,
        "objective": objective,
        "refined":   refined,
    }


_LAW_ALIAS_PATTERNS: dict[str, re.Pattern] = {
    "ANM":  re.compile(r"\b(luật\s+an\s+ninh\s+mạng|luật\s+ANM)\b", re.IGNORECASE),
    "CNTT": re.compile(r"\b(luật\s+công\s+nghệ\s+thông\s+tin|luật\s+CNTT)\b", re.IGNORECASE),
    "VT":   re.compile(r"\b(luật\s+viễn\s+thông|luật\s+VT)\b", re.IGNORECASE),
}


def _detected_laws(text: str) -> set[str]:
    return {key for key, rx in _LAW_ALIAS_PATTERNS.items() if rx.search(text)}


def _law_name_changed(original: str, refined: str) -> bool:
    """True nếu refined nhắc tới luật khác hẳn so với original."""
    o = _detected_laws(original)
    r = _detected_laws(refined)
    if not o:
        # query gốc không nêu luật → refined không được tự gắn luật
        return bool(r)
    # query gốc có nêu luật → refined có luật nào khác trong original không
    return bool(r - o)


_LAW_ID_TO_KEY: dict[str, str] = {
    "LuatAnNinhMang2025": "ANM",
    "LuatCNTT2025":       "CNTT",
    "LuatCNTT2006":       "CNTT",
    "LuatVienThong2023":  "VT",
}


def _refined_locked_ok(refined: str, law_id: str) -> bool:
    """Locked mode: refined phải chứa luật được lock + KHÔNG có luật khác."""
    locked_key = _LAW_ID_TO_KEY.get(law_id)
    if not locked_key:
        return True  # law_id không thuộc set quản lý → không enforce
    detected = _detected_laws(refined)
    return locked_key in detected and not (detected - {locked_key})


_JSON_RX = re.compile(r"\{[\s\S]*\}")


def _extract_json(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).rstrip("`").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = _JSON_RX.search(content)
        if not m:
            raise
        return json.loads(m.group(0))
