"""
prompt_builder.py
Xây dựng prompt cho LLM trong Vector RAG pipeline.
"""

from __future__ import annotations


SYSTEM_PROMPT = """Bạn là trợ lý pháp lý chuyên về luật công nghệ thông tin và an ninh mạng Việt Nam.
Hãy trả lời câu hỏi DỰA TRÊN các điều khoản pháp luật được cung cấp trong context.
Quy tắc:
- Chỉ trích dẫn thông tin từ context được cung cấp.
- Ghi rõ tên luật, số điều khi trích dẫn.
- Nếu không tìm thấy thông tin trong context, nói rõ "Không tìm thấy quy định liên quan trong các văn bản được cung cấp."
- Không bịa đặt hoặc suy diễn ngoài phạm vi văn bản pháp luật."""


def build_rag_prompt(query: str, context: str) -> list[dict]:
    """
    Trả về messages list cho chat completion API.
    """
    user_message = (
        f"Các điều khoản pháp luật liên quan:\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"Câu hỏi: {query}"
    )
    return [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": user_message},
    ]


def build_graph_rag_prompt(query: str, vector_context: str, graph_context: str) -> list[dict]:
    """
    Hybrid prompt: kết hợp context từ Vector RAG và Graph RAG.
    """
    combined = (
        "=== NGỮ CẢNH TỪ TÌM KIẾM VĂN BẢN ===\n\n"
        f"{vector_context}\n\n"
        "=== NGỮ CẢNH TỪ KNOWLEDGE GRAPH ===\n\n"
        f"{graph_context}"
    )
    return build_rag_prompt(query, combined)