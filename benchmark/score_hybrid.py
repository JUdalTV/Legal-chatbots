"""
score_benchmark.py — Tính điểm benchmark cho 3 luật dựa trên ground truth.

Đọc 3 file JSON (benchmark_luat*.json), với mỗi câu hỏi tính 3 metric so với
groundtruth + reference, tổng hợp ra file Markdown.

Metrics:
- semantic_score: cosine similarity giữa model_answer & ground_truth
  (embedding truro7/vn-law-embedding, đã normalize → dot product).
- citation_score: tỷ lệ điều khoản trong `reference` xuất hiện trong model_answer
  (recall trên các cặp (Điều, khoản) bắt buộc).
- keyword_score: F1 trên content tokens (underthesea tokenize, lọc stopword).

Tổng điểm (mặc định): 0.5 * semantic + 0.3 * citation + 0.2 * keyword.

Chạy:
    python benchmark/score_benchmark.py
    python benchmark/score_benchmark.py --output benchmark/report.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DATASETS: list[dict] = [
    {
        "key": "anm",
        "title": "Luật An ninh mạng 116/2025/QH15",
        "path": ROOT / "benchmark" / "benchmark_luatAnNinhMang.json",
    },
    {
        "key": "vt",
        "title": "Luật Viễn thông 24/2023/QH15",
        "path": ROOT / "benchmark" / "benchmark_luatVienThong.json",
    },
    {
        "key": "cntt",
        "title": "Luật Công nghệ thông tin 65/VBHN-VPQH",
        "path": ROOT / "benchmark" / "benchmark_luatCNTT.json",
    },
]


# ══════════════════════════════════════════════════════════════════════
# Citation parsing
# ══════════════════════════════════════════════════════════════════════
# Bắt cụm "Điều X" với (optional) khoản. Diacritic-insensitive qua
# normalize_for_match(). Hỗ trợ 2 thứ tự:
#   (A) "Điều N, khoản M"     — model viết theo style học thuật.
#   (B) "Khoản M Điều N"      — model thường viết kiểu "Khoản 1 Điều 29".
_RX_ARTICLE_FIRST = re.compile(
    r"dieu\s*(\d+)"
    r"(?:[^a-z0-9]{0,40}?khoan\s*([\d,\s]*\d))?",
    re.IGNORECASE,
)
_RX_CLAUSE_FIRST = re.compile(
    r"khoan\s*([\d,\s]*\d)"
    r"[^a-z0-9]{0,20}?dieu\s*(\d+)",
    re.IGNORECASE,
)


def normalize_for_match(text: str) -> str:
    """Hạ lowercase + bỏ dấu để regex match không phụ thuộc dấu/case."""
    if not text:
        return ""
    # NFD tách dấu, rồi lọc combining marks
    decomposed = unicodedata.normalize("NFD", text.lower())
    no_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    # giữ "đ" → "d" để regex đơn giản, nhưng "đ" trong "điểm" đã được normalize
    no_accents = no_accents.replace("đ", "d")
    return no_accents


def _split_clauses(raw: str | None) -> list[str]:
    """'1 và 2' → ['1','2']. '1, 2 và 3' → ['1','2','3']. '1' → ['1']."""
    if not raw:
        return [""]
    parts = re.split(r"[,\s]*(?:va|,)[,\s]*|\s+", raw.strip())
    out = [p for p in parts if p and p.isdigit()]
    return out or [""]


def extract_citations(text: str) -> set[tuple[str, str]]:
    """
    Extract {(article_no, clause_no)} từ text. clause_no='' nếu chỉ có Điều.
    Hỗ trợ cả "Điều N, khoản M" và "Khoản M Điều N".
    """
    norm = normalize_for_match(text)
    cites: set[tuple[str, str]] = set()

    # Order A: Điều N [, khoản M ...]
    for m in _RX_ARTICLE_FIRST.finditer(norm):
        art = m.group(1)
        for c in _split_clauses(m.group(2)):
            cites.add((art, c))

    # Order B: Khoản M Điều N
    for m in _RX_CLAUSE_FIRST.finditer(norm):
        art = m.group(2)
        for c in _split_clauses(m.group(1)):
            cites.add((art, c))

    return cites


def citation_recall(reference: str, model_answer: str) -> tuple[float, set, set]:
    """
    Recall: bao nhiêu cặp (Điều, khoản) trong reference xuất hiện trong model_answer?
    Nếu reference chỉ có Điều (không khoản) → khớp khi model nhắc tới Điều đó.
    """
    expected_raw = extract_citations(reference)
    if not expected_raw:
        return 1.0, set(), set()  # không có expected → coi như đạt
    got = extract_citations(model_answer)

    # Tập Điều mà model có nhắc tới (bất kể khoản nào)
    got_articles = {a for (a, _) in got}

    hits = set()
    for (art, clause) in expected_raw:
        if clause == "":
            # reference chỉ ghi "Điều X" — chỉ cần model nhắc Điều X là đủ
            if art in got_articles:
                hits.add((art, clause))
        else:
            # cần khớp cả Điều + Khoản
            if (art, clause) in got:
                hits.add((art, clause))

    score = len(hits) / len(expected_raw)
    return score, expected_raw, hits


# ══════════════════════════════════════════════════════════════════════
# Keyword overlap (F1 trên content tokens)
# ══════════════════════════════════════════════════════════════════════
# Stopwords tiếng Việt + token format hóa của underthesea (từ ghép nối '_').
_VI_STOPWORDS = frozenset({
    "và", "hoặc", "của", "là", "có", "không", "được", "trong", "khi", "với",
    "theo", "tại", "cho", "từ", "đến", "này", "đó", "các", "những", "một",
    "bị", "đã", "sẽ", "đang", "vẫn", "cũng", "thì", "mà", "nhưng", "nên",
    "nếu", "vì", "do", "bởi", "ra", "vào", "lên", "xuống", "qua", "về",
    "trên", "dưới", "ngoài", "giữa", "sau", "trước", "bằng", "đối với",
    "phải", "cần", "hay", "rằng", "ai", "gì", "nào", "đâu", "sao",
    "tôi", "bạn", "họ", "chúng", "mình",
    "the", "a", "an", "is", "are", "of", "to", "in", "and", "or",
})


def _strip_markdown(text: str) -> str:
    """Bỏ ký hiệu markdown thông dụng (*, **, _, #, `, >, [, ]) cho keyword count."""
    if not text:
        return ""
    # bỏ code/inline code, headings, bold/italic, blockquote markers, links
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"[#>*_~\[\]()]", " ", text)
    return text


def _tokenize_content(text: str) -> list[str]:
    """
    Tokenize tiếng Việt bằng underthesea (giữ từ ghép '_'). Lọc stopwords +
    token <2 ký tự + token thuần số ngắn.
    """
    from underthesea import word_tokenize  # lazy import

    text = _strip_markdown(text)
    raw = word_tokenize(text.lower(), format="text").split()
    toks: list[str] = []
    for t in raw:
        t = re.sub(r"[^\w\d_]+", "", t)
        if not t or len(t) < 2:
            continue
        if t in _VI_STOPWORDS:
            continue
        if t.replace("_", "").isdigit() and len(t) < 2:
            continue
        toks.append(t)
    return toks


def keyword_recall(reference_text: str, model_text: str) -> float:
    """
    Recall trên content token giữa ground_truth và model_answer.
    Why recall (chứ không phải F1): model trả lời pháp lý thường dài hơn GT
    (kèm "Căn cứ pháp lý", các khoản phụ liên quan, lưu ý phân biệt khái niệm).
    F1 phạt verbose nặng dù câu trả lời đúng → mất điểm oan. Recall đo "bao
    nhiêu keyword GT được model đề cập" — phù hợp domain pháp lý.
    """
    gt = set(_tokenize_content(reference_text))
    if not gt:
        return 0.0
    md = set(_tokenize_content(model_text))
    if not md:
        return 0.0
    common = gt & md
    return len(common) / len(gt)


# ══════════════════════════════════════════════════════════════════════
# Semantic similarity (cosine qua embedder)
# ══════════════════════════════════════════════════════════════════════
def compute_semantic_scores(
    pairs: list[tuple[str, str]],
    *,
    device: str = "gpu",
) -> list[float]:
    """
    pairs: list of (model_answer, ground_truth). Trả về list cosine similarity.
    Vector đã normalize → dot product = cosine.
    """
    if not pairs:
        return []

    from backend.vector_rag.embedder import Embedder

    emb = Embedder(device=device)
    flat: list[str] = []
    for a, b in pairs:
        flat.append(a or "")
        flat.append(b or "")
    vecs = emb.encode(flat, show_progress=True)

    scores: list[float] = []
    for i in range(0, len(vecs), 2):
        va = vecs[i]
        vb = vecs[i + 1]
        # đã normalize, nhưng phòng trường hợp 0-vector
        dot = sum(x * y for x, y in zip(va, vb))
        # clamp về [0, 1]: cosine có thể âm với văn bản đối lập → coi như 0
        scores.append(max(0.0, min(1.0, dot)))
    return scores


# ══════════════════════════════════════════════════════════════════════
# Aggregation
# ══════════════════════════════════════════════════════════════════════
WEIGHTS = {"semantic": 0.5, "citation": 0.3, "keyword": 0.2}


def overall(row: dict) -> float:
    return (
        WEIGHTS["semantic"] * row["semantic"]
        + WEIGHTS["citation"] * row["citation"]
        + WEIGHTS["keyword"] * row["keyword"]
    )


def mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def grade(score: float) -> str:
    if score >= 0.85:
        return "🟢 Xuất sắc"
    if score >= 0.70:
        return "🟢 Tốt"
    if score >= 0.55:
        return "🟡 Khá"
    if score >= 0.40:
        return "🟠 Trung bình"
    return "🔴 Yếu"


# ══════════════════════════════════════════════════════════════════════
# Report rendering
# ══════════════════════════════════════════════════════════════════════
def render_md(per_law: list[dict], output: Path) -> None:
    lines: list[str] = []
    lines.append("# Benchmark Report — Hybrid Legal RAG\n")
    lines.append(f"- Trọng số: semantic **{WEIGHTS['semantic']:.0%}** · "
                 f"citation **{WEIGHTS['citation']:.0%}** · "
                 f"keyword **{WEIGHTS['keyword']:.0%}**")
    lines.append("- Semantic: cosine similarity (`truro7/vn-law-embedding`)")
    lines.append("- Citation: recall trên (Điều, khoản) trong `reference`")
    lines.append("- Keyword: recall trên content tokens (underthesea, sau khi lọc stopword)\n")

    # Overall summary
    all_rows: list[dict] = []
    for law in per_law:
        all_rows.extend(law["rows"])

    lines.append("## Tổng quan\n")
    lines.append("| Luật | Câu | Semantic | Citation | Keyword | **Tổng** | Đánh giá |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for law in per_law:
        rows = law["rows"]
        sem = mean(r["semantic"] for r in rows)
        cit = mean(r["citation"] for r in rows)
        kw  = mean(r["keyword"] for r in rows)
        ov  = mean(overall(r) for r in rows)
        lines.append(
            f"| {law['title']} | {len(rows)} | {sem:.3f} | {cit:.3f} | "
            f"{kw:.3f} | **{ov:.3f}** | {grade(ov)} |"
        )

    sem_all = mean(r["semantic"] for r in all_rows)
    cit_all = mean(r["citation"] for r in all_rows)
    kw_all  = mean(r["keyword"] for r in all_rows)
    ov_all  = mean(overall(r) for r in all_rows)
    lines.append(
        f"| **TOÀN BỘ** | **{len(all_rows)}** | **{sem_all:.3f}** | "
        f"**{cit_all:.3f}** | **{kw_all:.3f}** | **{ov_all:.3f}** | "
        f"**{grade(ov_all)}** |"
    )

    # Per-difficulty breakdown (toàn bộ)
    lines.append("\n## Phân tích theo độ khó (toàn bộ)\n")
    lines.append("| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    by_diff: dict[str, list[dict]] = defaultdict(list)
    for r in all_rows:
        by_diff[r["difficulty"]].append(r)
    for diff in ("easy", "medium", "hard"):
        rows = by_diff.get(diff, [])
        if not rows:
            continue
        lines.append(
            f"| {diff} | {len(rows)} | "
            f"{mean(r['semantic'] for r in rows):.3f} | "
            f"{mean(r['citation'] for r in rows):.3f} | "
            f"{mean(r['keyword'] for r in rows):.3f} | "
            f"**{mean(overall(r) for r in rows):.3f}** |"
        )

    # Per-law detail
    for law in per_law:
        lines.append(f"\n## {law['title']}\n")

        # By difficulty within this law
        per_diff: dict[str, list[dict]] = defaultdict(list)
        for r in law["rows"]:
            per_diff[r["difficulty"]].append(r)
        lines.append("### Tổng hợp theo độ khó\n")
        lines.append("| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for diff in ("easy", "medium", "hard"):
            rows = per_diff.get(diff, [])
            if not rows:
                continue
            lines.append(
                f"| {diff} | {len(rows)} | "
                f"{mean(r['semantic'] for r in rows):.3f} | "
                f"{mean(r['citation'] for r in rows):.3f} | "
                f"{mean(r['keyword'] for r in rows):.3f} | "
                f"**{mean(overall(r) for r in rows):.3f}** |"
            )

        # Detail per question
        lines.append("\n### Chi tiết từng câu\n")
        lines.append("| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |")
        lines.append("|---|---|---|---:|---:|---:|---:|")
        for r in law["rows"]:
            ref = r["reference"].replace("|", "\\|")
            lines.append(
                f"| {r['id']} | {r['difficulty']} | {ref} | "
                f"{r['semantic']:.3f} | {r['citation']:.3f} | "
                f"{r['keyword']:.3f} | **{overall(r):.3f}** |"
            )

        # Bottom 5 (cần xem lại)
        worst = sorted(law["rows"], key=overall)[:5]
        if worst:
            lines.append("\n### 5 câu điểm thấp nhất (cần review)\n")
            for r in worst:
                lines.append(
                    f"- **{r['id']}** ({r['difficulty']}) — tổng "
                    f"`{overall(r):.3f}` · sem `{r['semantic']:.3f}` · "
                    f"cit `{r['citation']:.3f}` · kw `{r['keyword']:.3f}`"
                )
                lines.append(f"  > Câu hỏi: {r['question'][:200]}")
                if r["expected_cites"] and not r["hit_cites"].issuperset(r["expected_cites"]):
                    missing = r["expected_cites"] - r["hit_cites"]
                    pretty = ", ".join(
                        f"Điều {a}" + (f" khoản {c}" if c else "")
                        for (a, c) in sorted(missing)
                    )
                    lines.append(f"  > Citation thiếu: {pretty}")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Directory containing benchmark_luat*.json files. Defaults to benchmark/.",
    )
    parser.add_argument(
        "--output", "-o",
        default=str(ROOT / "benchmark" / "benchmark_score_report.md"),
        help="File MD output",
    )
    parser.add_argument("--device", default="gpu", help="gpu | cpu cho embedder")
    args = parser.parse_args()

    # Load datasets
    per_law: list[dict] = []
    for ds in DATASETS:
        path = (
            Path(args.input_dir) / Path(ds["path"]).name
            if args.input_dir else Path(ds["path"])
        )
        if not path.exists():
            print(f"[warn] không tìm thấy {path}, bỏ qua")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        # CNTT dùng key "questions", còn lại dùng "results"
        rows = data.get("results") or data.get("questions") or []
        per_law.append({"title": ds["title"], "key": ds["key"], "results": rows})

    if not per_law:
        print("[error] không có dataset nào để chấm.")
        return 1

    # Gom tất cả pairs để embed 1 lần (tận dụng batch GPU)
    all_pairs: list[tuple[str, str]] = []
    index_map: list[tuple[int, int]] = []  # (law_idx, row_idx)
    for li, law in enumerate(per_law):
        for ri, r in enumerate(law["results"]):
            all_pairs.append((r.get("model_answer", ""), r.get("ground_truth", "")))
            index_map.append((li, ri))

    print(f"[info] Đang tính semantic similarity cho {len(all_pairs)} cặp…")
    sem_scores = compute_semantic_scores(all_pairs, device=args.device)

    # Compute citation + keyword + assemble rows
    for law in per_law:
        law["rows"] = []

    print(f"[info] Đang tính citation + keyword…")
    for (li, ri), sem in zip(index_map, sem_scores):
        law = per_law[li]
        r = law["results"][ri]
        cit_score, expected, hits = citation_recall(
            r.get("reference", ""), r.get("model_answer", ""),
        )
        kw_score = keyword_recall(
            r.get("ground_truth", ""), r.get("model_answer", ""),
        )
        law["rows"].append({
            "id": r.get("id", ""),
            "difficulty": r.get("difficulty", ""),
            "question": r.get("question", ""),
            "reference": r.get("reference", ""),
            "semantic": sem,
            "citation": cit_score,
            "keyword": kw_score,
            "expected_cites": expected,
            "hit_cites": hits,
        })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    render_md(per_law, output)

    # Console summary
    print("\n=== Tổng kết ===")
    for law in per_law:
        rows = law["rows"]
        ov = mean(overall(r) for r in rows)
        print(f"  {law['title']:55s}  N={len(rows):3d}  tổng={ov:.3f}")
    all_rows = [r for law in per_law for r in law["rows"]]
    ov_all = mean(overall(r) for r in all_rows)
    print(f"  {'TOÀN BỘ':55s}  N={len(all_rows):3d}  tổng={ov_all:.3f}")
    print(f"\n[done] Báo cáo: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
