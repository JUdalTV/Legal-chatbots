"""
test.py — Debug tool: xem riêng 2 nguồn retrieval của Hybrid RAG.
  1. VECTOR CHUNKS: các chunk search được từ Qdrant (sau rerank)
  2. GRAPH CONTEXT: đồ thị truy xuất từ Neo4j (subgraph quanh article)

Dùng lại HybridRAGService nhưng KHÔNG gọi LLM sinh answer,
chỉ in raw retrieval results.

Chạy:
  python -m backend.services.test --law-id LuatAnNinhMang2025
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

from backend.graph_rag.graph_retriever import GraphRetriever
from backend.graph_rag.neo4j_loader import Neo4jKG
from backend.vector_rag.intent import extract_article_number
from backend.vector_rag.pipeline import VectorRAGPipeline


DEFAULT_QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
DEFAULT_QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DEFAULT_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    return [v for v in values if v and v not in seen and not seen.add(v)]


class HybridRetriever:
    """Chỉ retrieval, không gọi LLM."""

    def __init__(self, *, qdrant_host, qdrant_port, neo4j_uri, neo4j_user, neo4j_password, device, min_rerank_score):
        self.vector = VectorRAGPipeline(
            qdrant_host=qdrant_host, qdrant_port=qdrant_port,
            device=device, min_rerank_score=min_rerank_score,
        )
        self.kg = Neo4jKG(neo4j_uri, neo4j_user, neo4j_password)
        self.graph = GraphRetriever(self.kg)

    def close(self):
        self.kg.close()

    def retrieve(self, query: str, *, law_id=None, top_k=None, min_rerank_score=None):
        with ThreadPoolExecutor(max_workers=2) as pool:
            vec_f = pool.submit(self.vector.search, query, law_id=law_id, top_k=top_k, min_rerank_score=min_rerank_score)
            graph_f = pool.submit(self._graph_seed_search, query, law_id=law_id)
            vector_out = vec_f.result()
            graph_seed_ids = graph_f.result()

        vector_results = vector_out.get("results", [])
        vector_article_ids = [
            r.get("neo4j_id") or r.get("article")
            for r in vector_results if r.get("neo4j_id") or r.get("article")
        ]
        all_article_ids = _unique([*graph_seed_ids, *vector_article_ids])
        graph_context = self.graph.retrieve_context(all_article_ids)

        return {
            "intent": vector_out.get("intent", ""),
            "top_k": vector_out.get("top_k", 0),
            "vector_results": vector_results,
            "graph_seed_ids": graph_seed_ids,
            "all_article_ids": all_article_ids,
            "graph_context": graph_context,
        }

    def _graph_seed_search(self, query: str, *, law_id=None) -> list[str]:
        exact = self._exact(query, law_id=law_id)
        fulltext = self._fulltext(query, law_id=law_id)
        entity = self._entity(query, law_id=law_id)
        return _unique([*exact, *fulltext, *entity])

    def _exact(self, query, *, law_id):
        if not law_id:
            return []
        no = extract_article_number(query)
        if not no:
            return []
        aid = f"{law_id}_dieu_{no}"
        with self.kg.driver.session() as s:
            row = s.run("MATCH (a:ARTICLE {id: $id}) RETURN a.id AS id", id=aid).single()
        return [row["id"]] if row else []

    def _fulltext(self, query, *, law_id, limit=8):
        try:
            with self.kg.driver.session() as s:
                rows = list(s.run("""
                    CALL db.index.fulltext.queryNodes('article_fts', $q) YIELD node, score
                    OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(node)
                    WHERE $law_id IS NULL OR l.id = $law_id
                    RETURN node.id AS id, score ORDER BY score DESC LIMIT $limit
                """, q=query, law_id=law_id, limit=limit))
        except Exception:
            return []
        return [r["id"] for r in rows if r.get("id")]

    def _entity(self, query, *, law_id, limit=8):
        try:
            with self.kg.driver.session() as s:
                rows = list(s.run("""
                    CALL db.index.fulltext.queryNodes('entity_fts', $q) YIELD node, score
                    MATCH (a)-[:MENTIONS]->(node)
                    OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(a)
                    WHERE a:ARTICLE AND ($law_id IS NULL OR l.id = $law_id)
                    RETURN DISTINCT a.id AS id, max(score) AS score ORDER BY score DESC LIMIT $limit
                """, q=query, law_id=law_id, limit=limit))
        except Exception:
            return []
        return [r["id"] for r in rows if r.get("id")]


# ── Pretty print ─────────────────────────────────────────────────────
def _print_vector(data: dict):
    results = data["vector_results"]
    print(f"\n{'='*70}")
    print(f"  [1] VECTOR CHUNKS  (intent={data['intent']}, top_k={data['top_k']}, found={len(results)})")
    print(f"{'='*70}")
    if not results:
        print("  (không có chunk nào)")
        return
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {}) or {}
        label = meta.get("article_label") or r.get("article", "")
        clause = meta.get("clause_label") or ""
        tag = f" — {clause}" if clause else ""
        print(f"\n  [{i}] score={r['score']:.4f}  dense={r.get('dense_score', 0):.4f}  type={r['chunk_type']}")
        print(f"      {r.get('law_id', '')} | {label}{tag}")
        print(f"      article_id={r.get('article', '')}")
        refs = r.get("refs", [])
        if refs:
            print(f"      refs={refs}")
        content = r.get("content", "")
        print(f"      ---")
        for line in content.split("\n"):
            print(f"      {line}")


def _print_graph(data: dict):
    print(f"\n{'='*70}")
    print(f"  [2] GRAPH CONTEXT  (seed_ids={len(data['graph_seed_ids'])}, total_articles={len(data['all_article_ids'])})")
    print(f"{'='*70}")
    print(f"\n  Graph seed IDs (từ fulltext/exact/entity search):")
    for aid in data["graph_seed_ids"]:
        print(f"    • {aid}")
    print(f"\n  All article IDs (seed + vector):")
    for aid in data["all_article_ids"]:
        src = "seed" if aid in data["graph_seed_ids"] else "vector"
        print(f"    • {aid}  [{src}]")
    ctx = data["graph_context"]
    if not ctx:
        print("\n  (không có graph context)")
        return
    print(f"\n  Graph context (từ Neo4j subgraph):")
    print(f"  {'-'*60}")
    for line in ctx.split("\n"):
        print(f"  {line}")


# ── Main REPL ────────────────────────────────────────────────────────
def main() -> int:
    p = argparse.ArgumentParser(description="Debug: xem riêng Vector chunks + Graph context")
    p.add_argument("--qdrant-host", default=DEFAULT_QDRANT_HOST)
    p.add_argument("--qdrant-port", type=int, default=DEFAULT_QDRANT_PORT)
    p.add_argument("--neo4j-uri", default=DEFAULT_NEO4J_URI)
    p.add_argument("--neo4j-user", default=DEFAULT_NEO4J_USER)
    p.add_argument("--neo4j-password", default=DEFAULT_NEO4J_PASSWORD)
    p.add_argument("--device", default="gpu")
    p.add_argument("--law-id", default=None)
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--min-rerank-score", type=float, default=-999.0,
                    help="Mặc định -999 để không filter chunk nào (debug)")
    args = p.parse_args()

    retriever = HybridRetriever(
        qdrant_host=args.qdrant_host, qdrant_port=args.qdrant_port,
        neo4j_uri=args.neo4j_uri, neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password, device=args.device,
        min_rerank_score=args.min_rerank_score,
    )

    print("\n=== Hybrid Retrieval Debug ===")
    if args.law_id:
        print(f"  Filter: law_id={args.law_id}")
    print("  Gõ /exit để thoát\n")

    try:
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

            try:
                data = retriever.retrieve(query, law_id=args.law_id, top_k=args.top_k)
                _print_vector(data)
                _print_graph(data)
                print()
            except Exception as ex:
                print(f"  [error] {ex}\n")
    finally:
        retriever.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
