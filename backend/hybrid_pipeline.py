"""
backend/hybrid_pipeline.py
Pipeline Hybrid RAG: kết hợp Vector RAG + Graph RAG.

Luồng đầy đủ:
  Câu hỏi
    ↓
  [Vector RAG] embed query → search Qdrant → rerank
    ↓
  neo4j_ids từ top-k Qdrant results
    ↓
  [Graph RAG] traverse Neo4j → subgraph context
    ↓
  [Context Merging] kết hợp vector_context + graph_context
    ↓
  [LLM] sinh câu trả lời
"""

from __future__ import annotations
import sys
from pathlib import Path

# sys.path setup
sys.path.insert(0, str(Path(__file__).parent / "vector_rag"))
sys.path.insert(0, str(Path(__file__).parent / "graph_rag"))
sys.path.insert(0, str(Path(__file__).parent / "graph_rag" / "services"))

from embedder import Embedder
from vector_store import VectorStore
from reranker import rerank, format_context_for_llm
from prompt_builder import build_graph_rag_prompt
from neo4j_loader import Neo4jLegalKG
from graph_retriever import GraphRetriever
from llm_client import LLMClient

import os


class HybridRAGPipeline:
    """
    Pipeline chính kết hợp Vector RAG và Graph RAG.
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        neo4j_uri: str   = "bolt://localhost:7687",
        neo4j_user: str  = "neo4j",
        neo4j_pass: str  = "password",
    ):
        self.embedder    = Embedder(device="cpu")
        self.vector_store = VectorStore(host=qdrant_host, port=qdrant_port)
        self.kg           = Neo4jLegalKG(neo4j_uri, neo4j_user, neo4j_pass)
        self.graph_ret    = GraphRetriever(self.kg)
        self.llm          = LLMClient()

    def query(
        self,
        question: str,
        top_k_vector: int = 10,
        top_k_rerank: int = 5,
        law_filter: str | None = None,
    ) -> dict:
        """
        Xử lý câu hỏi và trả về câu trả lời + metadata.

        Returns:
          {
            "answer":         str,
            "vector_sources": list[dict],   top-k chunks từ Qdrant
            "graph_context":  str,          context từ KG
            "neo4j_ids_used": list[str],
          }
        """
        # ── Bước 1: Embed câu hỏi ───────────────────────────────
        query_vector = self.embedder.encode([question], show_progress=False)[0]

        # ── Bước 2: Vector search Qdrant ────────────────────────
        raw_results = self.vector_store.search_dense(
            query_vector=query_vector,
            top_k=top_k_vector,
            law_name=law_filter,
        )

        # ── Bước 3: Rerank ───────────────────────────────────────
        reranked = rerank(raw_results, query=question, top_k=top_k_rerank)

        # ── Bước 4: Vector context ───────────────────────────────
        vector_context = format_context_for_llm(reranked)

        # ── Bước 5: Graph context (từ neo4j_id trong payload) ────
        neo4j_ids = list(dict.fromkeys(
            r["neo4j_id"] for r in reranked if r.get("neo4j_id")
        ))
        graph_context = self.graph_ret.retrieve_context(neo4j_ids)

        # ── Bước 6: Build prompt + LLM ───────────────────────────
        messages = build_graph_rag_prompt(
            query=question,
            vector_context=vector_context,
            graph_context=graph_context,
        )
        answer = self.llm.chat(messages)

        return {
            "answer":         answer,
            "vector_sources": reranked,
            "graph_context":  graph_context,
            "neo4j_ids_used": neo4j_ids,
        }

    def close(self):
        self.kg.close()


# ── CLI test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    pipeline = HybridRAGPipeline(
        neo4j_uri=os.getenv("NEO4J_URI",      "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER",    "neo4j"),
        neo4j_pass=os.getenv("NEO4J_PASSWORD","12345678"),
    )

    test_questions = [
        "An ninh mạng là gì?",
        "Doanh nghiệp cung cấp dịch vụ trên không gian mạng có trách nhiệm gì?",
        "Các hành vi bị nghiêm cấm trong Luật An ninh mạng 2025 là gì?",
        "Điều kiện để được cấp giấy phép kinh doanh dịch vụ viễn thông là gì?",
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Câu hỏi: {q}")
        result = pipeline.query(q)
        print(f"\nTrả lời:\n{result['answer']}")
        print(f"\nNguồn: {[s['neo4j_id'] for s in result['vector_sources'][:3]]}")

    pipeline.close()