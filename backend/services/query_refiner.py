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


_SYSTEM = """Bạn là chuyên gia tinh chỉnh câu hỏi pháp lý.
Nhiệm vụ:
1. Xác định MỤC TIÊU thực sự của người hỏi (1-2 câu, dùng cho hướng dẫn LLM trả lời).
2. Viết lại câu hỏi rõ ràng, đầy đủ keyword cho retrieval (giữ thuật ngữ pháp lý gốc, bổ sung context bị thiếu).

Quy tắc:
- KHÔNG bịa luật/điều khoản chưa được nhắc.
- Giữ tên luật, số Điều/Khoản nếu có.
- Câu refined phải ngắn gọn (<= 50 từ), chứa nhiều keyword pháp lý hữu ích.
- Trả về JSON thuần, KHÔNG markdown:
  {"objective": "...", "refined": "..."}"""


def refine_query(
    query: str,
    *,
    intent: Optional[str] = None,
    llm: Optional[LLMClient] = None,
    max_tokens: int = 256,
) -> dict:
    """Trả {original, intent, objective, refined}. Fail-soft: lỗi LLM → original."""
    llm = llm or LLMClient()
    user = f"Intent: {intent or 'unknown'}\nCâu hỏi gốc: {query}"
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user},
    ]
    try:
        raw = llm.chat(messages, temperature=0.0, max_tokens=max_tokens)
        data = _extract_json(raw)
        refined   = (data.get("refined")   or "").strip() or query
        objective = (data.get("objective") or "").strip()
    except Exception as ex:
        print(f"[query_refiner] fail-soft → dùng query gốc: {ex}")
        refined, objective = query, ""

    return {
        "original":  query,
        "intent":    intent,
        "objective": objective,
        "refined":   refined,
    }


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
