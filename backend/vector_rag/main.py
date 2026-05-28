"""
Vector-only QA benchmark runner.

This CLI runs the 90 benchmark questions through Vector RAG only:
Qdrant dense/sparse search + reranker -> vector context -> LLM answer.
It does not import or call Graph RAG, Neo4j, or graph retrievers.

It always starts exactly three law-level workers: one for each benchmark law.

Run:
    python -m backend.vector_rag.main
    python -m backend.vector_rag.main --limit-per-law 2
    python -m backend.vector_rag.main --no-refine
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DEFAULT_QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
DEFAULT_QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


DATASETS: list[dict[str, Any]] = [
    {
        "key": "anm",
        "title": "Luật An ninh mạng 116/2025/QH15",
        "law_id": "LuatAnNinhMang2025",
        "source": ROOT / "benchmark" / "benchmark_luatAnNinhMang.json",
        "md_source": ROOT / "benchmark" / "metric_benchmark" / "legal_qa_answers_anm.md",
        "json_name": "benchmark_luatAnNinhMang.json",
    },
    {
        "key": "vt",
        "title": "Luật Viễn thông 24/2023/QH15",
        "law_id": "LuatVienThong2023",
        "source": ROOT / "benchmark" / "benchmark_luatVienThong.json",
        "md_source": ROOT / "benchmark" / "metric_benchmark" / "legal_qa_answers_vt.md",
        "json_name": "benchmark_luatVienThong.json",
    },
    {
        "key": "cntt",
        "title": "Luật Công nghệ thông tin 65/VBHN-VPQH",
        "law_id": "LuatCNTT2025",
        "source": ROOT / "benchmark" / "benchmark_luatCNTT.json",
        "md_source": ROOT / "benchmark" / "metric_benchmark" / "legal_qa_answers_cntt.md",
        "json_name": "benchmark_luatCNTT.json",
    },
]

GROUNDTRUTH_MD = ROOT / "benchmark" / "metric_benchmark" / "Dap_an_90_cau_hoi_groundtruth.md"


DIFFICULTY_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}


@dataclass(frozen=True)
class QAItem:
    index: int
    item_id: str
    difficulty: str
    question: str
    reference: str
    ground_truth: str


@dataclass
class VectorAnswer:
    answer: str
    refined: dict[str, Any]
    vector_context: str
    vector_results: list[dict[str, Any]]
    low_confidence: bool
    elapsed: float


class VectorOnlyRAGService:
    def __init__(
        self,
        *,
        qdrant_host: str,
        qdrant_port: int,
        device: str,
        min_rerank_score: float,
        enable_refine: bool,
    ) -> None:
        from backend.services.llm_client import LLMClient
        from backend.vector_rag.pipeline import VectorRAGPipeline

        self.vector = VectorRAGPipeline(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            device=device,
            min_rerank_score=min_rerank_score,
        )
        self.llm = LLMClient()
        self.enable_refine = enable_refine

    def answer(
        self,
        query: str,
        *,
        law_id: str,
        top_k: int | None,
        min_rerank_score: float | None,
        temperature: float,
        max_tokens: int,
    ) -> VectorAnswer:
        from backend.services.query_refiner import refine_and_decompose_query
        from backend.vector_rag.intent import classify_intent
        from backend.vector_rag.prompt_builder import build_rag_prompt

        start = time.perf_counter()
        intent = classify_intent(query)
        if self.enable_refine:
            refined = refine_and_decompose_query(
                query,
                intent=intent,
                law_id=law_id,
                llm=self.llm,
            )
        else:
            refined = {
                "original": query,
                "intent": intent,
                "objective": "",
                "refined": query,
                "subqueries": [],
            }

        retrieval_query = refined.get("refined") or query
        subqueries = refined.get("subqueries") or []
        search_queries = subqueries if len(subqueries) >= 2 else [retrieval_query]
        vector_out = self._search_many(
            search_queries,
            law_id=law_id,
            top_k=top_k,
            min_rerank_score=min_rerank_score,
        )

        context = vector_out.get("context", "")
        messages = build_rag_prompt(query, context)
        answer = self.llm.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=False,
            extra_payload={"top_p": 0.9, "repetition_penalty": 1.05},
        )

        return VectorAnswer(
            answer=answer,
            refined=refined,
            vector_context=context,
            vector_results=vector_out.get("results", []),
            low_confidence=bool(vector_out.get("low_confidence", False)),
            elapsed=time.perf_counter() - start,
        )

    def _search_many(
        self,
        queries: list[str],
        *,
        law_id: str,
        top_k: int | None,
        min_rerank_score: float | None,
    ) -> dict[str, Any]:
        if len(queries) == 1:
            return self.vector.search(
                queries[0],
                law_id=law_id,
                top_k=top_k,
                min_rerank_score=min_rerank_score,
            )

        from backend.vector_rag.reranker import format_context_for_llm

        outs = [
            self.vector.search(
                q,
                law_id=law_id,
                top_k=top_k,
                min_rerank_score=min_rerank_score,
            )
            for q in queries
        ]
        merged: dict[str, dict[str, Any]] = {}
        low_confidence = True
        for out in outs:
            low_confidence = low_confidence and bool(out.get("low_confidence", False))
            for row in out.get("results", []):
                key = row.get("chunk_id") or row.get("article") or row.get("neo4j_id")
                if not key:
                    key = json.dumps(row, ensure_ascii=False, sort_keys=True)
                current = merged.get(key)
                if current is None or float(row.get("score") or 0.0) > float(current.get("score") or 0.0):
                    merged[key] = row

        k = top_k or max((int(out.get("top_k") or 0) for out in outs), default=5)
        results = sorted(
            merged.values(),
            key=lambda row: float(row.get("score") or 0.0),
            reverse=True,
        )[:k]
        if low_confidence:
            for row in results:
                row["low_confidence"] = True

        return {
            "intent": outs[0].get("intent", ""),
            "top_k": k,
            "results": results,
            "context": format_context_for_llm(results),
            "low_confidence": low_confidence,
        }


def _rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("results") or data.get("questions")
    if not isinstance(rows, list):
        raise ValueError("Benchmark JSON must contain a list in `results` or `questions`.")
    return rows


_ITEM_HEADING_RE = re.compile(r"^####\s+\d+\.\s+(.+?)\s*$")
_QUESTION_LINE_RE = re.compile(r"^\*\*Câu hỏi:\*\*\s*(.+?)\s*$")
_REFERENCE_LINE_RE = re.compile(r"^-\s+Căn cứ kỳ vọng:\s*(.+?)\s*$")
_GT_HEADING_RE = re.compile(r"^####\s+Câu\s+(\d+)\.\s*(.+?)\s*$", re.IGNORECASE)


def _dataset_key_from_title(line: str) -> str | None:
    lowered = line.lower()
    if "an ninh" in lowered:
        return "anm"
    if "viễn thông" in lowered:
        return "vt"
    if "cntt" in lowered or "công nghệ thông tin" in lowered:
        return "cntt"
    return None


def _parse_groundtruth_md(path: Path = GROUNDTRUTH_MD) -> dict[str, dict[int, str]]:
    out: dict[str, dict[int, str]] = {"anm": {}, "vt": {}, "cntt": {}}
    if not path.exists():
        return out

    current_key: str | None = None
    current_no: int | None = None
    answer_lines: list[str] = []

    def flush() -> None:
        nonlocal current_no, answer_lines
        if current_key and current_no is not None:
            answer = "\n".join(answer_lines).strip()
            out.setdefault(current_key, {})[current_no] = answer
        current_no = None
        answer_lines = []

    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            flush()
            detected = _dataset_key_from_title(line)
            if detected:
                current_key = detected
            continue

        m = _GT_HEADING_RE.match(line)
        if m:
            flush()
            current_no = int(m.group(1))
            continue

        if current_no is not None:
            answer_lines.append(line)

    flush()
    return out


def _parse_questions_md(spec: dict[str, Any]) -> dict[str, Any]:
    path = Path(spec["md_source"])
    if not path.exists():
        raise FileNotFoundError(path)

    gt_by_no = _parse_groundtruth_md().get(str(spec["key"]), {})
    rows: list[dict[str, Any]] = []
    current_difficulty = "unknown"
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current and current.get("question"):
            rows.append(current)
        current = None

    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line.startswith("### "):
            label = line[4:].strip().lower()
            if label.startswith("easy"):
                current_difficulty = "easy"
            elif label.startswith("medium"):
                current_difficulty = "medium"
            elif label.startswith("hard"):
                current_difficulty = "hard"
            continue

        m = _ITEM_HEADING_RE.match(line)
        if m:
            flush()
            item_no = len(rows) + 1
            current = {
                "id": m.group(1).strip(),
                "difficulty": current_difficulty,
                "category": "",
                "reference": "",
                "question": "",
                "ground_truth": gt_by_no.get(item_no, ""),
                "model_answer": "",
            }
            continue

        if current is None:
            continue

        m = _REFERENCE_LINE_RE.match(line)
        if m:
            current["reference"] = m.group(1).strip()
            continue

        m = _QUESTION_LINE_RE.match(line)
        if m:
            current["question"] = m.group(1).strip()
            continue

    flush()
    return {
        "metadata": {
            "title": f"Vector benchmark source parsed from {path.name}",
            "source": str(path),
            "total_questions": len(rows),
        },
        "results": rows,
    }


def _load_dataset(spec: dict[str, Any], *, resume_json: Path | None) -> tuple[dict[str, Any], list[QAItem]]:
    source = Path(spec["source"])
    if resume_json and resume_json.exists():
        data = json.loads(resume_json.read_text(encoding="utf-8-sig"))
    elif Path(spec["md_source"]).exists():
        data = _parse_questions_md(spec)
    elif source.exists():
        data = json.loads(source.read_text(encoding="utf-8-sig"))
    else:
        raise FileNotFoundError(f"Missing both {spec['md_source']} and {source}")

    items: list[QAItem] = []
    for idx, row in enumerate(_rows(data), 1):
        question = str(row.get("question") or "").strip()
        if not question:
            continue
        items.append(
            QAItem(
                index=idx,
                item_id=str(row.get("id") or f"Q{idx:03d}"),
                difficulty=str(row.get("difficulty") or "unknown").lower(),
                question=question,
                reference=str(row.get("reference") or "").strip(),
                ground_truth=str(row.get("ground_truth") or "").strip(),
            )
        )
    return data, items


def _source_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in results:
        meta = row.get("metadata") or {}
        out.append(
            {
                "score": row.get("score"),
                "dense_score": row.get("dense_score"),
                "chunk_id": row.get("chunk_id"),
                "law_id": row.get("law_id"),
                "article": row.get("article") or row.get("neo4j_id"),
                "clause": row.get("clause"),
                "chunk_type": row.get("chunk_type"),
                "article_label": meta.get("article_label"),
                "clause_label": meta.get("clause_label"),
            }
        )
    return out


def _write_md_header(f, spec: dict[str, Any], args: argparse.Namespace, total: int) -> None:
    f.write(f"# Vector-only benchmark - {spec['title']}\n\n")
    f.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("- Pipeline: Vector RAG only (Qdrant + reranker + LLM)\n")
    f.write("- Graph RAG / Neo4j: disabled\n")
    f.write("- Thinking: off\n")
    f.write(f"- Query refine: {'on' if not args.no_refine else 'off'}\n")
    f.write(f"- Total questions: {total}\n\n")


def _write_md_item(f, no: int, item: QAItem, result: VectorAnswer | None, error: str | None) -> None:
    f.write(f"#### {no}. {item.item_id}\n\n")
    if item.reference:
        f.write(f"- Expected reference: {item.reference}\n")
    if result is not None:
        f.write(f"- Elapsed: {result.elapsed:.1f}s\n")
        f.write(f"- Low confidence: {result.low_confidence}\n")
    f.write("\n")
    f.write(f"**Question:** {item.question}\n\n")
    f.write("**Answer:**\n\n")
    if error:
        f.write(f"> Error: `{error}`\n\n")
    else:
        f.write((result.answer if result else "[No answer]").strip())
        f.write("\n\n")


def _output_paths(spec: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    return (
        out_dir / f"legal_qa_answers_vector_{spec['key']}.md",
        out_dir / str(spec["json_name"]),
    )


def _run_law(spec: dict[str, Any], args: argparse.Namespace) -> tuple[str, Path, Path]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path, json_path = _output_paths(spec, out_dir)
    resume_path = json_path if args.resume and json_path.exists() else None
    data, items = _load_dataset(spec, resume_json=resume_path)
    can_skip_existing = resume_path is not None
    if args.limit_per_law:
        items = items[: args.limit_per_law]

    rows = _rows(data)
    service = VectorOnlyRAGService(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        device=args.device,
        min_rerank_score=args.min_rerank_score,
        enable_refine=not args.no_refine,
    )

    try:
        with md_path.open("w", encoding="utf-8", newline="\n") as f:
            _write_md_header(f, spec, args, len(items))
            current_difficulty = ""
            for local_no, item in enumerate(items, 1):
                if item.difficulty != current_difficulty:
                    current_difficulty = item.difficulty
                    label = DIFFICULTY_LABELS.get(item.difficulty, item.difficulty.title())
                    f.write(f"### {label}\n\n")

                row = rows[item.index - 1]
                if can_skip_existing and str(row.get("model_answer") or "").strip():
                    print(f"[{spec['key']} {local_no}/{len(items)}] skip {item.item_id}", flush=True)
                    _write_md_item(
                        f,
                        local_no,
                        item,
                        VectorAnswer(
                            answer=str(row.get("model_answer") or ""),
                            refined={"refined": row.get("refined_query", item.question)},
                            vector_context="",
                            vector_results=[],
                            low_confidence=bool((row.get("vector_only") or {}).get("low_confidence", False)),
                            elapsed=0.0,
                        ),
                        None,
                    )
                    continue

                print(f"[{spec['key']} {local_no}/{len(items)}] run {item.item_id}", flush=True)
                try:
                    result = service.answer(
                        item.question,
                        law_id=str(spec["law_id"]),
                        top_k=args.top_k,
                        min_rerank_score=args.min_rerank_score,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                    )
                    row["model_answer"] = result.answer
                    row["refined_query"] = result.refined.get("refined", item.question)
                    row["vector_only"] = {
                        "intent": result.refined.get("intent"),
                        "objective": result.refined.get("objective", ""),
                        "subqueries": result.refined.get("subqueries", []),
                        "low_confidence": result.low_confidence,
                        "sources": _source_summary(result.vector_results),
                    }
                    _write_md_item(f, local_no, item, result, None)
                except Exception as ex:
                    error = f"{type(ex).__name__}: {ex}"
                    row["model_answer"] = ""
                    row["vector_only"] = {"error": error}
                    _write_md_item(f, local_no, item, None, error)
                    f.flush()
                    json_path.write_text(
                        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    if args.stop_on_error:
                        raise

                f.flush()
                json_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

        return str(spec["key"]), md_path, json_path
    finally:
        # VectorRAGPipeline owns HTTP clients/models only; no explicit close.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run vector-only RAG benchmark for all 3 laws.")
    parser.add_argument("--out-dir", default=str(ROOT / "benchmark" / "vector_benchmark"))
    parser.add_argument("--qdrant-host", default=DEFAULT_QDRANT_HOST)
    parser.add_argument("--qdrant-port", type=int, default=DEFAULT_QDRANT_PORT)
    parser.add_argument("--device", default=os.getenv("RAG_DEVICE", "gpu"))
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--min-rerank-score", type=float, default=0.30)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--no-refine", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument(
        "--limit-per-law",
        type=int,
        default=None,
        help="Smoke-test only the first N questions per law; still starts 3 law workers.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    print("Running vector-only benchmark with exactly 3 law workers.", flush=True)
    print("Graph RAG / Neo4j is not used.", flush=True)
    print("Thinking is forced off for answer generation.", flush=True)

    outputs: list[tuple[str, Path, Path]] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_run_law, spec, args) for spec in DATASETS]
        for future in as_completed(futures):
            outputs.append(future.result())

    print("\nDone. Outputs:", flush=True)
    for key, md_path, json_path in sorted(outputs):
        print(f"  [{key}] {md_path}", flush=True)
        print(f"       {json_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
