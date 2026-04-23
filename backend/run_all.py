"""
backend/run_all.py
Script master để chạy toàn bộ pipeline Tuần 2:
  1. Vector RAG ingestion (Qdrant)
  2. Graph RAG ingestion  (Neo4j)

Cách dùng:
  python run_all.py              # chạy cả 2
  python run_all.py --vector     # chỉ Vector RAG
  python run_all.py --graph      # chỉ Graph RAG
  python run_all.py --test       # chạy test query
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load biến môi trường từ .env
BACKEND = Path(__file__).parent
load_dotenv(BACKEND / ".env")

# Setup paths
sys.path.insert(0, str(BACKEND / "vector_rag"))
sys.path.insert(0, str(BACKEND / "graph_rag"))
sys.path.insert(0, str(BACKEND / "services"))


def run_vector_ingestion():
    print("\n" + "█"*55)
    print("  BƯỚC 1: VECTOR RAG INGESTION → Qdrant")
    print("█"*55)
    from vector_rag.ingestion import run_ingestion
    run_ingestion(recreate_collection=True)


def run_graph_ingestion():
    print("\n" + "█"*55)
    print("  BƯỚC 2: GRAPH RAG INGESTION → Neo4j")
    print("█"*55)
    from graph_rag.ingestion import run_ingestion
    run_ingestion()


def run_test():
    print("\n" + "█"*55)
    print("  BƯỚC 3: TEST HYBRID QUERY")
    print("█"*55)
    from hybrid_pipeline import HybridRAGPipeline

    pipeline = HybridRAGPipeline(
        neo4j_uri=os.getenv("NEO4J_URI",      "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER",     "neo4j"),
        neo4j_pass=os.getenv("NEO4J_PASSWORD", "12345678"),
    )

    test_questions = [
        "An ninh mạng là gì?",
        "Luật An ninh mạng 2025 sửa đổi những gì?",
        "Các hành vi bị nghiêm cấm trong Luật An ninh mạng 2025 là gì?",
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Câu hỏi: {q}")
        result = pipeline.query(q)
        print(f"\nTrả lời:\n{result['answer']}")
        print(f"\nNguồn: {[s['neo4j_id'] for s in result['vector_sources'][:3]]}")

    pipeline.close()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--vector" in args:
        run_vector_ingestion()
    elif "--graph" in args:
        run_graph_ingestion()
    elif "--test" in args:
        run_test()
    else:
        # Mặc định: chạy cả 2 ingestion
        run_vector_ingestion()
        run_graph_ingestion()
        print("\n✅ Tuần 2 hoàn tất! Dữ liệu sẵn sàng cho Tuần 3.")