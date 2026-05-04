"""
prompt_builder.py
Xây dựng prompt cho LLM trong Vector RAG pipeline.
"""

from __future__ import annotations


SYSTEM_PROMPT = f"""Bạn là trợ lý pháp lý chuyên về luật công nghệ thông tin và an ninh mạng Việt Nam.
Nhiệm vụ: Trả lời câu hỏi pháp lý CHỈ dựa trên các đoạn văn bản luật được cung cấp trong phần <văn_bản_pháp_luật>.

<yêu_cầu_trích_dẫn>
- Mỗi luận điểm ghi rõ: tên luật | số điều | khoản/điểm.
- Trích dẫn ĐẦY ĐỦ các khoản, mức phạt, điều kiện, ngoại lệ liên quan có trong context.
- Nếu nhiều luật cùng điều chỉnh một vấn đề: hợp nhất, phân rõ theo từng văn bản.
</yêu_cầu_trích_dẫn>

<cấu_trúc_trả_lời>
Với câu hỏi về xử phạt hoặc vi phạm, trình bày theo thứ tự:
1. Hành vi vi phạm
2. Căn cứ pháp lý (tên luật | điều | khoản)
3. Chế tài / mức phạt
4. Biện pháp khắc phục hậu quả (nếu có)
</cấu_trúc_trả_lời>

<giới_hạn>
- Không tìm thấy quy định trong context: trả lời chính xác "Không tìm thấy quy định liên quan trong các văn bản được cung cấp."
- Tuyệt đối không suy diễn hoặc bổ sung thông tin ngoài context.
- Không áp dụng nghị định, thông tư hay văn bản khác ngoài các đoạn văn bản được cung cấp.
- Không bịa số điều, khoản, mức phạt hoặc căn cứ pháp lý cụ thể nếu chúng không xuất hiện trong context.
</giới_hạn>"""


def build_rag_prompt(query: str, context: str) -> list[dict]:
    """
    Trả về messages list cho chat completion API.
    """
    context = context.strip()
    if not context:
        context = "[Không có đoạn văn bản luật nào được truy xuất]"

    user_message = (
        "<văn_bản_pháp_luật>\n"
        f"{context}\n"
        "</văn_bản_pháp_luật>\n\n"
        f"<câu_hỏi>\n{query}\n</câu_hỏi>"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
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
    ).strip()
    return build_rag_prompt(query, combined)
