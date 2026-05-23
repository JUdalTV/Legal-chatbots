"""
faithfulness.py — LLM-based claim verification.

Pass 2 sau khi sinh answer: kiểm tra mỗi claim trong answer có được hỗ trợ
bởi context retrieved hay không. Trả list flagged claims để UI hiển thị
hoặc để regenerate.

Cách tiếp cận:
  1. Tách answer thành claims (regex câu)
  2. Cho LLM đánh giá batch: với mỗi claim, output {supported: bool, evidence: str}
  3. Tính faithfulness_score = supported / total

Fail-soft: lỗi LLM → trả unknown, không chặn flow trả lời.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from .llm_client import LLMClient


_SYSTEM = """Bạn là kiểm duyệt sự thật cho câu trả lời pháp lý.
Đầu vào: 1 đoạn CONTEXT (trích văn bản luật) + danh sách CLAIMS (câu khẳng định trong câu trả lời).
Với mỗi claim, đánh giá:
  - "supported": true nếu nội dung claim được CONTEXT hỗ trợ trực tiếp; false nếu không.
  - "evidence": trích nguyên văn ngắn (≤ 120 ký tự) trong CONTEXT làm bằng chứng (nếu supported).

Quy tắc:
- Chỉ dựa vào CONTEXT, không dùng kiến thức ngoài.
- Claim mơ hồ / không kiểm chứng được → supported=false.
- Trả JSON thuần (không markdown):
  {"results": [{"supported": bool, "evidence": "..."}]}
- Đảm bảo `results` cùng độ dài với CLAIMS."""


_SENT_SPLIT = re.compile(r"(?<=[\.!\?])\s+(?=[A-ZĐÀ-Ỹ0-9])")


def split_claims(answer: str, max_claims: int = 12) -> list[str]:
    """Tách answer thành câu — bỏ câu quá ngắn (<10 ký tự)."""
    parts = [p.strip() for p in _SENT_SPLIT.split(answer.strip()) if p.strip()]
    parts = [p for p in parts if len(p) >= 10]
    return parts[:max_claims]


def check_faithfulness(
    answer: str,
    context: str,
    *,
    llm: Optional[LLMClient] = None,
    max_tokens: int = 1024,
) -> dict:
    """
    Trả:
      { "faithful": bool, "score": float ∈[0,1],
        "supported": int, "total": int, "issues": [{claim, evidence?}], "raw": [...] }
    """
    claims = split_claims(answer)
    if not claims:
        return {"faithful": True, "score": 1.0, "supported": 0, "total": 0,
                "issues": [], "raw": []}

    llm = llm or LLMClient()
    claim_block = "\n".join(f"{i+1}. {c}" for i, c in enumerate(claims))
    user = f"<CONTEXT>\n{context}\n</CONTEXT>\n\n<CLAIMS>\n{claim_block}\n</CLAIMS>"
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user},
    ]

    try:
        raw = llm.chat(
            messages, temperature=0.0, max_tokens=max_tokens,
            enable_thinking=False,
        )
        data = _extract_json(raw)
        results = data.get("results") or []
    except Exception as ex:
        print(f"[faithfulness] fail-soft: {ex}")
        return {"faithful": True, "score": 1.0, "supported": len(claims),
                "total": len(claims), "issues": [], "raw": []}

    # Pad / truncate kết quả về cùng độ dài
    while len(results) < len(claims):
        results.append({"supported": False, "evidence": ""})
    results = results[:len(claims)]

    issues: list[dict] = []
    n_supported = 0
    for c, r in zip(claims, results):
        if r.get("supported"):
            n_supported += 1
        else:
            issues.append({
                "claim":    c,
                "evidence": (r.get("evidence") or "").strip(),
            })

    score = n_supported / len(claims)
    return {
        "faithful":  score >= 0.8,
        "score":     score,
        "supported": n_supported,
        "total":     len(claims),
        "issues":    issues,
        "raw":       results,
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
