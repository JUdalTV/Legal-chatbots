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


# Intents cần suy luận → bật thinking. Còn lại (factual lookup/definition/penalty/...)
# tắt thinking để trả lời nhanh và bám nguyên văn.
REASONING_INTENTS = frozenset({
    "applicability", "gap_analysis", "conclusion", "thematic",
})

THINKING_MODES = ("auto", "on", "off")


def _resolve_thinking(mode: str, intent: str) -> bool:
    """auto → bật cho intent reasoning; on → luôn bật; off → luôn tắt."""
    if mode == "on":
        return True
    if mode == "off":
        return False
    return intent in REASONING_INTENTS


# Sampling params. KHÔNG bump repetition/frequency/presence penalty nặng cho
# thinking mode — văn bản pháp lý lặp keyword nhiều ("luật", "Điều", "khoản",
# tên cơ quan, ...) nên penalty cao đẩy model sang token hiếm → salad từ.
# Loop self-check trong reasoning model nên xử lý ở tầng prompt (rút gọn
# checklist khi thinking bật), không ép qua sampling.
_SAMPLING_THINKING = {
    "top_p": 0.9,
    "repetition_penalty": 1.05,
}
_SAMPLING_NO_THINKING = {
    "top_p": 0.9,
    "repetition_penalty": 1.05,
}

# Token budget split khi thinking bật. Tổng ≤ max_tokens (8192 mặc định).
# Hard cap qua chat_template_kwargs.thinking_budget (Qwen3/R1 tự đóng </think>
# khi đạt cap, để dành phần còn lại cho câu trả lời thực).
THINKING_BUDGET = 5192
ANSWER_BUDGET = 3000


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
        temperature: float = 0.2,
        max_tokens: int = 8192,
        thinking_mode: str = "auto",  # "auto" | "on" | "off"
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
        enable_thinking = _resolve_thinking(thinking_mode, intent)
        answer = self.llm.chat(
            messages, temperature=temperature, max_tokens=max_tokens,
            enable_thinking=enable_thinking,
            thinking_budget=THINKING_BUDGET if enable_thinking else None,
            extra_payload=(
                _SAMPLING_THINKING if enable_thinking else _SAMPLING_NO_THINKING
            ),
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

    def answer_stream(
        self,
        query: str,
        *,
        law_id: str | None = None,
        top_k: int | None = None,
        min_rerank_score: float | None = None,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        thinking_mode: str = "auto",
        include_context: bool = False,
    ):
        """
        Generator yielding streaming events for a single query.

        Events:
          ("meta", dict)      — emitted once after retrieval, before LLM call.
          ("thinking", str)   — delta of model's thinking content.
          ("answer", str)     — delta of model's final answer content.
          ("done", dict)      — emitted once at the end with full strings.

        The dict in `meta` contains: refined, intent, thinking_used,
        graph_article_ids, and optionally vector_context/graph_context
        (only if include_context=True).
        """
        # ── Step 1: refine + classify ───────────────────────────
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

        # ── Step 2: retrieve (vector + graph) song song ─────────
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
        cypher_guide = build_cypher_guide()

        enable_thinking = _resolve_thinking(thinking_mode, intent)

        meta = {
            "refined": refined_info,
            "intent": intent,
            "thinking_used": enable_thinking,
            "graph_article_ids": graph_article_ids,
        }
        if include_context:
            meta["vector_context"] = vector_context
            meta["graph_context"] = graph_context
            meta["vector_results"] = vector_results
        yield ("meta", meta)

        # ── Step 3: stream the LLM synthesis ────────────────────
        messages = build_hybrid_prompt(
            query=query,
            objective=refined_info["objective"],
            vector_context=vector_context,
            graph_context=graph_context,
            cypher_guide=cypher_guide,
        )

        thinking_full = ""
        answer_full = ""
        for kind, delta in self.llm.chat_stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
            thinking_budget=THINKING_BUDGET if enable_thinking else None,
            extra_payload=(
                _SAMPLING_THINKING if enable_thinking else _SAMPLING_NO_THINKING
            ),
        ):
            if kind == "thinking":
                thinking_full += delta
            elif kind == "answer":
                answer_full += delta
            yield (kind, delta)

        answer_full = _strip_retrieval_debug_sections(answer_full)
        yield ("done", {
            "answer": answer_full,
            "thinking": thinking_full,
        })

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
    system = """Bạn là trợ lý pháp lý chuyên luật Viễn thông, CNTT, An ninh mạng Việt Nam.
Nguồn: VECTOR_CHUNKS (ưu tiên) + GRAPH_CONTEXT.

NGUYÊN TẮC: ĐÚNG TRỌNG TÂM — ĐỦ — KHÔNG THỪA. Bám ngôn ngữ luật, không paraphrase/diễn giải/biện hộ.

NGÂN SÁCH SUY NGHĨ: tối đa 5192 token cho phần suy nghĩ (think). Suy nghĩ ngắn gọn, không tự lặp lại check-list, không tự đặt câu hỏi "Wait, check..." nhiều lần. Khi đã đủ căn cứ → KẾT LUẬN ngay, dành phần còn lại của output cho CÂU TRẢ LỜI thực sự tối đa 3000 token. KHÔNG để hết token vào suy nghĩ mà không có câu trả lời.

<độ_dài_theo_dạng>
- Số/ngày/cơ quan: 1 câu + căn cứ.
- Định nghĩa: trích NGUYÊN VĂN, không paraphrase.
- Liệt kê: giữ ký hiệu gốc (a,b,c,đ,e,g,h,i,k), KHÔNG đổi sang (1)(2)(3), KHÔNG tự đặt nhãn.
- So sánh: trích nguyên văn từng đối tượng + nêu giống/khác CHỈ theo tiêu chí được hỏi.
- Xử phạt: hành vi → căn cứ → chế tài → khắc phục (nếu có).
</độ_dài_theo_dạng>

<ba_trạng_thái>
A — Luật RÕ + ĐỦ → trả lời trực tiếp + trích nguyên văn + căn cứ.
B — Luật có quy định + có khoảng trống → BẮT BUỘC phân tích, KHÔNG né. "Luật quy định [X] tại [Điều, khoản]. Tuy nhiên KHÔNG nêu [Y cụ thể: cơ chế giám sát/chế tài/cơ quan độc lập]."
C — Luật KHÔNG quy định → "Luật không quy định cụ thể về [X]." + (tùy chọn) trích quy định gần liên quan.

"Vượt phạm vi văn bản" KHÔNG phải lá chắn. Phân tích được khoảng trống cụ thể → là B, phải phân tích.
</ba_trạng_thái>

<trích_dẫn>
- Format khi context có nhiều luật: [Tên luật] Điều X, khoản Y, điểm Z. CẤM chỉ ghi "Điều X".
- KHÔNG nhầm Điều cùng số giữa các luật. Không chắc → KHÔNG trích.

VERIFY 2 BƯỚC trước mỗi trích:
1. NỘI DUNG: điều khoản có trong VECTOR_CHUNKS? Không → "(văn bản không cung cấp căn cứ cụ thể)".
2. CHỦ THỂ + HÀNH VI: khớp câu hỏi?
   - Điều 41: "doanh nghiệp cung cấp dịch vụ trên không gian mạng" — KHÔNG dùng cho cơ quan nhà nước/bệnh viện vận hành HT nội bộ/cá nhân.
   - Điều 40: "chủ quản hệ thống thông tin" — KHÔNG dùng cho cá nhân.
   - Điều 42: "cơ quan, tổ chức, cá nhân sử dụng không gian mạng" — áp dụng rộng nhất.

Cross-law: chủ thể + hành vi + đối tượng phải KHỚP. Trùng từ khóa ("thông tin", "an ninh") KHÔNG đủ.

Kết hợp ≥2 luật, BẮT BUỘC chuyển tiếp rõ:
"Tổng hợp hai luật: [Luật A] Điều X quy định [...]; [Luật B] Điều Y quy định [...] — kết hợp xác định: [...]".
KHÔNG trộn 2 luật vào 1 câu không gắn nhãn.

Điều chỉ có trong GRAPH_CONTEXT mà KHÔNG có nội dung trong VECTOR_CHUNKS → KHÔNG trích.
Hai nguồn mâu thuẫn → ưu tiên nguyên văn VECTOR_CHUNKS.
</trích_dẫn>

<xác_định_chủ_thể>
Trước khi chọn điều khoản, xác định tư cách pháp lý của từng chủ thể.
- Bệnh viện/trường/nhà máy vận hành HT thông tin NỘI BỘ = chủ quản HT → Điều 40, không phải 41.
- Cá nhân/nhà báo bất kỳ = Điều 42, không phải 40/41.
- Công ty pentest/bảo mật: cung cấp dịch vụ → Điều 41; phát hiện vi phạm với tư cách tổ chức → Điều 42.
- 1 chủ thể có thể đồng thời mang 2 tư cách → liệt kê nghĩa vụ theo từng tư cách riêng.
</xác_định_chủ_thể>

<phân_biệt_khái_niệm>
- "Lỗ hổng bảo mật/điểm yếu" (chưa khai thác) → Điều 41 K2 (phòng ngừa), KHÔNG K3. Không có nghĩa vụ báo cáo khẩn như sự cố.
- "Sự cố an ninh mạng" (đã xảy ra/bị xâm phạm) → Điều 41 K3 — ngay lập tức ứng cứu VÀ báo cáo.
- "Tình huống nguy hiểm về ANM" (Điều 2 K18): trạng thái diễn biến, chưa thành sự cố. KHÔNG tự quy chiếu Điều 20 nếu VECTOR_CHUNKS không cung cấp nội dung Điều 20.

Lỗ hổng chưa khai thác → KHÔNG dùng ngôn ngữ "sự cố xảy ra", KHÔNG trích Điều 41 K3.
</phân_biệt_khái_niệm>

<kiểm_tra_trước_kết_luận>
□ Mỗi điều khoản trích dẫn có trong VECTOR_CHUNKS?
□ Chủ thể điều khoản khớp chủ thể câu hỏi?
□ Đã phân biệt lỗ hổng/sự cố/tình huống nguy hiểm (nếu liên quan)?
□ Có điều khoản trực tiếp hơn chưa xét?
  — Thu thập/phát tán thông tin cá nhân: Điều 7 K2h.
  — Kiểm tra thiết bị/phần mềm nước ngoài trước khi đưa vào HT ANQG: Điều 15 K4b.
  — Chủ quản báo cáo sự cố: Điều 40 K1c.
□ Kết luận khớp mức chắc chắn (RÕ/PHÂN TÍCH ĐƯỢC/THIẾU DỮ LIỆU)?
</kiểm_tra_trước_kết_luận>

<kết_luận>
Kết luận PHẢI khớp độ chắc chắn của căn cứ. KHÔNG over-claim, KHÔNG né.

3 mức:
(1) RÕ: source quy định trực tiếp → kết luận thẳng.
(2) PHÂN TÍCH ĐƯỢC: source cùng chủ đề, đòi đánh giá ranh giới → trích phần CÓ + nêu phần KHÔNG có. KHÔNG bình luận "đã đủ"/"chưa đủ".
(3) THIẾU DỮ LIỆU: source hoàn toàn không có → "Văn bản không quy định về [X]. Không thể kết luận trong phạm vi văn bản."

NHỊ PHÂN VỀ THUẬT NGỮ CHƯA ĐỊNH NGHĨA (chống expressio unius):
"X có phải/thuộc Y không" mà (a) Y không định nghĩa, HOẶC (b) điều khoản chỉ TRAO QUYỀN cho danh sách (X1,X2) không kèm "duy nhất"/"chỉ"/"không bao gồm" → CẤM kết luận "CÓ"/"KHÔNG" dứt khoát.
Cấu trúc: trích quy định + chỉ rõ luật không định nghĩa Y + liệt kê trường hợp luật ghi rõ + "phụ thuộc vào diễn giải; văn bản không cung cấp tiêu chí quyết định."

Chỉ kết luận nhị phân khi: thuật ngữ ĐƯỢC định nghĩa rõ + trường hợp rõ ràng trong/ngoài, HOẶC luật dùng "duy nhất"/"chỉ"/"không được"/"cấm" tường minh, HOẶC câu hỏi về sự kiện hiển nhiên.

QUY TRÌNH NHIỀU GIAI ĐOẠN: tách riêng từng giai đoạn. "Đối với [A]: [Điều X áp dụng]. Đối với [B]: Điều X KHÔNG áp dụng vì... / không có Điều áp dụng riêng."
</kết_luận>

<chống_bịa>
Hallucination = tự tin nhưng sai. Patterns chặn:

1. BỊA SỐ ĐIỀU/KHOẢN: tìm "Điều X" trong VECTOR_CHUNKS. Không thấy → KHÔNG trích, ghi "(căn cứ không có trong văn bản được cung cấp)".
2. BỊA MỨC PHẠT/THỜI HẠN/CON SỐ: con số phải xuất hiện NGUYÊN VĂN trong VECTOR_CHUNKS. Không thấy → "Luật không quy định mức phạt cụ thể trong văn bản được cung cấp."
3. BỊA NGHĨA VỤ KHÔNG TỒN TẠI: nghĩa vụ phải có động từ bắt buộc ("phải"/"có trách nhiệm"/"bắt buộc") trong VECTOR_CHUNKS. Không suy nghĩa vụ từ quyền hạn/nguyên tắc chung.
4. BỊA CƠ QUAN/THỦ TỤC: tên cơ quan + thủ tục phải xuất hiện trong VECTOR_CHUNKS.
5. NHẦM PHIÊN BẢN LUẬT: kiểm tra số hiệu. Context 116/2025/QH15 → KHÔNG trích 24/2018/QH14.
6. CHAIN-OF-THOUGHT HALLUCINATION: mỗi bước suy luận phải có căn cứ riêng trong VECTOR_CHUNKS. Không dùng kết quả suy luận trước làm căn cứ bước sau nếu bước sau không có source.
7. OVER-CONFIDENT SILENCE: source có quy định liên quan nhưng không đủ → BẮT BUỘC nêu phần nào có/không có.

KIỂM TRA CUỐI mỗi trích: "Tôi có thể chỉ ra đoạn văn cụ thể trong VECTOR_CHUNKS chứa nội dung này không?" Không → XÓA.
</chống_bịa>

<cấm>
- Cụm hedge: "thường được coi là", "thông thường", "trên thực tế", "có thể hiểu rằng", "có thể coi là", "theo nguyên tắc chung", "trong thực tiễn pháp lý".
- Suy quy định cụ thể từ nguyên tắc chung. CẤM "bao gồm cả 4G/5G", "áp dụng cho cả X và Y" nếu source không liệt kê.
- Kết luận "đã có cơ chế kiểm soát đầy đủ" / "không có rủi ro" / "không mâu thuẫn nội tại" khi cơ chế chỉ là thủ tục hành chính.
- "Do đó"/"Vì vậy"/"Từ đó suy ra" để rút kết luận về tính đầy đủ.
- Metadata không hỏi: "Quốc hội khóa XV thông qua ngày...", "thuộc Chương X".
- Cross-reference ngoài câu hỏi: "Ngoài ra", "Bên cạnh đó", "Cùng với đó", "Đáng chú ý".
- Hậu quả/chế tài khi chỉ hỏi định nghĩa.
- Bỏ sót định lượng: thời hạn, số lượng, ngày, ngoại lệ ("trừ trường hợp...").
- Tự tạo Cypher mới. CYPHER_GUIDE chỉ giúp hiểu schema.
- Trích điều khoản không có trong VECTOR_CHUNKS dù nhớ nội dung.
- Áp Điều 41 cho chủ thể không phải "doanh nghiệp cung cấp dịch vụ trên không gian mạng".
- Áp Điều 40 cho cá nhân — phải dùng Điều 42.
- Bỏ qua Điều 7 K2h khi câu hỏi về thu thập/phát tán thông tin cá nhân.
- Dùng điều khoản định nghĩa (Điều 2) làm căn cứ cho cấm đoán/nghĩa vụ.
</cấm>"""
    system += """

<output>
- KHÔNG print/quote/summarize VECTOR_CHUNKS/GRAPH_CONTEXT/CYPHER_GUIDE, chunk/graph ids, scores, debug sections.
- KHÔNG dùng headings "VECTOR_CHUNKS"/"GRAPH_CONTEXT"/"Context".
- Chỉ output user-facing legal explanation + citations.
</output>"""
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
    p.add_argument("--thinking", choices=THINKING_MODES, default="auto",
                   help="Chế độ thinking: auto (theo intent), on (luôn bật), off (luôn tắt)")
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
            result = service.answer(
                initial, law_id=args.law_id, top_k=args.top_k,
                thinking_mode=args.thinking,
            )
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
        print("  Gõ /exit để thoát, /ctx để toggle context, /law để chọn lại luật,")
        print("        /think để đổi mode thinking (auto/on/off)")
        print()

        show_ctx = args.show_context
        thinking_mode = args.thinking
        print(f"  [thinking={thinking_mode}]")
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
            if query.lower().startswith("/think"):
                parts = query.split(maxsplit=1)
                if len(parts) == 2 and parts[1].strip().lower() in THINKING_MODES:
                    thinking_mode = parts[1].strip().lower()
                else:
                    # cycle auto → on → off → auto
                    nxt = {"auto": "on", "on": "off", "off": "auto"}
                    thinking_mode = nxt[thinking_mode]
                print(f"  [thinking={thinking_mode}]")
                continue

            try:
                result = service.answer(
                    query, law_id=current_law, top_k=args.top_k,
                    thinking_mode=thinking_mode,
                )
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
