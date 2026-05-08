"""
hybrid_rag_service.py
Service-level Hybrid RAG: Vector RAG + Graph RAG run in parallel, then one LLM
synthesizes an answer from both text chunks and graph context.
"""

from __future__ import annotations

import argparse
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

from backend.graph_rag.graph_retriever import GraphRetriever
from backend.graph_rag.neo4j_loader import Neo4jKG
from backend.graph_rag.ontology import ALL_NODE_TYPES, RELATION_CATALOG
from backend.vector_rag.intent import classify_intent, extract_article_number
from backend.vector_rag.pipeline import VectorRAGPipeline
from backend.services.llm_client import LLMClient
from backend.services.query_refiner import refine_query

# Note: citation.py + faithfulness.py vẫn còn trong codebase nhưng KHÔNG còn
# nằm trong hybrid pipeline. Giữ lại 2 file để dùng programmatic ở chỗ khác
# (vd: benchmark scoring).


DEFAULT_QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
DEFAULT_QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DEFAULT_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")


@dataclass
class HybridRAGResult:
    answer: str
    vector_context: str
    graph_context: str
    vector_results: list[dict]
    graph_article_ids: list[str]
    cypher_guide: str
    refined: dict          # {original, intent, objective, refined}


class HybridRAGService:
    """
    Compose two retrieval pipelines:
    - Vector RAG: Qdrant dense search + reranker -> chunks
    - Graph RAG: Neo4j fulltext/exact lookup -> graph neighborhood

    Both retrieval branches are started in parallel. The LLM receives both
    `VECTOR_CHUNKS` and `GRAPH_CONTEXT`, plus a Cypher/schema guide.
    """

    def __init__(
        self,
        *,
        qdrant_host: str = DEFAULT_QDRANT_HOST,
        qdrant_port: int = DEFAULT_QDRANT_PORT,
        neo4j_uri: str = DEFAULT_NEO4J_URI,
        neo4j_user: str = DEFAULT_NEO4J_USER,
        neo4j_password: str = DEFAULT_NEO4J_PASSWORD,
        device: str = "gpu",
        llm: LLMClient | None = None,
        min_rerank_score: float = 0.25,
        enable_refine:       bool = True,
    ):
        self.vector = VectorRAGPipeline(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            device=device,
            min_rerank_score=min_rerank_score,
        )
        self.kg = Neo4jKG(neo4j_uri, neo4j_user, neo4j_password)
        self.graph = GraphRetriever(self.kg)
        self.llm = llm or LLMClient()
        self.enable_refine = enable_refine

    def close(self) -> None:
        self.kg.close()

    def answer(
        self,
        query: str,
        *,
        law_id: str | None = None,
        top_k: int | None = None,
        min_rerank_score: float | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> HybridRAGResult:
        # ── Step 1: tinh chỉnh query (intent-aware, law-locked nếu có) ──
        intent = classify_intent(query)
        if self.enable_refine:
            refined_info = refine_query(
                query, intent=intent, law_id=law_id, llm=self.llm,
            )
        else:
            refined_info = {
                "original": query, "intent": intent,
                "objective": "", "refined": query,
            }
        retrieval_query = refined_info["refined"]

        # ── Step 2: retrieve (vector + graph seed) song song ──────
        with ThreadPoolExecutor(max_workers=2) as pool:
            vector_future = pool.submit(
                self._run_vector,
                retrieval_query,
                law_id=law_id,
                top_k=top_k,
                min_rerank_score=min_rerank_score,
            )
            graph_future = pool.submit(
                self._run_graph_seed_search, retrieval_query, law_id=law_id,
            )
            vector_out = vector_future.result()
            graph_seed_ids = graph_future.result()

        vector_results = vector_out.get("results", [])
        vector_context = vector_out.get("context", "")
        vector_article_ids = [
            r.get("neo4j_id") or r.get("article")
            for r in vector_results
            if r.get("neo4j_id") or r.get("article")
        ]
        graph_article_ids = _unique([*graph_seed_ids, *vector_article_ids])
        graph_context = self.graph.retrieve_context(graph_article_ids)
        cypher_guide  = build_cypher_guide()

        # ── Step 3: synthesize answer ─────────────────────────────
        messages = build_hybrid_prompt(
            query=query,                        # giữ câu gốc cho user-facing
            objective=refined_info["objective"],
            vector_context=vector_context,
            graph_context=graph_context,
            cypher_guide=cypher_guide,
        )
        answer = self.llm.chat(
            messages, temperature=temperature, max_tokens=max_tokens,
            extra_payload={"top_p": 0.9, "repetition_penalty": 1.05},
        )
        answer = _strip_retrieval_debug_sections(answer)

        return HybridRAGResult(
            answer=answer,
            vector_context=vector_context,
            graph_context=graph_context,
            vector_results=vector_results,
            graph_article_ids=graph_article_ids,
            cypher_guide=cypher_guide,
            refined=refined_info,
        )

    def _run_vector(
        self,
        query: str,
        *,
        law_id: str | None,
        top_k: int | None,
        min_rerank_score: float | None,
    ) -> dict:
        return self.vector.search(
            query,
            law_id=law_id,
            top_k=top_k,
            min_rerank_score=min_rerank_score,
        )

    def _run_graph_seed_search(self, query: str, *, law_id: str | None) -> list[str]:
        exact = self._exact_article_ids(query, law_id=law_id)
        fulltext = self._fulltext_article_ids(query, law_id=law_id)
        entity_hits = self._entity_article_ids(query, law_id=law_id)
        return _unique([*exact, *fulltext, *entity_hits])

    def _exact_article_ids(self, query: str, *, law_id: str | None) -> list[str]:
        if not law_id:
            return []
        article_no = extract_article_number(query)
        if not article_no:
            return []
        article_id = f"{law_id}_dieu_{article_no}"
        with self.kg.driver.session() as s:
            row = s.run(
                "MATCH (a:ARTICLE {id: $id}) RETURN a.id AS id",
                id=article_id,
            ).single()
        return [row["id"]] if row else []

    def _fulltext_article_ids(
        self,
        query: str,
        *,
        law_id: str | None,
        limit: int = 8,
    ) -> list[str]:
        cypher = """
        CALL db.index.fulltext.queryNodes('article_fts', $q)
        YIELD node, score
        OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(node)
        WHERE $law_id IS NULL OR l.id = $law_id
        RETURN node.id AS id, score
        ORDER BY score DESC
        LIMIT $limit
        """
        try:
            with self.kg.driver.session() as s:
                rows = list(s.run(cypher, q=query, law_id=law_id, limit=limit))
        except Exception:
            return []
        return [r["id"] for r in rows if r.get("id")]

    def _entity_article_ids(
        self,
        query: str,
        *,
        law_id: str | None,
        limit: int = 8,
    ) -> list[str]:
        cypher = """
        CALL db.index.fulltext.queryNodes('entity_fts', $q)
        YIELD node, score
        MATCH (a)-[:MENTIONS]->(node)
        OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(a)
        WHERE a:ARTICLE AND ($law_id IS NULL OR l.id = $law_id)
        RETURN DISTINCT a.id AS id, max(score) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        try:
            with self.kg.driver.session() as s:
                rows = list(s.run(cypher, q=query, law_id=law_id, limit=limit))
        except Exception:
            return []
        return [r["id"] for r in rows if r.get("id")]


def build_hybrid_prompt(
    *,
    query: str,
    vector_context: str,
    graph_context: str,
    cypher_guide: str,
    objective: str = "",
) -> list[dict]:
    system = """Bạn là trợ lý pháp lý chuyên luật CNTT và an ninh mạng Việt Nam.
Nguồn: VECTOR_CHUNKS (ưu tiên) + GRAPH_CONTEXT.

NGUYÊN TẮC TỐI THƯỢNG: ĐÚNG TRỌNG TÂM — ĐỦ — KHÔNG THỪA. Bám sát ngôn ngữ luật, không paraphrase, không diễn giải, không biện hộ.

<độ_dài_theo_dạng>
- Hỏi 1 số/ngày/cơ quan: 1 câu chứa đáp án + căn cứ.
- Hỏi định nghĩa: trích NGUYÊN VĂN, không paraphrase ("Định nghĩa này bao gồm... khía cạnh" — CẤM).
- Hỏi liệt kê: giữ ký hiệu gốc của luật (a, b, c, đ, e, g, h, i, k...), KHÔNG đổi sang (1)(2)(3), KHÔNG tự đặt nhãn từng mục.
- Hỏi so sánh: trích định nghĩa nguyên văn từng đối tượng + nêu giống/khác CHỈ theo tiêu chí được hỏi.
- Hỏi xử phạt: hành vi → căn cứ → chế tài → biện pháp khắc phục (nếu có).
</độ_dài_theo_dạng>

<ba_trạng_thái>
Phân loại câu trả lời và xử lý khác nhau:

A — Luật quy định RÕ + ĐỦ → trả lời trực tiếp + trích nguyên văn + căn cứ.

B — Luật CÓ quy định nhưng CÓ khoảng trống → BẮT BUỘC phân tích, KHÔNG né. Cấu trúc: "Luật quy định [X] tại [Điều, khoản]. Tuy nhiên, văn bản KHÔNG nêu [Y cụ thể: cơ chế giám sát / chế tài / cơ quan độc lập]."

C — Luật HOÀN TOÀN KHÔNG quy định → "Luật không quy định cụ thể về [X]." + (tùy chọn) trích quy định gần liên quan.

LƯU Ý: "Vượt phạm vi văn bản" KHÔNG phải lá chắn cho câu khó. Nếu phân tích được khoảng trống cụ thể → là Trạng thái B, phải phân tích.
</ba_trạng_thái>

<trích_dẫn>
- Format BẮT BUỘC khi context có nhiều luật: [Tên luật] Điều X, khoản Y, điểm Z. KHÔNG được chỉ ghi "Điều X".
- KHÔNG nhầm Điều cùng số giữa các luật. Không chắc → KHÔNG trích.

- VERIFY 2 BƯỚC trước mỗi lần trích:
  Bước 1 — NỘI DUNG: Nội dung điều khoản này trong VECTOR_CHUNKS có đúng như mình nhớ không?
             Nếu điều khoản KHÔNG xuất hiện trong VECTOR_CHUNKS → CẤM trích, ghi "(văn bản không cung cấp căn cứ cụ thể)".
  Bước 2 — CHỦ THỂ + HÀNH VI: Chủ thể trong điều khoản có khớp với chủ thể câu hỏi không?
             Hành vi/đối tượng điều chỉnh có đúng với tình huống không?
             Ví dụ: Điều 41 áp dụng cho "doanh nghiệp cung cấp dịch vụ trên không gian mạng" — KHÔNG áp dụng cho
             cơ quan nhà nước, bệnh viện vận hành hệ thống nội bộ, hay cá nhân người dùng thông thường.
             Điều 40 áp dụng cho "chủ quản hệ thống thông tin" — KHÔNG áp dụng cho người dùng cá nhân.
             Điều 42 áp dụng cho "cơ quan, tổ chức, cá nhân sử dụng không gian mạng" — áp dụng rộng nhất.

- VERIFY substantive trước khi dùng cross-law: chủ thể + hành vi + đối tượng phải KHỚP câu hỏi.
  Trùng từ khóa ("thông tin", "an ninh") KHÔNG đủ.

- Khi kết hợp ≥2 luật, BẮT BUỘC mở đầu bằng câu chuyển tiếp rõ:
  "Tổng hợp hai luật: [Luật A] Điều X quy định [...]; [Luật B] Điều Y quy định [...] — kết hợp lại xác định: [...]".
  KHÔNG trộn 2 luật vào 1 câu không gắn nhãn.

- Điều chỉ có trong GRAPH_CONTEXT mà KHÔNG có nội dung trong VECTOR_CHUNKS → KHÔNG trích.
- Hai nguồn mâu thuẫn → ưu tiên nguyên văn VECTOR_CHUNKS.
</trích_dẫn>

<xác_định_chủ_thể>
Với mọi câu hỏi tình huống, BẮT BUỘC xác định tư cách pháp lý của từng chủ thể TRƯỚC khi chọn điều khoản áp dụng.

QUY TẮC:
- Bệnh viện/trường học/nhà máy vận hành hệ thống thông tin NỘI BỘ = Chủ quản hệ thống → Điều 40, không phải Điều 41.
- Người dùng cá nhân, nhà báo, cá nhân bất kỳ = Điều 42, không phải Điều 40 hay 41.
- Công ty pentest/bảo mật: xác định rõ họ đang hoạt động với tư cách nào trong tình huống cụ thể
  (cung cấp dịch vụ → Điều 41; phát hiện vi phạm với tư cách tổ chức → Điều 42).
- Một chủ thể CÓ THỂ có cả 2 tư cách đồng thời → liệt kê nghĩa vụ theo từng tư cách riêng.
</xác_định_chủ_thể>

<phân_biệt_khái_niệm>
Trước khi áp điều khoản về sự cố an ninh mạng, phân biệt rõ:

- "Lỗ hổng bảo mật / điểm yếu" (vulnerability): chưa bị khai thác.
  → Áp dụng: Điều 41 Khoản 2 (phòng ngừa chủ động), không phải Khoản 3 (ứng phó sự cố).
  → Không có nghĩa vụ báo cáo khẩn cấp ngay lập tức như khi sự cố xảy ra.

- "Sự cố an ninh mạng" (incident): đã xảy ra, hệ thống đã bị xâm phạm/gián đoạn.
  → Áp dụng: Điều 41 Khoản 3 — ngay lập tức triển khai ứng cứu VÀ báo cáo.

- "Tình huống nguy hiểm về an ninh mạng" (Điều 2 Khoản 18): trạng thái diễn biến, chưa thành sự cố.
  → Không được tự ý quy chiếu sang "Điều 20" nếu VECTOR_CHUNKS không cung cấp nội dung Điều 20 rõ ràng.

Nếu tình huống mô tả lỗ hổng chưa bị khai thác: KHÔNG dùng ngôn ngữ "sự cố xảy ra", KHÔNG trích Điều 41 K3
như thể sự cố đã xảy ra.
</phân_biệt_khái_niệm>

<kiểm_tra_trước_kết_luận>
Trước khi xuất kết quả, chạy checklist:

□ Mỗi điều khoản trích dẫn có xuất hiện trong VECTOR_CHUNKS không?
□ Chủ thể trong điều khoản có khớp với chủ thể trong câu hỏi không?
□ Đã phân biệt lỗ hổng / sự cố / tình huống nguy hiểm chưa (nếu liên quan)?
□ Có điều khoản nào trực tiếp hơn mà chưa xét không?
  — Nếu câu hỏi về thu thập/phát tán thông tin cá nhân: đã xét Điều 7 K2h chưa?
  — Nếu câu hỏi về kiểm tra thiết bị/phần mềm nước ngoài trước khi đưa vào hệ thống ANQG: đã xét Điều 15 K4b chưa?
  — Nếu câu hỏi về chủ quản báo cáo sự cố: đã xét Điều 40 K1c chưa?
□ Kết luận có khớp với mức độ chắc chắn của căn cứ không (RÕ / PHÂN TÍCH ĐƯỢC / THIẾU DỮ LIỆU)?
</kiểm_tra_trước_kết_luận>

<kết_luận>
Kết luận PHẢI khớp với độ chắc chắn của căn cứ. KHÔNG over-claim, KHÔNG né.

3 mức kết luận:
(1) RÕ: source quy định trực tiếp → kết luận thẳng.
(2) PHÂN TÍCH ĐƯỢC: source có quy định cùng chủ đề nhưng đòi đánh giá ranh giới → trích phần CÓ + nêu phần KHÔNG có. KHÔNG bình luận "đã đủ"/"chưa đủ".
(3) THIẾU DỮ LIỆU: source hoàn toàn không có → "Văn bản không quy định về [X]. Không thể kết luận trong phạm vi văn bản."

CÂU HỎI NHỊ PHÂN VỀ THUẬT NGỮ CHƯA ĐỊNH NGHĨA (chống expressio unius):
Khi hỏi "X có phải/có thuộc Y không" mà (a) Y không được định nghĩa, HOẶC (b) điều khoản chỉ TRAO QUYỀN cho danh sách (X1, X2) không kèm "duy nhất"/"chỉ"/"không bao gồm" → CẤM kết luận "CÓ"/"KHÔNG" dứt khoát.
Cấu trúc: trích quy định + chỉ rõ luật không định nghĩa Y + liệt kê trường hợp luật ghi rõ + KẾT LUẬN: "phụ thuộc vào diễn giải; văn bản không cung cấp tiêu chí quyết định."

Chỉ kết luận nhị phân khi: thuật ngữ ĐƯỢC định nghĩa rõ + trường hợp rõ ràng nằm trong/ngoài, HOẶC luật dùng "duy nhất"/"chỉ"/"không được"/"cấm" tường minh, HOẶC câu hỏi về sự kiện hiển nhiên ("hiệu lực ngày nào").

VÍ DỤ: Q "Sao chép để chuyển máy có phải 'lưu trữ dự phòng' không?" + Source "trao quyền sao chép cho dự phòng và thay thế phần mềm hỏng" (không định nghĩa "dự phòng").
SAI: "KHÔNG được coi là lưu trữ dự phòng" (= expressio unius).
ĐÚNG: "Luật trao quyền cho 2 trường hợp [...], không định nghĩa 'dự phòng' và không tuyên bố danh sách đóng. Việc chuyển máy có thuộc 'dự phòng' hay không phụ thuộc vào diễn giải; văn bản không có tiêu chí quyết định."

QUY TRÌNH NHIỀU GIAI ĐOẠN: Tách riêng từng giai đoạn, KHÔNG trộn vào 1 kết luận chung. "Đối với [A]: [Điều X áp dụng]. Đối với [B]: Điều X KHÔNG áp dụng vì... / không có Điều áp dụng riêng."
</kết_luận>

<chống_bịa>
HALLUCINATION XẢY RA KHI MODEL TỰ TIN NHƯNG SAI. Các pattern phổ biến cần chặn:

1. BỊA SỐ ĐIỀU/KHOẢN:
   - Triệu chứng: trích "Điều 15, Khoản 3" nhưng VECTOR_CHUNKS không có nội dung đó.
   - Kiểm tra: tìm chuỗi "Điều 15" trong VECTOR_CHUNKS. Không thấy → KHÔNG trích.
   - Nếu nhớ nội dung nhưng không thấy trong VECTOR_CHUNKS: ghi "(căn cứ không có trong văn bản được cung cấp)".

2. BỊA MỨC PHẠT / THỜI HẠN / CON SỐ:
   - Triệu chứng: "phạt từ 50-100 triệu", "trong vòng 30 ngày", "tối thiểu 3 năm".
   - Quy tắc: CON SỐ phải xuất hiện NGUYÊN VĂN trong VECTOR_CHUNKS. Không thấy → KHÔNG nêu.
   - Thay bằng: "Luật không quy định mức phạt cụ thể trong văn bản được cung cấp."

3. BỊA NGHĨA VỤ KHÔNG TỒN TẠI:
   - Triệu chứng: "doanh nghiệp phải báo cáo hàng quý", "phải có chứng chỉ ISO".
   - Quy tắc: nghĩa vụ phải có động từ bắt buộc ("phải", "có trách nhiệm", "bắt buộc") trong VECTOR_CHUNKS.
   - Không suy ra nghĩa vụ từ quyền hạn hoặc nguyên tắc chung.

4. BỊA CƠ QUAN / THỦ TỤC:
   - Triệu chứng: "nộp hồ sơ tại Bộ TT&TT", "Cục An toàn thông tin xét duyệt".
   - Quy tắc: tên cơ quan + thủ tục phải xuất hiện trong VECTOR_CHUNKS. Không thấy → KHÔNG nêu.

5. NHẦM PHIÊN BẢN LUẬT:
   - Triệu chứng: trích Luật ANM 2018 khi đang hỏi về Luật ANM 2025.
   - Quy tắc: kiểm tra số hiệu luật trong VECTOR_CHUNKS trước khi trích. Nếu context là 116/2025/QH15 → KHÔNG trích 24/2018/QH14.

6. CHAIN-OF-THOUGHT HALLUCINATION:
   - Triệu chứng: "Vì A → suy ra B → do đó C phải chịu trách nhiệm D" khi D không có trong source.
   - Quy tắc: mỗi bước suy luận phải có căn cứ riêng trong VECTOR_CHUNKS. Không được dùng kết quả suy luận trước làm căn cứ cho bước sau nếu bước sau không có source.

7. OVER-CONFIDENT SILENCE:
   - Triệu chứng: không nói gì về khoảng trống pháp lý khi câu hỏi đòi hỏi phân tích.
   - Quy tắc: nếu source có quy định liên quan nhưng không đủ → BẮT BUỘC nêu rõ phần nào có, phần nào không có.

KIỂM TRA CUỐI: Với mỗi điều khoản sắp trích, tự hỏi:
"Tôi có thể chỉ ra đoạn văn cụ thể trong VECTOR_CHUNKS chứa nội dung này không?"
Nếu KHÔNG → XÓA khỏi câu trả lời.
</chống_bịa>

- Cụm hedge ngụy trang: "thường được coi là", "thông thường", "trên thực tế", "có thể hiểu rằng", "có thể coi là", "theo nguyên tắc chung", "trong thực tiễn pháp lý".
- Suy ra quy định cụ thể từ nguyên tắc chung. CẤM "bao gồm cả 4G/5G", "áp dụng cho cả X và Y" nếu source không liệt kê.
- Kết luận "đã có cơ chế kiểm soát đầy đủ" / "không có rủi ro lạm dụng" / "không mâu thuẫn nội tại" khi cơ chế chỉ là thủ tục hành chính nội bộ.
- "Do đó", "Vì vậy", "Từ đó suy ra" để rút kết luận về tính đầy đủ.
- Metadata không hỏi: "Quốc hội khóa XV thông qua ngày...", "thuộc Chương X".
- Cross-reference ngoài câu hỏi: "Ngoài ra", "Bên cạnh đó", "Cùng với đó", "Đáng chú ý".
- Hậu quả/chế tài khi chỉ hỏi định nghĩa.
- Bỏ sót chi tiết định lượng: thời hạn ("trong thời hạn 12 tháng"), số lượng, ngày tháng, ngoại lệ ("trừ trường hợp...").
- Tự tạo Cypher mới. CYPHER_GUIDE chỉ giúp hiểu schema.
- Trích điều khoản không có trong VECTOR_CHUNKS dù nhớ nội dung — đây là hallucination. KHÔNG trích.
- Áp Điều 41 cho chủ thể không phải "doanh nghiệp cung cấp dịch vụ trên không gian mạng".
- Áp Điều 40 cho cá nhân người dùng thông thường — phải dùng Điều 42.
- Bỏ qua điều khoản về "thu thập, sử dụng, phát tán trái pháp luật thông tin, dữ liệu cá nhân" (Điều 7 K2h)
  khi câu hỏi liên quan đến thu thập/phát tán thông tin cá nhân — đây thường là căn cứ trực tiếp nhất.
- Dùng điều khoản định nghĩa (Điều 2) như căn cứ cho cấm đoán hoặc nghĩa vụ.
</cấm>"""
    system += """

Output rules:
- Do not print, quote, summarize, or expose raw VECTOR_CHUNKS, GRAPH_CONTEXT, CYPHER_GUIDE, chunk ids, graph ids, scores, or retrieval/debug sections.
- Do not include headings such as VECTOR_CHUNKS, GRAPH_CONTEXT, Graph context, Vector chunks, or Context in the final answer.
- Final answer must contain only the user-facing legal explanation and legal citations when relevant."""
    objective_block = (
        f"\n<MỤC_TIÊU_NGƯỜI_HỎI>\n{objective}\n</MỤC_TIÊU_NGƯỜI_HỎI>\n"
        if objective else ""
    )
    user = f"""<CYPHER_GUIDE>
{cypher_guide}
</CYPHER_GUIDE>

<VECTOR_CHUNKS>
{vector_context or "[Không có chunk phù hợp]"}
</VECTOR_CHUNKS>

<GRAPH_CONTEXT>
{graph_context or "[Không có graph context phù hợp]"}
</GRAPH_CONTEXT>
{objective_block}
<CÂU_HỎI>
{query}
</CÂU_HỎI>"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_cypher_guide() -> str:
    rel_groups = "\n".join(
        f"- {group}: {', '.join(types)}"
        for group, types in RELATION_CATALOG.items()
    )
    node_labels = ", ".join(sorted(ALL_NODE_TYPES))
    return f"""Neo4j schema guide for Legal Knowledge Graph.

Node labels:
{node_labels}

Core node properties:
- id: stable identifier, e.g. LuatAnNinhMang2025_dieu_10
- label: Vietnamese display label
- layer: structural | normative | governance | system | cyber | telecom | it | geo
- ARTICLE: so, content, amendment_type, hieu_luc
- LAW: so_hieu, nam, loai, hieu_luc
- CLAUSE: so, content
- Entity nodes: score, source, subclass

Relationship groups:
{rel_groups}

Core relationships:
- (LAW)-[:HAS_CHAPTER]->(CHAPTER)
- (CHAPTER)-[:HAS_ARTICLE]->(ARTICLE)
- (LAW)-[:HAS_ARTICLE]->(ARTICLE)
- (ARTICLE)-[:HAS_CLAUSE]->(CLAUSE)
- (ARTICLE|CLAUSE)-[:MENTIONS]->(entity)
- (ARTICLE)-[:REFERS_TO]->(ARTICLE)
- Semantic LLM edges can include article_id, sentence_idx, source, evidence, modality, condition, exception, scope, time.

Useful Cypher patterns:
1. Exact article:
MATCH (l:LAW {{id: $law_id}})-[:HAS_ARTICLE]->(a:ARTICLE {{id: $article_id}})
OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(k:CLAUSE)
RETURN l, a, collect(k) AS clauses

2. Fulltext article search:
CALL db.index.fulltext.queryNodes('article_fts', $query)
YIELD node, score
RETURN node.id AS article_id, node.label AS label, score
ORDER BY score DESC

3. Entity search then back to articles:
CALL db.index.fulltext.queryNodes('entity_fts', $query)
YIELD node, score
MATCH (a:ARTICLE)-[:MENTIONS]->(node)
RETURN DISTINCT a.id AS article_id, labels(node)[0] AS entity_type, node.label AS entity, score
ORDER BY score DESC

4. Clauses of an article:
MATCH (a:ARTICLE {{id: $article_id}})-[:HAS_CLAUSE]->(k:CLAUSE)
RETURN k.so AS clause_no, k.content AS content
ORDER BY toInteger(k.so)

5. Article references:
MATCH (a:ARTICLE {{id: $article_id}})-[r:REFERS_TO]->(b:ARTICLE)
RETURN b.id AS target_article, r.evidence AS evidence, r.cross_law AS cross_law

6. Entities mentioned in an article:
MATCH (a:ARTICLE {{id: $article_id}})-[:MENTIONS]->(e)
RETURN labels(e)[0] AS type, collect(DISTINCT e.label) AS labels

7. Semantic edges extracted for an article:
MATCH (from)-[r]->(to)
WHERE r.article_id = $article_id
RETURN from.label AS from, type(r) AS relation, to.label AS to,
       r.modality AS modality, r.condition AS condition,
       r.exception AS exception, r.scope AS scope,
       r.time AS time, r.evidence AS evidence

Interpretation rules:
- VECTOR_CHUNKS contain primary legal text.
- GRAPH_CONTEXT summarizes graph neighborhoods and may omit full text.
- MENTIONS means an entity appears in an article/clause, not necessarily a legal obligation.
- REFERS_TO means the article references another article; inspect target text before treating it as substantive rule.
- Semantic edges with source='llm' are extracted relations and should be treated as supporting signals, not stronger than the text."""


def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for v in values:
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


_DEBUG_SECTION_RE = re.compile(
    r"(?ims)"
    r"^\s*(?:#{1,6}\s*)?"
    r"(?:={2,}\s*)?"
    r"(?:VECTOR_CHUNKS?|GRAPH_CONTEXT|CYPHER_GUIDE|GRAPH_ARTICLE_IDS|"
    r"Vector\s+chunks?|Graph\s+context|Cypher\s+guide)"
    r"\s*(?:={2,})?\s*:?\s*$"
    r".*?"
    r"(?=^\s*(?:#{1,6}\s*)?(?:={2,}\s*)?"
    r"(?:VECTOR_CHUNKS?|GRAPH_CONTEXT|CYPHER_GUIDE|GRAPH_ARTICLE_IDS|"
    r"Vector\s+chunks?|Graph\s+context|Cypher\s+guide)"
    r"\s*(?:={2,})?\s*:?\s*$|\Z)"
)

_DEBUG_TAG_RE = re.compile(
    r"(?is)<\s*(VECTOR_CHUNKS?|GRAPH_CONTEXT|CYPHER_GUIDE|GRAPH_ARTICLE_IDS)\s*>"
    r".*?"
    r"<\s*/\s*\1\s*>"
)


def _strip_retrieval_debug_sections(answer: str) -> str:
    """Remove leaked retrieval/debug blocks from the user-facing answer."""
    if not answer:
        return answer

    cleaned = _DEBUG_TAG_RE.sub("", answer)
    cleaned = _DEBUG_SECTION_RE.sub("", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hybrid RAG service CLI")
    p.add_argument("--qdrant-host", default=DEFAULT_QDRANT_HOST)
    p.add_argument("--qdrant-port", type=int, default=DEFAULT_QDRANT_PORT)
    p.add_argument("--neo4j-uri", default=DEFAULT_NEO4J_URI)
    p.add_argument("--neo4j-user", default=DEFAULT_NEO4J_USER)
    p.add_argument("--neo4j-password", default=DEFAULT_NEO4J_PASSWORD)
    p.add_argument("--device", default="gpu")
    p.add_argument("--law-id", default=None)
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--min-rerank-score", type=float, default=0.0)
    p.add_argument("--show-context", action="store_true")
    p.add_argument("--no-refine",       action="store_true",
                   help="Tắt LLM query refinement")
    p.add_argument("query", nargs="*")
    return p


def _pick_law(kg) -> str | None:
    """Hỏi user chọn luật từ danh sách đã ingest. Trả về law_id hoặc None (toàn bộ)."""
    with kg.driver.session() as s:
        rows = list(s.run(
            "MATCH (l:LAW) RETURN l.id AS id, l.label AS label ORDER BY l.label"
        ))
    laws = [(r["id"], r["label"]) for r in rows]
    if not laws:
        print("[warn] Không có luật nào trong Neo4j.")
        return None

    while True:
        print("\nChọn luật để tra cứu:")
        for i, (_, label) in enumerate(laws, 1):
            print(f"  {i}. {label}")
        print(f"  {len(laws)+1}. Tất cả luật (không filter)")
        print(f"  0. Thoát")
        try:
            choice = input("Lựa chọn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "__exit__"
        if choice == "0":
            return "__exit__"
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(laws):
                return laws[n-1][0]
            if n == len(laws)+1:
                return None
        print("  [!] Lựa chọn không hợp lệ.")


def main() -> int:
    args = _build_parser().parse_args()
    service = HybridRAGService(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        device=args.device,
        min_rerank_score=args.min_rerank_score,
        enable_refine=not args.no_refine,
    )
    try:
        # Single query mode
        initial = " ".join(args.query).strip()
        if initial:
            result = service.answer(initial, law_id=args.law_id, top_k=args.top_k)
            _print_answer_block(result)
            if args.show_context:
                _print_context(result)
            return 0

        # REPL mode
        print("\n=== Hybrid RAG Chat ===")
        current_law = args.law_id
        if current_law is None:
            current_law = _pick_law(service.kg)
            if current_law == "__exit__":
                return 0
        print(f"  Filter: law_id={current_law or '(tất cả)'}")
        print("  Gõ /exit để thoát, /ctx để toggle context, /law để chọn lại luật")
        print()

        show_ctx = args.show_context
        while True:
            try:
                query = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not query:
                continue
            if query.lower() in ("/exit", "/quit", "exit", "quit"):
                break
            if query.lower() == "/ctx":
                show_ctx = not show_ctx
                print(f"  [show_context={show_ctx}]")
                continue
            if query.lower() == "/law":
                picked = _pick_law(service.kg)
                if picked == "__exit__":
                    break
                current_law = picked
                print(f"  [law_id={current_law or '(tất cả)'}]")
                continue

            try:
                result = service.answer(query, law_id=current_law, top_k=args.top_k)
                _print_answer_block(result)
                if show_ctx:
                    _print_context(result)
            except Exception as ex:
                print(f"  [error] {ex}\n")
        return 0
    finally:
        service.close()


def _print_answer_block(result: HybridRAGResult) -> None:
    refined = result.refined or {}
    if refined.get("refined") and refined["refined"] != refined.get("original"):
        print(f"\n[refined] {refined['refined']}")
    if refined.get("objective"):
        print(f"[mục tiêu] {refined['objective']}")

    print(f"\n{result.answer}\n")


def _print_context(result: HybridRAGResult) -> None:
    print("\n=== VECTOR_CHUNKS ===")
    print(result.vector_context)
    print("\n=== GRAPH_CONTEXT ===")
    print(result.graph_context)
    print("\n=== GRAPH_ARTICLE_IDS ===")
    print(result.graph_article_ids)
    print()


if __name__ == "__main__":
    raise SystemExit(main())

# python -m backend.services.hybrid_rag_service
