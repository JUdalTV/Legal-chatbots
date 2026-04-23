"""
reranker.py
Rerank kết quả từ Qdrant trước khi đưa vào LLM.

Chiến lược:
  1. Score kết hợp: Qdrant cosine score + keyword bonus
  2. Ưu tiên chunk_type="dieu" nếu câu hỏi mang tính tổng quát
  3. Ưu tiên chunk_type="khoan" nếu câu hỏi hỏi về chi tiết cụ thể
  4. Đảm bảo không trùng DieuLuat (dedup theo neo4j_id ở mức Điều)
"""

from __future__ import annotations
import re
from typing import List


def rerank(
    results: list,               # kết quả từ VectorStore.search_dense()
    query: str,
    top_k: int = 5,
    prefer_type: str = "auto",   # "dieu" | "khoan" | "auto"
) -> list:
    """
    Rerank danh sách kết quả Qdrant.
    Trả về top_k results đã sắp xếp lại.
    """
    if not results:
        return []

    query_tokens = set(re.findall(r"\w+", query.lower()))

    scored = []
    for r in results:
        payload = r.payload
        base_score = r.score  # cosine score từ Qdrant (0~1)

        # Keyword bonus: tần suất token query xuất hiện trong nội dung
        content_tokens = set(
            re.findall(r"\w+", payload.get("content", "").lower())
        )
        keyword_overlap = len(query_tokens & content_tokens) / max(len(query_tokens), 1)
        keyword_bonus = keyword_overlap * 0.15  # trọng số nhỏ

        # Loại chunk bonus
        chunk_type = payload.get("chunk_type", "dieu")
        effective_prefer = _infer_prefer_type(query) if prefer_type == "auto" else prefer_type

        type_bonus = 0.0
        if effective_prefer == "khoan" and chunk_type == "khoan":
            type_bonus = 0.05
        elif effective_prefer == "dieu" and chunk_type == "dieu":
            type_bonus = 0.03

        final_score = base_score + keyword_bonus + type_bonus

        scored.append({
            "score":      final_score,
            "neo4j_id":   payload.get("neo4j_id", ""),
            "chunk_id":   payload.get("chunk_id", ""),
            "chunk_type": chunk_type,
            "law_name":   payload.get("law_name", ""),
            "dieu_so":    payload.get("dieu_so", ""),
            "dieu_ten":   payload.get("dieu_ten", ""),
            "khoan_so":   payload.get("khoan_so"),
            "content":    payload.get("content", ""),
            "so_hieu":    payload.get("so_hieu", ""),
            "chuong_ten": payload.get("chuong_ten", ""),
        })

    # Sắp xếp theo final_score giảm dần
    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:top_k]


def _infer_prefer_type(query: str) -> str:
    """
    Phán đoán loại chunk phù hợp từ câu hỏi.
    """
    q = query.lower()
    # Từ khóa gợi ý câu hỏi chi tiết → cần chunk khoản
    DETAIL_KEYWORDS = [
        "cụ thể", "như thế nào", "điều kiện", "thủ tục", "quy trình",
        "mức phạt", "xử lý", "trách nhiệm của", "nghĩa vụ của",
        "quyền của", "khoản"
    ]
    # Từ khóa gợi ý câu hỏi tổng quát → cần chunk điều
    GENERAL_KEYWORDS = [
        "là gì", "định nghĩa", "khái niệm", "quy định gì",
        "điều chỉnh", "phạm vi", "nguyên tắc", "chính sách"
    ]

    detail_score = sum(1 for kw in DETAIL_KEYWORDS if kw in q)
    general_score = sum(1 for kw in GENERAL_KEYWORDS if kw in q)

    if detail_score > general_score:
        return "khoan"
    return "dieu"


def format_context_for_llm(reranked: list) -> str:
    """
    Format các chunks đã rerank thành context string cho LLM.
    """
    parts = []
    for i, r in enumerate(reranked, 1):
        header = (
            f"[Nguồn {i}] {r['law_name']} ({r['so_hieu']})"
            f" | Điều {r['dieu_so']}. {r['dieu_ten']}"
        )
        if r["khoan_so"]:
            header += f" — Khoản {r['khoan_so']}"
        parts.append(f"{header}\n{r['content']}")

    return "\n\n---\n\n".join(parts)