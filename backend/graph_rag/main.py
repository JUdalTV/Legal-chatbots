"""
main.py — Test driver ĐỘC LẬP cho Graph RAG (không cần Vector RAG / Qdrant).

Yêu cầu trước khi chạy:
  - Neo4j đã chạy ở $NEO4J_URI (mặc định bolt://localhost:7687)
    → docker compose up neo4j  (xem docker-compose.yml ở root)
  - NER model đã có ở thư mục `models/`
  - (Tuỳ chọn) LLM endpoint OpenAI-compatible — nếu không có thì dùng --no-llm

Các lệnh:

  # 1) Ingest 1 file luật .docx hoặc .pdf vào Neo4j
  python -m graph_rag.main ingest /path/to/luat.docx --law-id LuatAnNinhMang2025 [--wipe] [--no-llm]
  python -m graph_rag.main ingest /path/to/luat.pdf  --law-id LuatAnNinhMang2025 [--wipe] [--no-llm]
  # Với 3 luật đã có meta sẵn (LuatAnNinhMang2025, LuatCNTT2006, LuatVienThong2023)
  # bạn chỉ cần --law-id, các trường ten/so-hieu/nam sẽ tự suy ra.

  # 2) Xem thống kê graph
  python -m graph_rag.main stats

  # 3) Liệt kê article ids đã có trong KG
  python -m graph_rag.main articles [--law-id LuatAnNinhMang2025] [--limit 50]

  # 4) Lấy graph context của một / nhiều article (output cho LLM)
  python -m graph_rag.main context LuatAnNinhMang2025_dieu_15 LuatAnNinhMang2025_dieu_8

  # 5) Tìm article theo từ khoá (fulltext index article_fts)
  python -m graph_rag.main search "an ninh mạng"

  # 6) Demo 1-shot: wipe + ingest + in context của 3 article đầu
  python -m graph_rag.main demo /path/to/luat.docx --law-id LuatAnNinhMang2025 [--no-llm]
  python -m graph_rag.main demo /path/to/luat.pdf  --law-id LuatAnNinhMang2025 [--no-llm]

Lưu ý: chạy bằng module-mode `python -m graph_rag.main ...` từ thư mục `backend/`
       hoặc trực tiếp `python backend/graph_rag/main.py ...` cũng được
       (file tự thêm `backend/` vào sys.path).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ── sys.path setup: cho phép chạy file trực tiếp ─────────────────────
_THIS = Path(__file__).resolve()
_BACKEND = _THIS.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

try:
    from dotenv import load_dotenv
    load_dotenv(_BACKEND / ".env")
except ImportError:
    pass

from vector_rag.chunker     import LAW_META                    # noqa: E402
from graph_rag.neo4j_loader import Neo4jKG                     # noqa: E402
from graph_rag.graph_retriever import GraphRetriever           # noqa: E402
try:
    from backend.services.llm_config import (                   # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
    )
except ImportError:
    from services.llm_config import (                           # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
    )


# ── Defaults từ env ──────────────────────────────────────────────────
DEFAULT_NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
DEFAULT_NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _resolve_law_meta(law_id: str, args: argparse.Namespace) -> dict:
    """Lấy metadata luật. Ưu tiên CLI override, fallback LAW_META."""
    base = LAW_META.get(law_id, {})
    so_hieu = args.so_hieu or base.get("so_hieu")
    ten     = args.ten     or base.get("ten")
    nam     = args.nam     or (so_hieu.split("/")[1] if so_hieu and "/" in so_hieu else None)
    if not (so_hieu and ten and nam):
        raise SystemExit(
            f"[main] Thiếu metadata cho law_id={law_id!r}. "
            f"Thêm vào LAW_META hoặc truyền --ten / --so-hieu / --nam."
        )
    return {"so_hieu": so_hieu, "ten": ten, "nam": nam, "loai": args.loai or "Luật"}


def _open_kg(args: argparse.Namespace) -> Neo4jKG:
    return Neo4jKG(args.neo4j_uri, args.neo4j_user, args.neo4j_password)


# ════════════════════════════════════════════════════════════════════
# Subcommand handlers
# ════════════════════════════════════════════════════════════════════
def cmd_ingest(args: argparse.Namespace) -> int:
    from graph_rag.ingestion import ingest_docx

    file_path = Path(args.file).expanduser()
    if not file_path.exists():
        print(f"[main] File không tồn tại: {file_path}")
        return 1

    meta = _resolve_law_meta(args.law_id, args)
    summary = ingest_docx(
        file_path=file_path,
        law_id=args.law_id,
        ten=meta["ten"],
        so_hieu=meta["so_hieu"],
        nam=meta["nam"],
        loai=meta["loai"],
        wipe=args.wipe,
        ner_model_dir=args.ner_model_dir,
        llm_endpoint=args.llm_endpoint,
        llm_model=args.llm_model,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        use_llm=not args.no_llm,
    )
    print("\n=== INGEST SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    kg = _open_kg(args)
    try:
        stats = kg.stats()
    finally:
        kg.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def cmd_articles(args: argparse.Namespace) -> int:
    kg = _open_kg(args)
    try:
        with kg.driver.session() as s:
            if args.law_id:
                rows = s.run(
                    """
                    MATCH (l:LAW {id: $lid})-[:HAS_ARTICLE]->(a:ARTICLE)
                    RETURN a.id AS id, a.so AS so, a.label AS label
                    ORDER BY toInteger(replace(a.so, 'a', '')), a.so
                    LIMIT $limit
                    """,
                    lid=args.law_id, limit=args.limit,
                )
            else:
                rows = s.run(
                    """
                    MATCH (a:ARTICLE)
                    RETURN a.id AS id, a.so AS so, a.label AS label
                    ORDER BY a.id
                    LIMIT $limit
                    """,
                    limit=args.limit,
                )
            data = list(rows)
    finally:
        kg.close()

    if not data:
        print("[main] Không có article nào trong KG.")
        return 1
    for r in data:
        print(f"  {r['id']:<55}  Điều {r['so']}. {r['label']}")
    print(f"\n  Total: {len(data)} article")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    kg = _open_kg(args)
    try:
        retriever = GraphRetriever(kg)
        ctx = retriever.retrieve_context(args.article_ids)
    finally:
        kg.close()
    if not ctx:
        print("[main] Không tìm thấy article nào với các id đã cho.")
        return 1
    print(ctx)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    kg = _open_kg(args)
    try:
        with kg.driver.session() as s:
            rows = list(s.run(
                """
                CALL db.index.fulltext.queryNodes('article_fts', $q)
                YIELD node, score
                RETURN node.id AS id, node.label AS label, score
                ORDER BY score DESC
                LIMIT $limit
                """,
                q=args.query, limit=args.limit,
            ))
    finally:
        kg.close()

    if not rows:
        print(f"[main] Không có kết quả cho: {args.query!r}")
        return 1
    for r in rows:
        print(f"  {r['score']:6.2f}  {r['id']:<55}  {r['label']}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Pipeline E2E nhanh: ingest 1 file + in context của 3 article đầu."""
    rc = cmd_ingest(args)
    if rc != 0:
        return rc

    # Lấy 3 article đầu của luật vừa ingest
    kg = _open_kg(args)
    try:
        with kg.driver.session() as s:
            rows = list(s.run(
                """
                MATCH (l:LAW {id: $lid})-[:HAS_ARTICLE]->(a:ARTICLE)
                RETURN a.id AS id ORDER BY a.so LIMIT 3
                """,
                lid=args.law_id,
            ))
        sample_ids = [r["id"] for r in rows]
        print(f"\n=== STATS ===\n{json.dumps(kg.stats(), ensure_ascii=False, indent=2)}")
        if not sample_ids:
            print("[demo] Không có article nào sau khi ingest.")
            return 1

        retriever = GraphRetriever(kg)
        print(f"\n=== SAMPLE CONTEXT cho {sample_ids} ===")
        print(retriever.retrieve_context(sample_ids))
    finally:
        kg.close()
    return 0


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════
def _add_law_meta_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--law-id", required=True,
                   help=f"VD: {', '.join(LAW_META)}")
    p.add_argument("--ten",     default=None, help="Tên luật (tự suy ra nếu trong LAW_META)")
    p.add_argument("--so-hieu", default=None, help="VD: 116/2025/QH15")
    p.add_argument("--nam",     default=None, help="VD: 2025")
    p.add_argument("--loai",    default=None, help='Mặc định "Luật"')


def _add_ingest_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("file", help="Đường dẫn file .docx hoặc .pdf")
    _add_law_meta_args(p)
    p.add_argument("--wipe",          action="store_true", help="Xoá toàn bộ graph trước khi ingest")
    p.add_argument("--no-llm",        action="store_true", help="Bỏ qua bước LLM extract edges")
    p.add_argument("--ner-model-dir", default=None,        help="Override thư mục NER model")
    p.add_argument("--llm-endpoint",  default=DEFAULT_LLM_ENDPOINT)
    p.add_argument("--llm-model",     default=DEFAULT_LLM_MODEL)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test driver độc lập cho Graph RAG (Neo4j).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--neo4j-uri",      default=DEFAULT_NEO4J_URI)
    parser.add_argument("--neo4j-user",     default=DEFAULT_NEO4J_USER)
    parser.add_argument("--neo4j-password", default=DEFAULT_NEO4J_PASSWORD)

    sub = parser.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest 1 file luật .docx vào Neo4j")
    _add_ingest_args(p_ing)

    sub.add_parser("stats", help="In thống kê graph hiện tại")

    p_art = sub.add_parser("articles", help="Liệt kê article ids trong graph")
    p_art.add_argument("--law-id", default=None, help="Lọc theo luật (optional)")
    p_art.add_argument("--limit",  type=int, default=50)

    p_ctx = sub.add_parser("context", help="In graph context cho article ids")
    p_ctx.add_argument("article_ids", nargs="+",
                       help="VD: LuatAnNinhMang2025_dieu_15")

    p_sea = sub.add_parser("search", help="Fulltext search trên ARTICLE")
    p_sea.add_argument("query")
    p_sea.add_argument("--limit", type=int, default=10)

    p_demo = sub.add_parser("demo", help="E2E nhanh: ingest + context")
    _add_ingest_args(p_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "ingest":   cmd_ingest, 
        "stats":    cmd_stats,  # đếm node/edge
        "articles": cmd_articles, # list điều đã ingest
        "context":  cmd_context, # graph context cho LLM
        "search":   cmd_search, # fulltext trên ARTICLE
        "demo":     cmd_demo, # E2E
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

# # Ingest 1 file luật (auto-suy ra metadata nếu law_id có trong LAW_META)
# python -m graph_rag.main ingest path/to/luat.docx --law-id LuatAnNinhMang2025 --wipe [--no-llm]

# python -m graph_rag.main stats                                   # đếm node/edge
# python -m graph_rag.main articles --law-id LuatAnNinhMang2025    # list điều đã ingest
# python -m graph_rag.main context LuatAnNinhMang2025_dieu_15      # graph context cho LLM
# python -m graph_rag.main search "an ninh mạng"                   # fulltext trên ARTICLE
# python -m graph_rag.main demo path/to/luat.docx --law-id LuatAnNinhMang2025  # E2E
