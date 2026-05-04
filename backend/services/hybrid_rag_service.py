"""
hybrid_rag_service.py
Service-level Hybrid RAG: Vector RAG + Graph RAG run in parallel, then one LLM
synthesizes an answer from both text chunks and graph context.
"""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

from backend.graph_rag.graph_retriever import GraphRetriever
from backend.graph_rag.neo4j_loader import Neo4jKG
from backend.graph_rag.ontology import ALL_NODE_TYPES, RELATION_CATALOG
from backend.vector_rag.intent import extract_article_number
from backend.vector_rag.pipeline import VectorRAGPipeline
from backend.services.llm_client import LLMClient


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
        min_rerank_score: float = 0.0,
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
        max_tokens: int = 4096,
    ) -> HybridRAGResult:
        with ThreadPoolExecutor(max_workers=2) as pool:
            vector_future = pool.submit(
                self._run_vector,
                query,
                law_id=law_id,
                top_k=top_k,
                min_rerank_score=min_rerank_score,
            )
            graph_future = pool.submit(self._run_graph_seed_search, query, law_id=law_id)

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

        messages = build_hybrid_prompt(
            query=query,
            vector_context=vector_context,
            graph_context=graph_context,
            cypher_guide=cypher_guide,
        )
        answer = self.llm.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return HybridRAGResult(
            answer=answer,
            vector_context=vector_context,
            graph_context=graph_context,
            vector_results=vector_results,
            graph_article_ids=graph_article_ids,
            cypher_guide=cypher_guide,
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
) -> list[dict]:
    system = """Bạn là trợ lý pháp lý chuyên về luật công nghệ thông tin và an ninh mạng Việt Nam.
Nhiệm vụ: tổng hợp câu trả lời từ hai nguồn đã truy xuất:
1. VECTOR_CHUNKS: trích đoạn văn bản luật, ưu tiên làm căn cứ chính.
2. GRAPH_CONTEXT: ngữ cảnh knowledge graph gồm điều luật, khoản, thực thể, quan hệ, tham chiếu.

Quy tắc:
Nếu một điều luật được đề cập trong GRAPH_CONTEXT 
nhưng nội dung không xuất hiện trong VECTOR_CHUNKS
→ KHÔNG trích dẫn điều đó.
→ Thay bằng: "Cần tra cứu thêm [Điều X] — chưa có 
  trong văn bản được cung cấp.
  
- Chỉ nêu căn cứ pháp lý cụ thể nếu căn cứ đó xuất hiện trong VECTOR_CHUNKS hoặc GRAPH_CONTEXT.
- Khi hai nguồn bổ sung nhau, hợp nhất thành câu trả lời mạch lạc, không lặp nguồn.
- Khi hai nguồn mâu thuẫn, ưu tiên nguyên văn trong VECTOR_CHUNKS và nêu rõ graph chỉ là ngữ cảnh hỗ trợ.
- Với câu hỏi về xử phạt/vi phạm, trình bày: hành vi; căn cứ; chế tài/mức phạt; biện pháp khắc phục nếu có.
- Không tự tạo Cypher mới để thay thế dữ liệu đã truy xuất. CYPHER_GUIDE chỉ giúp hiểu schema và cách graph context được hình thành."""
    user = f"""<CYPHER_GUIDE>
{cypher_guide}
</CYPHER_GUIDE>

<VECTOR_CHUNKS>
{vector_context or "[Không có chunk phù hợp]"}
</VECTOR_CHUNKS>

<GRAPH_CONTEXT>
{graph_context or "[Không có graph context phù hợp]"}
</GRAPH_CONTEXT>

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
    p.add_argument("query", nargs="*")
    return p


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
    )
    try:
        # Single query mode
        initial = " ".join(args.query).strip()
        if initial:
            result = service.answer(initial, law_id=args.law_id, top_k=args.top_k)
            print(result.answer)
            if args.show_context:
                _print_context(result)
            return 0

        # REPL mode
        print("\n=== Hybrid RAG Chat ===")
        if args.law_id:
            print(f"  Filter: law_id={args.law_id}")
        print("  Gõ /exit để thoát, /ctx để toggle hiện context")
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

            try:
                result = service.answer(query, law_id=args.law_id, top_k=args.top_k)
                print(f"\n{result.answer}\n")
                if show_ctx:
                    _print_context(result)
            except Exception as ex:
                print(f"  [error] {ex}\n")
        return 0
    finally:
        service.close()


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

# python -m backend.services.hybrid_rag_service --law-id LuatAnNinhMang2025
