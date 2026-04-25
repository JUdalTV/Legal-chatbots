from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parent.parent

load_dotenv(BACKEND_DIR / ".env")

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "vector_rag"))

from graph_rag.graph_retriever import GraphRetriever
from graph_rag.neo4j_loader import Neo4jKG


DEFAULT_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
DEFAULT_LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3.5-9B")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test Graph RAG ingestion and Neo4j retrieval.",
    )
    parser.add_argument("--neo4j-uri", default=DEFAULT_NEO4J_URI)
    parser.add_argument("--neo4j-user", default=DEFAULT_NEO4J_USER)
    parser.add_argument("--neo4j-password", default=DEFAULT_NEO4J_PASSWORD)

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest one law .docx into Neo4j.")
    ingest_parser.add_argument("file", nargs="?", help="Path to .docx file")
    ingest_parser.add_argument("--law-id", required=True, help="Example: LuatAnNinhMang2025")
    ingest_parser.add_argument("--ten", required=True, help="Law title")
    ingest_parser.add_argument("--so-hieu", required=True, help="Example: 24/2018/QH14")
    ingest_parser.add_argument("--nam", required=True, help="Example: 2018")
    ingest_parser.add_argument("--loai", default="Luat", help="Example: Luat, Nghi dinh")
    ingest_parser.add_argument("--wipe", action="store_true", help="Delete existing graph before ingest")
    ingest_parser.add_argument("--no-llm", action="store_true", help="Disable LLM edge extraction")
    ingest_parser.add_argument("--llm-endpoint", default=DEFAULT_LLM_ENDPOINT)
    ingest_parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    ingest_parser.add_argument("--ner-model-dir", default=None)

    context_parser = subparsers.add_parser("context", help="Print Graph RAG context for article ids.")
    context_parser.add_argument("article_ids", nargs="+", help="Example: LuatAnNinhMang2025_dieu_15")

    subparsers.add_parser("stats", help="Print current Neo4j graph stats.")
    return parser


def run_ingest(args: argparse.Namespace) -> int:
    from graph_rag.ingestion import ingest_docx

    file_path = args.file or input("Nhap duong dan file .docx: ").strip()
    if not file_path:
        print("File path is required.")
        return 1

    summary = ingest_docx(
        file_path=file_path,
        law_id=args.law_id,
        ten=args.ten,
        so_hieu=args.so_hieu,
        nam=args.nam,
        loai=args.loai,
        wipe=args.wipe,
        ner_model_dir=args.ner_model_dir,
        llm_endpoint=args.llm_endpoint,
        llm_model=args.llm_model,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        use_llm=not args.no_llm,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def run_context(args: argparse.Namespace) -> int:
    kg = Neo4jKG(args.neo4j_uri, args.neo4j_user, args.neo4j_password)
    try:
        retriever = GraphRetriever(kg)
        context = retriever.retrieve_context(args.article_ids)
        if not context:
            print("No graph context found for the given article ids.")
            return 1
        print(context)
        return 0
    finally:
        kg.close()


def run_stats(args: argparse.Namespace) -> int:
    kg = Neo4jKG(args.neo4j_uri, args.neo4j_user, args.neo4j_password)
    try:
        print(json.dumps(kg.stats(), ensure_ascii=False, indent=2))
        return 0
    finally:
        kg.close()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "ingest":
            return run_ingest(args)
        if args.command == "context":
            return run_context(args)
        if args.command == "stats":
            return run_stats(args)
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
