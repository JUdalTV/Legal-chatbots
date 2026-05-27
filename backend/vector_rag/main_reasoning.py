"""
Vector-only reasoning benchmark runner.

Chạy LLM với **chế độ reasoning bật** (enable_thinking=True) trên các tình huống
thực tế phức tạp trong `benchmark/claude_benchmark/hybrid_reasoning/`.

Cấu trúc input:
    benchmark/claude_benchmark/hybrid_reasoning/
    ├── tinh_huong_thuc_te_suy_luan/
    │   ├── An_Ninh_Mang.docx          (10 câu, luật ANM)
    │   ├── Vien_thong.docx            (10 câu, luật VT)
    │   └── CNTT.docx                  (10 câu, luật CNTT)
    ├── tinh_huong_thuc_te_phap_ly_chuyen_sau/
    │   ├── An_Ninh_Mang.docx
    │   ├── Vien_Thong.docx
    │   └── CNTT.docx
    └── ket_hop_luat/
        └── Lien_luat_Cau_hoi_va_Cau_tra_loi.docx   (câu hỏi đa luật)

Output:
    benchmark/claude_benchmark/vector_reasoning/
    ├── tinh_huong_thuc_te_suy_luan/{An_Ninh_Mang,Vien_thong,CNTT}.md
    ├── tinh_huong_thuc_te_phap_ly_chuyen_sau/{An_Ninh_Mang,Vien_Thong,CNTT}.md
    └── ket_hop_luat/Lien_luat_Cau_hoi_va_Cau_tra_loi.md

Concurrency: 7 worker song song (3 cho suy_luan + 3 cho phap_ly_chuyen_sau + 1
cho ket_hop_luat). Mỗi worker chạy câu hỏi tuần tự trong 1 file docx.

Run:
    python -m backend.vector_rag.main_reasoning
"""
from __future__ import annotations

import argparse
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

BASE_IN  = ROOT / "benchmark" / "claude_benchmark" / "hybrid_reasoning"
BASE_OUT = ROOT / "benchmark" / "claude_benchmark" / "vector_reasoning"


# ══════════════════════════════════════════════════════════════════════
# Task spec
# ══════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class TaskFile:
    task: str           # subdir name (suy_luan / phap_ly_chuyen_sau / ket_hop_luat)
    name: str           # docx stem (An_Ninh_Mang, Vien_thong, CNTT, ...)
    src: Path           # input docx
    out: Path           # output md
    law_id: str | None  # None nếu cross-law (ket_hop_luat)
    law_title: str


# Map docx filename → (law_id, law_title)
_LAW_BY_FILENAME = {
    "An_Ninh_Mang":  ("LuatAnNinhMang2025",  "Luật An ninh mạng 116/2025/QH15"),
    "Vien_Thong":    ("LuatVienThong2023",   "Luật Viễn thông 24/2023/QH15"),
    "Vien_thong":    ("LuatVienThong2023",   "Luật Viễn thông 24/2023/QH15"),
    "CNTT":          ("LuatCNTT2025",        "Luật Công nghệ thông tin 65/VBHN-VPQH"),
}


def discover_tasks() -> list[TaskFile]:
    """Quét BASE_IN, sinh danh sách TaskFile cho từng docx."""
    tasks: list[TaskFile] = []
    for sub in ("tinh_huong_thuc_te_suy_luan",
                "tinh_huong_thuc_te_phap_ly_chuyen_sau",
                "ket_hop_luat"):
        in_dir = BASE_IN / sub
        if not in_dir.exists():
            print(f"[warn] skip missing {in_dir}")
            continue
        out_dir = BASE_OUT / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        for docx in sorted(in_dir.glob("*.docx")):
            stem = docx.stem
            if sub == "ket_hop_luat":
                law_id = None
                law_title = "Liên luật (cross-law)"
            else:
                law = _LAW_BY_FILENAME.get(stem)
                if law is None:
                    print(f"[warn] không map được law cho {docx} — bỏ qua")
                    continue
                law_id, law_title = law
            tasks.append(TaskFile(
                task=sub, name=stem, src=docx,
                out=out_dir / f"{stem}.md",
                law_id=law_id, law_title=law_title,
            ))
    return tasks


# ══════════════════════════════════════════════════════════════════════
# DOCX parser
# ══════════════════════════════════════════════════════════════════════
# Chỉ chấp nhận bảng MỞ ĐẦU bằng "Câu N." hoặc "Câu hỏi" (chứ KHÔNG phải bảng
# phụ kiểu "Hành vi", "Giai đoạn"… chèn giữa câu hỏi).
_RX_QUESTION_TABLE = re.compile(
    r"^\s*C[aâ]u\s+(?:\d+\.?|h[ỏo]i\b)",
    re.IGNORECASE,
)
_RX_STRIP_LEADING = re.compile(
    r"^\s*C[aâ]u\s+(?:\d+\s*\.?\s*|h[ỏo]i\s*[:\.]?\s*)",
    re.IGNORECASE,
)


def parse_questions(docx_path: Path) -> list[dict[str, str]]:
    """
    Mỗi docx chứa N tables; câu hỏi nằm trong các table có ô đầu mở đầu bằng
    "Câu N." (suy_luan/ket_hop_luat) hoặc "Câu hỏi" (phap_ly_chuyen_sau).
    Bỏ qua các bảng phụ khác (vd "Hành vi", "Giai đoạn") xen kẽ.
    """
    from docx import Document

    doc = Document(str(docx_path))
    out: list[dict[str, str]] = []
    qno = 0
    for tbl in doc.tables:
        if not tbl.rows:
            continue
        raw = tbl.rows[0].cells[0].text.strip()
        if not raw or not _RX_QUESTION_TABLE.match(raw):
            continue

        # Bỏ tiền tố "Câu N." / "Câu hỏi" để giữ nội dung thuần
        text = _RX_STRIP_LEADING.sub("", raw, count=1).strip()
        if not text:
            continue
        qno += 1
        out.append({"qno": str(qno), "question": text})
    return out


# ══════════════════════════════════════════════════════════════════════
# Vector RAG service (enable_thinking=True)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class VectorAnswer:
    answer: str
    refined: dict[str, Any]
    low_confidence: bool
    elapsed: float


class VectorReasoningService:
    """
    Vector RAG only, LLM call với enable_thinking=True (reasoning mode).
    """

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
        law_id: str | None,
        top_k: int | None,
        min_rerank_score: float | None,
        temperature: float,
        max_tokens: int,
    ) -> VectorAnswer:
        from backend.services.query_refiner import refine_and_decompose_query
        from backend.vector_rag.intent import classify_intent
        from backend.vector_rag.prompt_builder import build_rag_prompt
        from backend.vector_rag.reranker import format_context_for_llm

        start = time.perf_counter()
        intent = classify_intent(query)
        if self.enable_refine:
            refined = refine_and_decompose_query(
                query, intent=intent, law_id=law_id, llm=self.llm,
            )
        else:
            refined = {
                "original": query, "intent": intent,
                "objective": "", "refined": query, "subqueries": [],
            }

        retrieval_query = refined.get("refined") or query
        subqueries = refined.get("subqueries") or []
        search_queries = subqueries if len(subqueries) >= 2 else [retrieval_query]

        # Search song song nếu có nhiều sub-query
        if len(search_queries) == 1:
            out = self.vector.search(
                search_queries[0], law_id=law_id, top_k=top_k,
                min_rerank_score=min_rerank_score,
            )
            context = out.get("context", "")
            low_conf = bool(out.get("low_confidence", False))
        else:
            outs = [
                self.vector.search(
                    q, law_id=law_id, top_k=top_k,
                    min_rerank_score=min_rerank_score,
                )
                for q in search_queries
            ]
            merged: dict[str, dict[str, Any]] = {}
            low_conf = True
            for o in outs:
                low_conf = low_conf and bool(o.get("low_confidence", False))
                for r in o.get("results", []):
                    key = r.get("chunk_id") or r.get("article") or r.get("neo4j_id") or id(r)
                    cur = merged.get(key)
                    if cur is None or float(r.get("score") or 0.0) > float(cur.get("score") or 0.0):
                        merged[key] = r
            k = top_k or 8
            results = sorted(merged.values(), key=lambda r: float(r.get("score") or 0.0), reverse=True)[:k]
            context = format_context_for_llm(results)

        messages = build_rag_prompt(query, context)
        answer = self.llm.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=True,   # ← reasoning ON
            extra_payload={"top_p": 0.9, "repetition_penalty": 1.05},
        )

        return VectorAnswer(
            answer=answer,
            refined=refined,
            low_confidence=low_conf,
            elapsed=time.perf_counter() - start,
        )


# ══════════════════════════════════════════════════════════════════════
# Per-task runner
# ══════════════════════════════════════════════════════════════════════
def _write_header(f, task: TaskFile, total: int) -> None:
    f.write(f"# Vector reasoning — {task.law_title}\n\n")
    f.write(f"- Task: `{task.task}`\n")
    f.write(f"- Source: `{task.src.name}`\n")
    f.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("- Pipeline: Vector RAG only (Qdrant + reranker + LLM)\n")
    f.write("- **Reasoning (enable_thinking): ON**\n")
    if task.law_id:
        f.write(f"- Law filter: `{task.law_id}`\n")
    else:
        f.write(f"- Law filter: none (cross-law search)\n")
    f.write(f"- Total questions: {total}\n\n")


def _write_item(f, no: int, question: str, ans: VectorAnswer | None, err: str | None) -> None:
    f.write(f"## Câu {no}\n\n")
    f.write(f"**Question:**\n\n{question}\n\n")
    if ans is not None:
        f.write(f"- Elapsed: {ans.elapsed:.1f}s\n")
        f.write(f"- Low confidence: {ans.low_confidence}\n\n")
    f.write("**Answer:**\n\n")
    if err:
        f.write(f"> Error: `{err}`\n\n")
    else:
        f.write((ans.answer if ans else "[No answer]").strip())
        f.write("\n\n")


def _run_task(task: TaskFile, args: argparse.Namespace) -> tuple[TaskFile, int, int]:
    """Trả (task, n_ok, n_err)."""
    questions = parse_questions(task.src)
    if not questions:
        print(f"[{task.task}/{task.name}] không có câu hỏi nào — skip")
        return task, 0, 0
    if args.limit_per_file:
        questions = questions[: args.limit_per_file]

    service = VectorReasoningService(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        device=args.device,
        min_rerank_score=args.min_rerank_score,
        enable_refine=not args.no_refine,
    )

    task.out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_err = 0
    with task.out.open("w", encoding="utf-8", newline="\n") as f:
        _write_header(f, task, len(questions))
        for i, q in enumerate(questions, 1):
            tag = f"[{task.task}/{task.name} {i}/{len(questions)}]"
            print(f"{tag} run", flush=True)
            try:
                ans = service.answer(
                    q["question"],
                    law_id=task.law_id,
                    top_k=args.top_k,
                    min_rerank_score=args.min_rerank_score,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                )
                _write_item(f, i, q["question"], ans, None)
                n_ok += 1
            except Exception as ex:
                err = f"{type(ex).__name__}: {ex}"
                print(f"{tag} ERROR {err}", flush=True)
                _write_item(f, i, q["question"], None, err)
                n_err += 1
                if args.stop_on_error:
                    raise
            f.flush()
    print(f"[{task.task}/{task.name}] DONE → {task.out}  (ok={n_ok}, err={n_err})", flush=True)
    return task, n_ok, n_err


# ══════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Vector-only reasoning benchmark on claude_benchmark scenarios.")
    p.add_argument("--qdrant-host", default=DEFAULT_QDRANT_HOST)
    p.add_argument("--qdrant-port", type=int, default=DEFAULT_QDRANT_PORT)
    p.add_argument("--device", default=os.getenv("RAG_DEVICE", "gpu"))
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--min-rerank-score", type=float, default=0.30)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--no-refine", action="store_true")
    p.add_argument("--stop-on-error", action="store_true")
    p.add_argument("--max-workers", type=int, default=7,
                   help="Số worker song song (mặc định 7: 3+3+1).")
    p.add_argument("--limit-per-file", type=int, default=None,
                   help="Chỉ chạy N câu đầu mỗi file (smoke test).")
    return p


def main() -> int:
    args = build_parser().parse_args()
    tasks = discover_tasks()
    if not tasks:
        print("[error] không tìm thấy task nào trong", BASE_IN)
        return 1

    print(f"Phát hiện {len(tasks)} file để chạy (reasoning=ON):", flush=True)
    for t in tasks:
        print(f"  - [{t.task}] {t.src.name}  →  {t.out.relative_to(ROOT)}", flush=True)
    print(f"Concurrency: max {args.max_workers} workers song song.\n", flush=True)

    results: list[tuple[TaskFile, int, int]] = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = [pool.submit(_run_task, t, args) for t in tasks]
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as ex:
                print(f"[fatal] worker crashed: {type(ex).__name__}: {ex}", flush=True)

    print("\n=== Tổng kết ===", flush=True)
    total_ok = total_err = 0
    for t, ok, err in sorted(results, key=lambda r: (r[0].task, r[0].name)):
        total_ok += ok
        total_err += err
        print(f"  [{t.task}/{t.name}] ok={ok} err={err}  →  {t.out.relative_to(ROOT)}", flush=True)
    print(f"  TOTAL ok={total_ok} err={total_err}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
