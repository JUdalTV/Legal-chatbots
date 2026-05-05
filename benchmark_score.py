"""
benchmark_score.py — Chấm điểm benchmark: ground_truth vs model_answer.

Metrics:
  1. Citation Accuracy: tỷ lệ citations đúng (đã có sẵn trong file)
  2. Faithfulness: tỷ lệ câu trả lời được hỗ trợ bởi nguồn (đã có sẵn)
  3. ROUGE-L: overlap n-gram giữa ground_truth và model_answer
  4. Semantic Similarity: cosine similarity giữa embedding 2 câu
  5. Exact Match: ground_truth có nằm trong model_answer không
  6. Answer Relevance: LLM chấm điểm (optional)

Chạy:
  python benchmark_score.py
  python benchmark_score.py --no-llm        # bỏ qua LLM scoring
  python benchmark_score.py --no-embedding   # bỏ qua semantic similarity
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "backend" / ".env")
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════
# ROUGE-L (F1)
# ═══════════════════════════════════════════════════════════════════
def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _lcs_length(x: list[str], y: list[str]) -> int:
    m, n = len(x), len(y)
    if m == 0 or n == 0:
        return 0
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(curr[j - 1], prev[j])
        prev = curr
    return prev[n]


def rouge_l(reference: str, hypothesis: str) -> dict:
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    lcs = _lcs_length(ref_tokens, hyp_tokens)
    precision = lcs / len(hyp_tokens)
    recall = lcs / len(ref_tokens)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


# ═══════════════════════════════════════════════════════════════════
# Exact Match (ground_truth substring in model_answer)
# ═══════════════════════════════════════════════════════════════════
def exact_match(ground_truth: str, model_answer: str) -> float:
    gt_norm = re.sub(r"\s+", " ", ground_truth.strip().lower())
    ma_norm = re.sub(r"\s+", " ", model_answer.strip().lower())
    return 1.0 if gt_norm in ma_norm else 0.0


# ═══════════════════════════════════════════════════════════════════
# Semantic Similarity (cosine, dùng sentence-transformers)
# ═══════════════════════════════════════════════════════════════════
def semantic_similarity(gt: str, ma: str, model=None) -> float:
    if model is None:
        return -1.0  # skip
    emb = model.encode([gt, ma], normalize_embeddings=True)
    return float(emb[0] @ emb[1])


# ═══════════════════════════════════════════════════════════════════
# LLM-as-Judge (optional)
# ═══════════════════════════════════════════════════════════════════
_JUDGE_PROMPT = """Bạn là giám khảo chấm điểm câu trả lời pháp lý.

Cho:
- Câu hỏi: {question}
- Đáp án chuẩn (ground_truth): {ground_truth}
- Câu trả lời model: {model_answer}

Chấm điểm từ 0-10 theo tiêu chí:
- Đúng nội dung so với đáp án chuẩn (0-5 điểm)
- Đầy đủ thông tin (0-3 điểm)
- Không thêm thông tin sai (0-2 điểm)

Trả về CHỈ 1 số nguyên từ 0 đến 10, không giải thích."""


def llm_judge(question: str, ground_truth: str, model_answer: str, llm_client) -> int:
    if llm_client is None:
        return -1
    prompt = _JUDGE_PROMPT.format(
        question=question, ground_truth=ground_truth, model_answer=model_answer
    )
    try:
        resp = llm_client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=10,
        )
        m = re.search(r"\d+", resp.strip())
        return min(int(m.group(0)), 10) if m else -1
    except Exception:
        return -1


# ═══════════════════════════════════════════════════════════════════
# Main scoring
# ═══════════════════════════════════════════════════════════════════
def score_benchmark(
    data: dict,
    *,
    use_embedding: bool = True,
    use_llm: bool = False,
) -> dict:
    results = data.get("results") or data.get("questions", [])

    # Load embedding model
    embed_model = None
    if use_embedding:
        try:
            from sentence_transformers import SentenceTransformer
            print("[scoring] Loading embedding model...")
            embed_model = SentenceTransformer("AITeamVN/Vietnamese_Embedding")
            print("[scoring] Embedding model loaded.")
        except ImportError:
            print("[scoring] sentence-transformers not installed, skipping semantic similarity.")

    # Load LLM client
    llm_client = None
    if use_llm:
        try:
            sys.path.insert(0, str(Path(__file__).parent / "backend"))
            from backend.services.llm_client import LLMClient
            llm_client = LLMClient()
            print("[scoring] LLM client ready.")
        except Exception as e:
            print(f"[scoring] LLM client failed: {e}")

    scored = []
    for item in results:
        gt = item["ground_truth"]
        ma = item["model_answer"]
        q = item["question"]

        # ROUGE-L
        rl = rouge_l(gt, ma)

        # Exact match
        em = exact_match(gt, ma)

        # Semantic similarity
        sim = semantic_similarity(gt, ma, embed_model)

        # LLM judge
        llm_score = llm_judge(q, gt, ma, llm_client)

        # Existing scores from file (handle null)
        citations_score = item.get("citations_score") or 0.0
        faithfulness_score = item.get("faithfulness_score") or 0.0

        # Composite score (weighted average of available metrics)
        components = [
            (citations_score, 0.25),
            (faithfulness_score, 0.25),
            (rl["f1"], 0.25),
            (em, 0.10),
        ]
        if sim >= 0:
            components.append((sim, 0.15))
        else:
            # redistribute weight
            components = [
                (citations_score, 0.30),
                (faithfulness_score, 0.30),
                (rl["f1"], 0.25),
                (em, 0.15),
            ]

        composite = sum(s * w for s, w in components)

        scored.append({
            "id": item["id"],
            "difficulty": item["difficulty"],
            "category": item["category"],
            "rouge_l": rl,
            "exact_match": em,
            "semantic_similarity": round(sim, 4) if sim >= 0 else None,
            "citations_score": citations_score,
            "faithfulness_score": faithfulness_score,
            "llm_judge": llm_score if llm_score >= 0 else None,
            "composite_score": round(composite, 4),
        })

    return {"scores": scored, "summary": _summarize(scored)}


def _summarize(scored: list[dict]) -> dict:
    n = len(scored)
    if n == 0:
        return {}

    avg = lambda key: round(sum(s[key] for s in scored) / n, 4)
    avg_rouge = round(sum(s["rouge_l"]["f1"] for s in scored) / n, 4)

    by_diff = {}
    for diff in ("easy", "medium", "hard"):
        subset = [s for s in scored if s["difficulty"] == diff]
        if subset:
            by_diff[diff] = {
                "count": len(subset),
                "avg_composite": round(sum(s["composite_score"] for s in subset) / len(subset), 4),
                "avg_rouge_l_f1": round(sum(s["rouge_l"]["f1"] for s in subset) / len(subset), 4),
                "avg_citations": round(sum(s["citations_score"] for s in subset) / len(subset), 4),
                "avg_faithfulness": round(sum(s["faithfulness_score"] for s in subset) / len(subset), 4),
            }

    sim_scores = [s["semantic_similarity"] for s in scored if s["semantic_similarity"] is not None]

    return {
        "total": n,
        "avg_composite": avg("composite_score"),
        "avg_rouge_l_f1": avg_rouge,
        "avg_exact_match": avg("exact_match"),
        "avg_citations": avg("citations_score"),
        "avg_faithfulness": avg("faithfulness_score"),
        "avg_semantic_similarity": round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else None,
        "by_difficulty": by_diff,
    }


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(description="Benchmark scoring: ground_truth vs model_answer")
    p.add_argument("file", nargs="?", default=None, help="Path to benchmark JSON (or enter interactively)")
    p.add_argument("--no-embedding", action="store_true", help="Skip semantic similarity")
    p.add_argument("--no-llm", action="store_true", help="Skip LLM-as-judge")
    p.add_argument("--output", default=None, help="Output JSON file (default: print to stdout)")
    args = p.parse_args()

    if args.file:
        file_path = Path(args.file)
    else:
        raw = input("Nhập đường dẫn file benchmark JSON: ").strip().strip('"')
        file_path = Path(raw)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[scoring] Loaded {len(data.get('results') or data.get('questions', []))} questions from {file_path.name}")
    print(f"[scoring] Embedding: {'ON' if not args.no_embedding else 'OFF'}")
    print(f"[scoring] LLM Judge: {'ON' if not args.no_llm else 'OFF'}")
    print()

    result = score_benchmark(
        data,
        use_embedding=not args.no_embedding,
        use_llm=not args.no_llm,
    )

    # Print summary
    summary = result["summary"]
    print(f"\n{'='*60}")
    print(f"  BENCHMARK RESULTS  ({summary['total']} questions)")
    print(f"{'='*60}")
    print(f"  Composite Score:      {summary['avg_composite']:.4f}")
    print(f"  ROUGE-L F1:           {summary['avg_rouge_l_f1']:.4f}")
    print(f"  Exact Match:          {summary['avg_exact_match']:.4f}")
    print(f"  Citations Accuracy:   {summary['avg_citations']:.4f}")
    print(f"  Faithfulness:         {summary['avg_faithfulness']:.4f}")
    if summary.get("avg_semantic_similarity") is not None:
        print(f"  Semantic Similarity:  {summary['avg_semantic_similarity']:.4f}")
    print()

    print(f"  {'Difficulty':<12} {'Count':<7} {'Composite':<11} {'ROUGE-L':<9} {'Citations':<11} {'Faith.'}")
    print(f"  {'-'*60}")
    for diff, stats in summary.get("by_difficulty", {}).items():
        print(f"  {diff:<12} {stats['count']:<7} {stats['avg_composite']:<11.4f} "
              f"{stats['avg_rouge_l_f1']:<9.4f} {stats['avg_citations']:<11.4f} {stats['avg_faithfulness']:.4f}")

    # Per-question detail
    print(f"\n  {'ID':<12} {'Diff':<8} {'Composite':<11} {'ROUGE-L':<9} {'Cite':<7} {'Faith':<7} {'EM'}")
    print(f"  {'-'*65}")
    for s in result["scores"]:
        print(f"  {s['id']:<12} {s['difficulty']:<8} {s['composite_score']:<11.4f} "
              f"{s['rouge_l']['f1']:<9.4f} {s['citations_score']:<7.2f} "
              f"{s['faithfulness_score']:<7.2f} {s['exact_match']:.0f}")

    # Save output
    if args.output:
        out_path = Path(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[scoring] Results saved to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
