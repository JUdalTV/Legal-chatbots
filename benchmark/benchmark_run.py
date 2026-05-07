"""
benchmark_run.py — Chạy tất cả câu hỏi trong benchmark qua Hybrid RAG,
ghi câu trả lời model mới vào file JSON.

Chạy:
  python benchmark_run.py benchmark_luatAnNinhMang.json --law-id LuatAnNinhMang2025
  python benchmark_run.py benchmark_luatVienThong.json --law-id LuatVienThong2023
  python benchmark_run.py benchmark_luatCNTT --law-id LuatCNTT2025

Output: file gốc được cập nhật model_answer mới (backup file cũ thành .bak)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass

from backend.services.hybrid_rag_service import HybridRAGService


def main():
    p = argparse.ArgumentParser(description="Run benchmark questions through Hybrid RAG")
    p.add_argument("file", help="Path to benchmark JSON")
    p.add_argument("--law-id", required=True, help="Law ID filter (e.g. LuatAnNinhMang2025)")
    p.add_argument("--output", default=None, help="Output file (default: overwrite input with backup)")
    p.add_argument("--device", default="gpu")
    p.add_argument("--start", type=int, default=0, help="Start from question index (0-based)")
    args = p.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results") or data.get("questions", [])
    print(f"[benchmark_run] Loaded {len(results)} questions from {file_path.name}")
    print(f"[benchmark_run] law_id={args.law_id}, device={args.device}")
    print(f"[benchmark_run] Starting from index {args.start}")
    print()

    # Init service
    print("[benchmark_run] Initializing Hybrid RAG service...")
    service = HybridRAGService(device=args.device)
    print("[benchmark_run] Service ready.\n")

    try:
        for i, item in enumerate(results):
            if i < args.start:
                continue

            qid = item.get("id", f"Q{i+1:03d}")
            question = item["question"]

            print(f"[{i+1}/{len(results)}] {qid}: {question[:80]}...")
            t0 = time.time()

            try:
                result = service.answer(question, law_id=args.law_id)
                item["model_answer"] = result.answer
                elapsed = time.time() - t0
                print(f"  -> OK ({elapsed:.1f}s, {len(result.answer)} chars)")
            except Exception as ex:
                print(f"  -> ERROR: {ex}")
                item["model_answer"] = f"[ERROR] {ex}"

            # Save progress after each question
            out_path = Path(args.output) if args.output else file_path
            if not args.output:
                # Backup only once
                bak = file_path.with_suffix(file_path.suffix + ".bak")
                if not bak.exists():
                    shutil.copy2(file_path, bak)
                    print(f"  [backup] {bak.name}")

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    finally:
        service.close()

    print(f"\n[benchmark_run] Done! Results saved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
