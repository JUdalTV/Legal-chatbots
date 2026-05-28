"""
Run the legal QA benchmark set and write question/answer pairs to Markdown.

Default mode calls the local HybridRAGService directly. Use --mode api if the
FastAPI server is already running, or --mode json to export existing answers
from the benchmark JSON files without calling the RAG pipeline.

Examples:
    python benchmark/run_qa_to_md.py
    python benchmark/run_qa_to_md.py --mode api --api-url http://localhost:8000
    python benchmark/run_qa_to_md.py --mode json --answer-field ground_truth
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DATASETS: dict[str, dict[str, str | Path]] = {
    "anm": {
        "title": "Luật An ninh mạng 116/2025/QH15",
        "law_id": "LuatAnNinhMang2025",
        "path": ROOT / "benchmark" / "benchmark_luatAnNinhMang.json",
    },
    "vt": {
        "title": "Luật Viễn thông 24/2023/QH15",
        "law_id": "LuatVienThong2023",
        "path": ROOT / "benchmark" / "benchmark_luatVienThong.json",
    },
    "cntt": {
        "title": "Luật Công nghệ thông tin 65/VBHN-VPQH",
        "law_id": "LuatCNTT2025",
        "path": ROOT / "benchmark" / "benchmark_luatCNTT.json",
    },
}

DIFFICULTY_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}


@dataclass(frozen=True)
class QAItem:
    dataset_key: str
    law_title: str
    law_id: str
    item_id: str
    difficulty: str
    question: str
    reference: str
    model_answer: str
    ground_truth: str


class Answerer(Protocol):
    def answer(self, item: QAItem) -> tuple[str, dict[str, Any]]:
        ...

    def close(self) -> None:
        ...


class JsonAnswerer:
    def __init__(self, field: str):
        self.field = field

    def answer(self, item: QAItem) -> tuple[str, dict[str, Any]]:
        answer = getattr(item, self.field, "")
        return answer or "[Không có câu trả lời trong JSON]", {}

    def close(self) -> None:
        return None


class ApiAnswerer:
    def __init__(self, args: argparse.Namespace):
        import requests

        self.requests = requests
        self.api_url = args.api_url.rstrip("/")
        self.timeout = args.timeout
        self.top_k = args.top_k
        self.temperature = args.temperature
        self.max_tokens = args.max_tokens
        self.thinking = args.thinking
        self.include_meta = args.include_meta

    def answer(self, item: QAItem) -> tuple[str, dict[str, Any]]:
        resp = self.requests.post(
            f"{self.api_url}/api/chat",
            json={
                "query": item.question,
                "law_id": item.law_id,
                "thinking_mode": self.thinking,
                "top_k": self.top_k,
                "include_context": self.include_meta,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer", ""), {
            "intent": data.get("intent"),
            "refined": (data.get("refined") or {}).get("refined"),
            "thinking_used": data.get("thinking_used"),
            "graph_article_ids": data.get("graph_article_ids"),
        }

    def close(self) -> None:
        return None


class RagAnswerer:
    def __init__(self, args: argparse.Namespace):
        from backend.services.hybrid_rag_service import HybridRAGService

        self.service = HybridRAGService(
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port,
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
            device=args.device,
            min_rerank_score=args.min_rerank_score,
            enable_refine=not args.no_refine,
        )
        self.top_k = args.top_k
        self.temperature = args.temperature
        self.max_tokens = args.max_tokens
        self.thinking = args.thinking
        self.include_meta = args.include_meta

    def answer(self, item: QAItem) -> tuple[str, dict[str, Any]]:
        result = self.service.answer(
            item.question,
            law_id=item.law_id,
            top_k=self.top_k,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            thinking_mode=self.thinking,
        )
        meta = {
            "intent": (result.refined or {}).get("intent"),
            "refined": (result.refined or {}).get("refined"),
            "thinking_used": None,
            "graph_article_ids": result.graph_article_ids,
        }
        return result.answer, meta

    def close(self) -> None:
        self.service.close()


def load_items(dataset_keys: list[str]) -> list[QAItem]:
    items: list[QAItem] = []
    for key in dataset_keys:
        spec = DATASETS[key]
        path = Path(spec["path"])
        with path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)

        rows = data.get("results") or data.get("questions") or []
        for idx, row in enumerate(rows, 1):
            item_id = str(row.get("id") or f"Q{idx:03d}")
            items.append(
                QAItem(
                    dataset_key=key,
                    law_title=str(spec["title"]),
                    law_id=str(spec["law_id"]),
                    item_id=item_id,
                    difficulty=str(row.get("difficulty") or "unknown").lower(),
                    question=str(row.get("question") or "").strip(),
                    reference=str(row.get("reference") or "").strip(),
                    model_answer=str(row.get("model_answer") or "").strip(),
                    ground_truth=str(row.get("ground_truth") or "").strip(),
                )
            )
    return [item for item in items if item.question]


def make_answerer(args: argparse.Namespace) -> Answerer:
    if args.mode == "json":
        return JsonAnswerer(args.answer_field)
    if args.mode == "api":
        return ApiAnswerer(args)
    return RagAnswerer(args)


def write_header(f, args: argparse.Namespace, total: int) -> None:
    f.write("# Bộ câu hỏi và câu trả lời benchmark pháp luật\n\n")
    f.write(f"- Thời điểm chạy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"- Chế độ: `{args.mode}`\n")
    f.write(f"- Tổng số câu hỏi: {total}\n")
    if args.mode in {"rag", "api"}:
        f.write(f"- Thinking mode: `{args.thinking}`\n")
        f.write(f"- Temperature: `{args.temperature}`\n")
        f.write(f"- Top K: `{args.top_k}`\n")
    if args.mode == "json":
        f.write(f"- Trường câu trả lời: `{args.answer_field}`\n")
    f.write("\n")


def write_item(
    f,
    number: int,
    item: QAItem,
    answer: str,
    *,
    elapsed: float | None = None,
    meta: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    f.write(f"#### {number}. {item.item_id}\n\n")
    if item.reference:
        f.write(f"- Căn cứ kỳ vọng: {item.reference}\n")
    if elapsed is not None:
        f.write(f"- Thời gian trả lời: {elapsed:.1f}s\n")
    f.write("\n")
    f.write(f"**Câu hỏi:** {item.question}\n\n")
    f.write("**Trả lời:**\n\n")
    if error:
        f.write(f"> Lỗi khi chạy câu hỏi: `{error}`\n\n")
    else:
        f.write((answer or "[Không có câu trả lời]").strip())
        f.write("\n\n")

    if meta:
        visible_meta = {
            k: v for k, v in meta.items()
            if v not in (None, "", [], {})
        }
        if visible_meta:
            f.write("<details>\n<summary>Meta</summary>\n\n")
            for key, value in visible_meta.items():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n</details>\n\n")


def _split_output_path(base: Path, dataset_key: str) -> Path:
    if base.suffix.lower() == ".md":
        return base.with_name(f"{base.stem}_{dataset_key}{base.suffix}")
    return base / f"legal_qa_answers_{dataset_key}.md"


def _group_by_dataset(items: list[QAItem], dataset_keys: list[str]) -> dict[str, list[QAItem]]:
    grouped: dict[str, list[QAItem]] = {key: [] for key in dataset_keys}
    for item in items:
        grouped.setdefault(item.dataset_key, []).append(item)
    return {key: values for key, values in grouped.items() if values}


def _write_items(
    *,
    args: argparse.Namespace,
    items: list[QAItem],
    output: Path,
    answerer: Answerer,
    progress_label: str,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    current_law = ""
    current_difficulty = ""

    with output.open("w", encoding="utf-8", newline="\n") as f:
        write_header(f, args, len(items))

        for index, item in enumerate(items, 1):
            if item.law_title != current_law:
                current_law = item.law_title
                current_difficulty = ""
                f.write(f"## {current_law}\n\n")

            if item.difficulty != current_difficulty:
                current_difficulty = item.difficulty
                label = DIFFICULTY_LABELS.get(item.difficulty, item.difficulty.title())
                f.write(f"### {label}\n\n")

            print(
                f"[{progress_label} {index}/{len(items)}] "
                f"{item.item_id} | {item.difficulty}",
                flush=True,
            )

            start = time.perf_counter()
            try:
                answer, meta = answerer.answer(item)
                elapsed = time.perf_counter() - start
                write_item(
                    f,
                    index,
                    item,
                    answer,
                    elapsed=elapsed if args.mode != "json" else None,
                    meta=meta if args.include_meta else None,
                )
            except Exception as ex:
                elapsed = time.perf_counter() - start
                error = f"{type(ex).__name__}: {ex}"
                write_item(
                    f,
                    index,
                    item,
                    "",
                    elapsed=elapsed if args.mode != "json" else None,
                    error=error,
                )
                f.flush()
                if args.stop_on_error:
                    raise

            f.flush()

    return output


def run(args: argparse.Namespace) -> int:
    items = load_items(args.only)
    if args.limit:
        items = items[: args.limit]

    output = Path(args.output)
    answerer = make_answerer(args)
    grouped = _group_by_dataset(items, args.only)
    split_by_law = len(grouped) > 1 and not args.single_file

    try:
        if split_by_law:
            max_workers = max(1, min(args.parallel_laws, len(grouped)))
            written: list[Path] = []
            print(
                f"Running {len(grouped)} laws in parallel "
                f"(workers={max_workers}, thinking={args.thinking}).",
                flush=True,
            )
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(
                        _write_items,
                        args=args,
                        items=law_items,
                        output=_split_output_path(output, key),
                        answerer=answerer,
                        progress_label=key,
                    ): key
                    for key, law_items in grouped.items()
                }
                for future in as_completed(futures):
                    written.append(future.result())

            print("\nDone. Wrote:", flush=True)
            for path in sorted(written):
                print(f"  {path}", flush=True)
            return 0

        written = _write_items(
            args=args,
            items=items,
            output=output,
            answerer=answerer,
            progress_label="all",
        )
        print(f"\nDone. Wrote: {written}", flush=True)
        return 0
    finally:
        answerer.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run legal QA questions and export answers to Markdown."
    )
    p.add_argument(
        "--mode",
        choices=("rag", "api", "json"),
        default="rag",
        help="rag = call HybridRAGService, api = POST /api/chat, json = export existing JSON answers",
    )
    p.add_argument(
        "--output",
        default=str(ROOT / "benchmark" / "legal_qa_answers.md"),
        help=(
            "Markdown output path. With multiple laws, default split mode writes "
            "<stem>_anm.md, <stem>_vt.md, <stem>_cntt.md."
        ),
    )
    p.add_argument(
        "--only",
        nargs="+",
        choices=tuple(DATASETS.keys()),
        default=list(DATASETS.keys()),
        help="Datasets to run: anm vt cntt.",
    )
    p.add_argument("--limit", type=int, default=None, help="Run only the first N questions.")
    p.add_argument(
        "--answer-field",
        choices=("model_answer", "ground_truth"),
        default="model_answer",
        help="Used only with --mode json.",
    )

    p.add_argument("--api-url", default="http://localhost:8000")
    p.add_argument("--timeout", type=int, default=900, help="HTTP timeout in seconds.")

    p.add_argument("--qdrant-host", default=os.getenv("QDRANT_HOST", "localhost"))
    p.add_argument("--qdrant-port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))
    p.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    p.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    p.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", "12345678"))
    p.add_argument("--device", default=os.getenv("RAG_DEVICE", "gpu"))
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--min-rerank-score", type=float, default=0.30)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--thinking", choices=("auto", "on", "off"), default="off")
    p.add_argument(
        "--parallel-laws",
        type=int,
        default=3,
        help="Number of law-level workers when writing split Markdown files.",
    )
    p.add_argument(
        "--single-file",
        action="store_true",
        help="Write one combined Markdown file and run questions sequentially.",
    )
    p.add_argument("--no-refine", action="store_true")
    p.add_argument("--include-meta", action="store_true")
    p.add_argument("--stop-on-error", action="store_true")
    return p


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
