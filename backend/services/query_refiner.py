"""
query_refiner.py — LLM-driven query refinement + decomposition (intent-aware).

Một LLM call duy nhất trả về 3 trường:
- `objective`:  mục tiêu thực sự của người hỏi (1-2 câu, làm tín hiệu cho LLM trả lời).
- `refined`:    câu hỏi viết lại, giàu keyword pháp lý, dùng cho single-query retrieval.
- `subqueries`: 2-4 câu con khi câu gốc PHỨC TẠP (nhiều chủ thể / khía cạnh).
                Câu đơn giản → [].

Hybrid RAG service quyết định search strategy dựa trên `subqueries`:
- subqueries non-empty (≥2) → multi-query vector search, dedupe theo chunk_id.
- subqueries rỗng           → search bằng `refined` đơn.

Mục tiêu: câu phức tạp với nhiều chủ thể/khía cạnh thường không match nguyên văn
chunk văn bản luật. Tách thành các câu đơn (1 chủ thể + 1 khía cạnh / câu) làm
vector embedding gần với cách văn bản luật thực sự được viết, tăng recall.
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


_SYSTEM_BASE = """Bạn là chuyên gia chuẩn hoá + phân rã câu hỏi pháp lý cho hệ thống RAG (vector + graph retrieval).

Trả về MỘT JSON thuần với đúng 3 trường:
{
  "objective":  "1-2 câu nêu mục tiêu thực sự của người hỏi (làm tín hiệu cho LLM trả lời)",
  "refined":    "câu hỏi viết lại, <=50 từ, giàu keyword pháp lý cho retrieval",
  "subqueries": ["sub 1", "sub 2", ...]
}

QUY TẮC `subqueries` (RẤT QUAN TRỌNG — ảnh hưởng trực tiếp tới chất lượng retrieval):
- subqueries = [] khi câu hỏi ĐƠN GIẢN: 1 chủ thể + 1 khía cạnh, hoặc lookup ngắn ("điều 15",
  "định nghĩa X", "thời hạn báo cáo sự cố", "ai cấp phép Y").
- subqueries có 2-4 phần tử khi câu PHỨC TẠP:
   • ≥2 CHỦ THỂ (vd: "doanh nghiệp viễn thông + nhà cung cấp dịch vụ điện toán đám mây + cá nhân"),
   • HOẶC ≥2 KHÍA CẠNH (nghĩa vụ + xử phạt + thủ tục báo cáo),
   • HOẶC câu so sánh/phân biệt nhiều đối tượng/khái niệm,
   • HOẶC câu có nhiều mệnh đề "và" / "nếu ... thì" / "khi nào" / "trong trường hợp".

Cách viết MỖI sub-query:
- 1 câu tiếng Việt NGẮN, RÕ, search-friendly. Mỗi sub chỉ có 1 chủ thể + 1 khía cạnh.
- GIỮ NGUYÊN VĂN tên chủ thể, dịch vụ, thuật ngữ pháp lý (để vector embedding match đoạn văn
  bản luật gốc — văn bản luật KHÔNG paraphrase, sub-query cũng KHÔNG được paraphrase).
- KHÔNG bịa số Điều/Khoản chưa được nhắc trong câu gốc.
- KHÔNG trùng lặp ngữ nghĩa giữa các sub.

QUY TẮC `refined` (LUÔN có, kể cả khi đã có subqueries):
- Ngắn gọn (<=50 từ), giàu keyword pháp lý, giữ thuật ngữ gốc.
- Mở rộng viết tắt: CNTT → Công nghệ thông tin, ANM → An ninh mạng, VT → Viễn thông.
- Giữ số Điều/Khoản nếu câu gốc có. KHÔNG bịa thêm.

Chỉ trả về JSON, KHÔNG markdown, KHÔNG giải thích thêm."""


_LAW_RULE_FREE = """
QUY TẮC TUYỆT ĐỐI VỀ TÊN LUẬT (free mode — user chưa chọn luật cụ thể):
- Nếu câu gốc nêu RÕ tên luật (vd: "Luật CNTT", "Luật An ninh mạng", "Luật Viễn thông") → BẮT
  BUỘC giữ NGUYÊN tên luật đó trong CẢ `refined` và MỖI sub-query. CẤM thay sang luật khác.
- Nếu câu gốc KHÔNG nêu tên luật → KHÔNG được tự gắn tên luật cụ thể vào `refined` hoặc bất
  kỳ sub-query nào."""


def _law_rule_locked(law_display: str) -> str:
    return f"""
QUY TẮC TUYỆT ĐỐI VỀ TÊN LUẬT (locked mode — user ĐÃ chọn luật cụ thể):
- LUẬT ĐANG TRA CỨU: "{law_display}".
- BẮT BUỘC `refined` bắt đầu bằng "Theo {law_display}, ..." HOẶC chèn cụm "trong {law_display}".
- MỖI sub-query cũng phải gắn cụm "{law_display}" (vd: "theo {law_display}" hoặc "trong
  {law_display}") để retrieval luôn lọc đúng luật.
- TUYỆT ĐỐI CẤM nhắc tới bất kỳ luật KHÁC trong `refined` hoặc bất kỳ sub-query nào (kể cả
  khi câu gốc có nhắc — vd: "so sánh Luật A và Luật B" mà luật đang tra cứu là "{law_display}"
  thì chỉ giữ phần liên quan đến "{law_display}").
- Giữ số Điều/Khoản từ câu gốc."""


def _build_system(law_id: Optional[str]) -> str:
    display = _LAW_DISPLAY.get(law_id or "")
    if display:
        return _SYSTEM_BASE + _law_rule_locked(display)
    return _SYSTEM_BASE + _LAW_RULE_FREE


def refine_and_decompose_query(
    query: str,
    *,
    intent: Optional[str] = None,
    law_id: Optional[str] = None,
    llm: Optional[LLMClient] = None,
    max_subqueries: int = 4,
    max_tokens: int = 512,
) -> dict:
    """
    Một LLM call → trả về {original, intent, objective, refined, subqueries}.

    - `subqueries` rỗng khi câu đơn giản; non-empty (đã sanitize, dedupe) khi câu phức tạp.
    - Fail-soft: lỗi LLM hoặc JSON parse → refined = original, subqueries = [].
    """
    llm = llm or LLMClient()
    locked_display = _LAW_DISPLAY.get(law_id or "") if law_id else None
    user_parts = [f"Câu hỏi gốc: {query}"]
    if intent:
        user_parts.append(f"Intent: {intent}")
    if locked_display:
        user_parts.append(f"Đang lọc theo: {locked_display}")
    messages = [
        {"role": "system", "content": _build_system(law_id)},
        {"role": "user",   "content": "\n".join(user_parts)},
    ]

    refined = query
    objective = ""
    subqueries: list[str] = []

    try:
        raw = llm.chat(
            messages, temperature=0.0, max_tokens=max_tokens,
            enable_thinking=False,
        )
        data = _extract_json(raw)

        refined = (data.get("refined") or "").strip() or query
        objective = (data.get("objective") or "").strip()
        raw_subs = data.get("subqueries") or []
        if isinstance(raw_subs, list):
            subqueries = [
                s.strip() for s in raw_subs
                if isinstance(s, str) and s.strip()
            ]

        # ── Safeguard 1: locked mode → refined phải đúng luật, KHÔNG mention luật khác ──
        if locked_display and not _refined_locked_ok(refined, law_id):
            print(f"[query_refiner] locked mode vi phạm refined (law_id={law_id}) → ép prefix")
            refined = f"Theo {locked_display}, {query}"
        # ── Safeguard 2: free mode → refined không được tự đổi/thêm tên luật ────────────
        elif not locked_display and _law_name_changed(query, refined):
            print(f"[query_refiner] free mode đổi tên luật refined → revert query gốc")
            refined = query

        # ── Safeguard 3: clean + dedupe subqueries; coi < 2 sub là không cần tách ──────
        if subqueries:
            subqueries = _sanitize_subqueries(
                subqueries,
                original=query, law_id=law_id,
                locked_display=locked_display,
            )[:max_subqueries]
            if len(subqueries) < 2:
                subqueries = []
    except Exception as ex:
        print(f"[query_refiner] fail-soft → dùng query gốc: {ex}")

    return {
        "original":   query,
        "intent":     intent,
        "objective":  objective,
        "refined":    refined,
        "subqueries": subqueries,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

_LAW_ALIAS_PATTERNS: dict[str, re.Pattern] = {
    "ANM":  re.compile(r"\b(luật\s+an\s+ninh\s+mạng|luật\s+ANM)\b", re.IGNORECASE),
    "CNTT": re.compile(r"\b(luật\s+công\s+nghệ\s+thông\s+tin|luật\s+CNTT)\b", re.IGNORECASE),
    "VT":   re.compile(r"\b(luật\s+viễn\s+thông|luật\s+VT)\b", re.IGNORECASE),
}

_LAW_ID_TO_KEY: dict[str, str] = {
    "LuatAnNinhMang2025": "ANM",
    "LuatCNTT2025":       "CNTT",
    "LuatCNTT2006":       "CNTT",
    "LuatVienThong2023":  "VT",
}


def _detected_laws(text: str) -> set[str]:
    return {key for key, rx in _LAW_ALIAS_PATTERNS.items() if rx.search(text)}


def _law_name_changed(original: str, refined: str) -> bool:
    """True nếu refined nhắc tới luật khác hẳn so với original."""
    o = _detected_laws(original)
    r = _detected_laws(refined)
    if not o:
        return bool(r)
    return bool(r - o)


def _refined_locked_ok(refined: str, law_id: str) -> bool:
    """Locked mode: refined phải chứa luật được lock + KHÔNG có luật khác."""
    locked_key = _LAW_ID_TO_KEY.get(law_id)
    if not locked_key:
        return True
    detected = _detected_laws(refined)
    return locked_key in detected and not (detected - {locked_key})


def _sanitize_subqueries(
    subs: list[str],
    *,
    original: str,
    law_id: Optional[str],
    locked_display: Optional[str],
) -> list[str]:
    """
    - Trim + collapse whitespace.
    - Dedupe (case-insensitive).
    - Locked mode: ép sub nhắc đúng locked law; rewrite nếu nhắc luật khác.
    - Free mode: bỏ sub đổi/thêm tên luật so với original.
    """
    out: list[str] = []
    seen: set[str] = set()
    locked_key = _LAW_ID_TO_KEY.get(law_id or "") if law_id else None
    original_laws = _detected_laws(original)

    for s in subs:
        norm = re.sub(r"\s+", " ", s).strip()
        if not norm:
            continue
        key = norm.lower()
        if key in seen:
            continue

        detected = _detected_laws(norm)
        if locked_display:
            other = detected - ({locked_key} if locked_key else set())
            if other:
                # Sub nhắc tới luật khác → ép prefix locked (giữ nội dung làm context).
                print(f"[query_refiner] sub vi phạm locked → ép prefix: {norm[:60]}")
                norm = f"Theo {locked_display}, {norm}"
                key = norm.lower()
                if key in seen:
                    continue
            elif locked_key and locked_key not in detected:
                # Sub không nhắc luật nào → thêm prefix locked để retrieval đúng luật.
                norm = f"Theo {locked_display}, {norm}"
                key = norm.lower()
                if key in seen:
                    continue
        else:
            if detected and detected - original_laws:
                print(f"[query_refiner] sub tự đổi/thêm tên luật → bỏ: {norm[:60]}")
                continue

        seen.add(key)
        out.append(norm)
    return out


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
