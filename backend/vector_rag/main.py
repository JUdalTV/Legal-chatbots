"""
main.py — Test driver ĐỘC LẬP cho Vector RAG (không cần Graph RAG).

Yêu cầu trước khi chạy:
  - Qdrant đã chạy ở $QDRANT_HOST:$QDRANT_PORT (mặc định localhost:6333)
    → docker compose up -d qdrant
  - GPU + CUDA (embedder + reranker chạy fp16). CPU vẫn được nhưng chậm.

Lệnh:

  # 1) Ingest 1 file luật .docx hoặc .pdf vào Qdrant
  python -m backend.vector_rag.main ingest "path/to/luat.docx" --law-id LuatAnNinhMang2025 [--recreate]

  # 2) Search — auto-detect intent + k
  python -m backend.vector_rag.main search "trách nhiệm doanh nghiệp viễn thông"
  python -m backend.vector_rag.main search "Điều 15 nói gì?"  --law-id LuatAnNinhMang2025
  python -m backend.vector_rag.main search "..." --top-k 5    # override k

  # 3) Stats
  python -m backend.vector_rag.main stats
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# sys.path: cho phép chạy file trực tiếp `python backend/vector_rag/main.py ...`
_THIS = Path(__file__).resolve()
_BACKEND = _THIS.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

try:
    from dotenv import load_dotenv
    load_dotenv(_BACKEND / ".env")
except ImportError:
    pass

from vector_rag.chunker import LAW_META                # noqa: E402
from vector_rag.intent  import classify_intent, get_k  # noqa: E402
try:
    from backend.services.llm_config import (           # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
        get_llm_model,
    )
except ImportError:
    from services.llm_config import (                   # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
        get_llm_model,
    )


DEFAULT_QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
DEFAULT_QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


# ════════════════════════════════════════════════════════════════════
# Subcommands
# ════════════════════════════════════════════════════════════════════
def cmd_ingest(args: argparse.Namespace) -> int:
    from vector_rag.ingestion import ingest_file

    file_path = Path(args.file).expanduser()
    if not file_path.exists():
        print(f"[main] File không tồn tại: {file_path}")
        return 1

    summary = ingest_file(
        file_path=file_path,
        law_id=args.law_id,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        recreate=args.recreate,
        device=args.device,
        min_tokens=args.min_tokens,
        max_tokens=args.max_tokens,
        embed_batch=args.batch,
    )
    print("\n=== INGEST SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    from vector_rag.pipeline import VectorRAGPipeline

    pipe = VectorRAGPipeline(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        device=args.device,
    )
    out = pipe.search(
        args.query,
        law_id=args.law_id,
        chunk_type=args.chunk_type,
        top_k=args.top_k,
        min_rerank_score=args.min_rerank_score,
    )

    print(f"\n=== INTENT={out['intent']}  k={out['top_k']} ===\n")
    for i, r in enumerate(out["results"], 1):
        print(f"[{i}] score={r['score']:.3f}  dense={r['dense_score']:.3f}  "
              f"{r['article']} ({r['chunk_type']})")
        head = r["content"].split("\n", 1)[0][:120]
        print(f"    {head}")
    if args.show_context:
        print("\n=== CONTEXT FOR LLM ===\n")
        print(out["context"])
    return 0


def cmd_intent(args: argparse.Namespace) -> int:
    """Quick test classify_intent + get_k mà không cần Qdrant/GPU."""
    intent = classify_intent(args.query)
    print(json.dumps({"query": args.query, "intent": intent, "k": get_k(intent)},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    from vector_rag.vector_store import VectorStore
    store = VectorStore(host=args.qdrant_host, port=args.qdrant_port)
    print(json.dumps(store.get_collection_info(), ensure_ascii=False, indent=2))
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """REPL: hỏi-đáp tương tác trên terminal. Vector RAG → LLM."""
    import requests
    from vector_rag.pipeline import VectorRAGPipeline
    from vector_rag.prompt_builder import build_rag_prompt

    llm_model = get_llm_model(args.llm_model)
    pipe = VectorRAGPipeline(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        device=args.device,
    )

    print(f"\n=== Vector RAG Chat ===")
    print(f"  LLM     : {args.llm_endpoint}")
    print(f"  Model   : {llm_model}")
    if args.law_id:
        print(f"  Filter  : law_id={args.law_id}")
    print(f"  Lệnh    : /exit để thoát, /sources để toggle hiện nguồn")
    print()

    show_sources = bool(args.show_sources)

    while True:
        try:
            q = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not q:
            continue
        if q.lower() in ("/exit", "/quit", "exit", "quit", ":q"):
            break
        if q.lower() == "/sources":
            show_sources = not show_sources
            print(f"  [show_sources={show_sources}]")
            continue

        # Vector RAG
        out = pipe.search(q, law_id=args.law_id, min_rerank_score=args.min_rerank_score)
        ctx = out["context"]

        # LLM call
        messages = build_rag_prompt(q, ctx)
        try:
            resp = requests.post(
                args.llm_endpoint,
                json={
                    "model":       llm_model,
                    "messages":    messages,
                    "temperature": args.temperature,
                    "max_tokens":  args.max_tokens,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=args.timeout,
            )
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"]
        except requests.RequestException as ex:
            print(f"  [chat] LLM error: {ex}\n")
            continue

        print(f"\n{answer}\n")
        if show_sources:
            print(f"--- Nguồn (intent={out['intent']}, k={out['top_k']}) ---")
            for i, r in enumerate(out["results"][:5], 1):
                head = r["content"].split("\n", 1)[0][:90]
                print(f"  [{i}] score={r['score']:.3f}  {r['article']}  | {head}")
            print()
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """E2E nhanh: ingest + 3 search mẫu (lookup / thematic / cross_law)."""
    rc = cmd_ingest(args)
    if rc != 0:
        return rc

    from vector_rag.pipeline import VectorRAGPipeline
    pipe = VectorRAGPipeline(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        device=args.device,
    )
    sample_queries = [
        "Điều 1 nói về gì?",                              # lookup
        "Trách nhiệm của doanh nghiệp viễn thông",         # thematic
        "Trường hợp nào được phép chia sẻ dữ liệu?",       # compare
    ]
    for q in sample_queries:
        print(f"\n{'─' * 60}\n>>> {q}")
        out = pipe.search(q, law_id=args.law_id)
        print(f"   intent={out['intent']}  k={out['top_k']}")
        for i, r in enumerate(out["results"][:3], 1):
            head = r["content"].split("\n", 1)[0][:100]
            print(f"   [{i}] {r['score']:.3f}  {r['article']}  | {head}")
    return 0


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Test driver Vector RAG (Qdrant int8 + rerank).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--qdrant-host", default=DEFAULT_QDRANT_HOST)
    p.add_argument("--qdrant-port", type=int, default=DEFAULT_QDRANT_PORT)
    p.add_argument("--device", default="gpu", help="'gpu' (default) | 'cpu'")

    sub = p.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest", help="Chunk + embed + upsert 1 file luật")
    p_ing.add_argument("file", help="Đường dẫn .docx hoặc .pdf")
    p_ing.add_argument("--law-id", required=True,
                       help=f"VD: {', '.join(LAW_META)}")
    p_ing.add_argument("--recreate", action="store_true",
                       help="Xoá collection cũ trước khi ingest")
    p_ing.add_argument("--min-tokens", type=int, default=80)
    p_ing.add_argument("--max-tokens", type=int, default=400)
    p_ing.add_argument("--batch",      type=int, default=16)

    p_se = sub.add_parser("search", help="Embed + search + rerank query")
    p_se.add_argument("query")
    p_se.add_argument("--law-id",      default=None)
    p_se.add_argument("--chunk-type",  default=None,
                      choices=["article_summary", "clause", "point_group"])
    p_se.add_argument("--top-k",       type=int, default=None,
                      help="Override get_k(intent)")
    p_se.add_argument("--min-rerank-score", type=float, default=0.0,
                      help="Loại chunk có reranker score thấp hơn ngưỡng này")
    p_se.add_argument("--show-context", action="store_true",
                      help="In context formatted cho LLM")

    p_int = sub.add_parser("intent", help="Test classify_intent (không cần GPU/Qdrant)")
    p_int.add_argument("query")

    sub.add_parser("stats", help="In thống kê collection")

    p_chat = sub.add_parser("chat", help="REPL: hỏi-đáp tương tác qua LLM")
    p_chat.add_argument("--law-id", default=None, help="Lọc theo luật (optional)")
    p_chat.add_argument("--llm-endpoint", default=DEFAULT_LLM_ENDPOINT)
    p_chat.add_argument("--llm-model",    default=DEFAULT_LLM_MODEL)
    p_chat.add_argument("--temperature",  type=float, default=0.2)
    p_chat.add_argument("--max-tokens",   type=int,   default=4096)
    p_chat.add_argument("--timeout",      type=int,   default=180)
    p_chat.add_argument("--min-rerank-score", type=float, default=0.0,
                        help="Loại chunk có reranker score thấp hơn ngưỡng này")
    p_chat.add_argument("--show-sources", action="store_true",
                        help="Hiện trích nguồn sau mỗi câu trả lời")

    p_demo = sub.add_parser("demo", help="E2E: ingest + 3 search mẫu")
    p_demo.add_argument("file", help="Đường dẫn .docx hoặc .pdf")
    p_demo.add_argument("--law-id", required=True,
                        help=f"VD: {', '.join(LAW_META)}")
    p_demo.add_argument("--recreate", action="store_true")
    p_demo.add_argument("--min-tokens", type=int, default=80)
    p_demo.add_argument("--max-tokens", type=int, default=400)
    p_demo.add_argument("--batch",      type=int, default=16)

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    handlers = {
        "ingest": cmd_ingest,
        "search": cmd_search,
        "intent": cmd_intent,
        "stats":  cmd_stats,
        "chat":   cmd_chat,
        "demo":   cmd_demo,
    }
    try:
        return handlers[args.command](args)
    except ImportError as e:
        print(f"[main] Thiếu dependency: {e}")
        return 1
    except RuntimeError as e:
        print(f"[main] {e}")
        return 1
    except KeyboardInterrupt:
        print("\n[main] Đã huỷ.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

# 0) Khởi động Qdrant
# docker compose up -d qdrant

# # 1) Test intent (không cần GPU/Qdrant)
# python -m backend.vector_rag.main intent "Điều 15 nói gì?"

# # 2) INGEST 1 file → chunk + embed + upsert vào Qdrant
# python -m backend.vector_rag.main ingest "C:\AI Project\Legal-chatbots\luat116-2025.docx" --law-id LuatAnNinhMang2025 --recreate

# # 3) SEARCH
# python -m backend.vector_rag.main search "trách nhiệm doanh nghiệp viễn thông"
# python -m backend.vector_rag.main search "Điều 15 nói gì?" --law-id LuatAnNinhMang2025 --show-context
# python -m backend.vector_rag.main search "phạm vi điều chỉnh" --chunk-type article_summary

# # 4) STATS
# python -m backend.vector_rag.main stats

# # 5) DEMO E2E — ingest + chạy 3 query mẫu (lookup / thematic / compare)
# python -m backend.vector_rag.main demo "C:\AI Project\Legal-chatbots\luat116-2025.docx" --law-id LuatAnNinhMang2025 --recreate

# python -m backend.vector_rag.main chat --law-id LuatAnNinhMang2025 --show-sources
