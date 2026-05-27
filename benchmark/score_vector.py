"""
Score Vector-only RAG answers from Markdown files.

Inputs:
- benchmark/vector_benchmark/legal_qa_answers_vector_anm.md
- benchmark/vector_benchmark/legal_qa_answers_vector_vt.md
- benchmark/vector_benchmark/legal_qa_answers_vector_cntt.md
- benchmark/vector_benchmark/Dap_an_90_cau_hoi_groundtruth.md

The question set is matched by law + question number, so this script does not
depend on the deleted benchmark JSON files.

Run:
    python benchmark/score_vector.py
    python benchmark/score_vector.py --device cpu
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


from benchmark.score_hybrid import (  # noqa: E402
    WEIGHTS,
    citation_recall,
    compute_semantic_scores,
    grade,
    keyword_recall,
    mean,
    overall,
)


LAW_SPECS = [
    {
        "key": "anm",
        "title": "Luật An ninh mạng 116/2025/QH15",
        "vector_file": "legal_qa_answers_vector_anm.md",
    },
    {
        "key": "vt",
        "title": "Luật Viễn thông 24/2023/QH15",
        "vector_file": "legal_qa_answers_vector_vt.md",
    },
    {
        "key": "cntt",
        "title": "Luật Công nghệ thông tin 65/VBHN-VPQH",
        "vector_file": "legal_qa_answers_vector_cntt.md",
    },
]

DEFAULT_GROUNDTRUTH_CANDIDATES = [
    ROOT / "benchmark" / "vector_benchmark" / "Dap_an_90_cau_hoi_groundtruth.md",
    ROOT / "benchmark" / "hybrid_metric_benchmark" / "Dap_an_90_cau_hoi_groundtruth.md",
    ROOT / "benchmark" / "metric_benchmark" / "Dap_an_90_cau_hoi_groundtruth.md",
]

_RX_VECTOR_HEAD = re.compile(r"^####\s+(\d+)\.\s+(.+?)\s*$")
_RX_GT_HEAD_NORM = re.compile(r"^####\s+cau\s+(\d+)\.\s*")


def fold_text(text: str) -> str:
    """Lowercase and strip Vietnamese accents for tolerant heading matching."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    no_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return no_accents.replace("đ", "d")


def project_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def resolve_groundtruth(raw: str | None) -> Path:
    if raw:
        return project_path(raw)
    for path in DEFAULT_GROUNDTRUTH_CANDIDATES:
        if path.exists():
            return path
    return DEFAULT_GROUNDTRUTH_CANDIDATES[0]


def law_key_from_heading(line: str) -> str | None:
    norm = fold_text(line)
    if "an ninh mang" in norm:
        return "anm"
    if "vien thong" in norm:
        return "vt"
    if "cntt" in norm or "cong nghe thong tin" in norm:
        return "cntt"
    return None


def difficulty_for_number(number: int) -> str:
    if number <= 10:
        return "easy"
    if number <= 20:
        return "medium"
    return "hard"


def difficulty_from_heading(line: str) -> str | None:
    norm = fold_text(line)
    if "easy" in norm:
        return "easy"
    if "medium" in norm:
        return "medium"
    if "hard" in norm:
        return "hard"
    return None


def strip_id(raw: str) -> str:
    """Support both 'easy_01' and old 'easy_01 / Q001' headings."""
    return raw.split("/", 1)[0].strip()


def split_after_colon(line: str) -> str:
    return line.split(":", 1)[1].strip() if ":" in line else ""


def parse_question_from_groundtruth_heading(line: str) -> str:
    if "." not in line:
        return ""
    return line.split(".", 1)[1].strip()


def parse_groundtruth_md(path: Path) -> dict[tuple[str, int], dict]:
    """Parse groundtruth MD into {(law_key, number): {question, ground_truth}}."""
    if not path.exists():
        raise FileNotFoundError(path)

    items: dict[tuple[str, int], dict] = {}
    current_law: str | None = None
    current_number: int | None = None
    current_question = ""
    answer_buf: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_question, answer_buf
        if current_law and current_number is not None:
            items[(current_law, current_number)] = {
                "question": current_question.strip(),
                "ground_truth": "\n".join(answer_buf).strip(),
            }
        current_number = None
        current_question = ""
        answer_buf = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        norm = fold_text(stripped)

        if stripped.startswith("## "):
            flush()
            current_law = law_key_from_heading(stripped)
            continue

        if stripped.startswith("### "):
            flush()
            continue

        match = _RX_GT_HEAD_NORM.match(norm)
        if match and current_law:
            flush()
            current_number = int(match.group(1))
            current_question = parse_question_from_groundtruth_heading(stripped)
            continue

        if current_law and current_number is not None:
            if stripped == "---":
                continue
            answer_buf.append(line)

    flush()
    return items


def parse_vector_md(path: Path) -> list[dict]:
    """Parse a vector benchmark answer MD into row dictionaries."""
    if not path.exists():
        raise FileNotFoundError(path)

    rows: list[dict] = []
    current: dict | None = None
    current_difficulty: str | None = None
    section: str | None = None
    question_buf: list[str] = []
    answer_buf: list[str] = []

    def flush() -> None:
        nonlocal current, section, question_buf, answer_buf
        if current is not None:
            number = int(current["number"])
            current["difficulty"] = current.get("difficulty") or difficulty_for_number(number)
            current["question"] = "\n".join(question_buf).strip()
            current["model_answer"] = "\n".join(answer_buf).strip()
            rows.append(current)
        current = None
        section = None
        question_buf = []
        answer_buf = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        norm = fold_text(stripped)

        head = _RX_VECTOR_HEAD.match(stripped)
        if head:
            flush()
            number = int(head.group(1))
            current = {
                "number": number,
                "id": strip_id(head.group(2)),
                "difficulty": current_difficulty or difficulty_for_number(number),
                "reference": "",
                "question": "",
                "model_answer": "",
            }
            continue

        if stripped.startswith("### "):
            flush()
            current_difficulty = difficulty_from_heading(stripped) or current_difficulty
            continue

        if current is None:
            continue

        if norm.startswith("- expected reference:") or norm.startswith("- can cu ky vong:"):
            current["reference"] = split_after_colon(stripped)
            continue

        if norm.startswith("**question:**") or norm.startswith("**cau hoi:**"):
            section = "question"
            rest = split_after_colon(stripped)
            if rest:
                question_buf.append(rest)
            continue

        if norm.startswith("**answer:**") or norm.startswith("**tra loi:**"):
            section = "answer"
            rest = split_after_colon(stripped)
            if rest:
                answer_buf.append(rest)
            continue

        if section == "question":
            question_buf.append(line)
        elif section == "answer":
            answer_buf.append(line)

    flush()
    return sorted(rows, key=lambda row: row["number"])


def collect_rows(vector_dir: Path, groundtruth_path: Path) -> list[dict]:
    groundtruth = parse_groundtruth_md(groundtruth_path)
    rows: list[dict] = []

    for spec in LAW_SPECS:
        vector_path = vector_dir / spec["vector_file"]
        vector_rows = parse_vector_md(vector_path)
        if len(vector_rows) != 30:
            print(f"[warn] {spec['key']}: expected 30 vector rows, got {len(vector_rows)}")

        missing_gt: list[int] = []
        missing_answers: list[int] = []
        for item in vector_rows:
            gt = groundtruth.get((spec["key"], item["number"]), {})
            if not gt:
                missing_gt.append(item["number"])
            if not item.get("model_answer"):
                missing_answers.append(item["number"])

            rows.append(
                {
                    "law_key": spec["key"],
                    "law_title": spec["title"],
                    "number": item["number"],
                    "id": item["id"],
                    "difficulty": item.get("difficulty") or difficulty_for_number(item["number"]),
                    "reference": item.get("reference") or gt.get("ground_truth", ""),
                    "question": item.get("question") or gt.get("question", ""),
                    "ground_truth": gt.get("ground_truth", ""),
                    "model_answer": item.get("model_answer", ""),
                }
            )

        if missing_gt:
            print(f"[warn] {spec['key']}: missing groundtruth for questions {missing_gt[:10]}")
        if missing_answers:
            print(f"[warn] {spec['key']}: missing vector answers for questions {missing_answers[:10]}")

    return rows


def score_rows(rows: list[dict], *, device: str, semantic: bool = True) -> None:
    if semantic:
        pairs = [(r["model_answer"] or "", r["ground_truth"] or "") for r in rows]
        print(f"[info] Computing semantic similarity for {len(pairs)} pairs...")
        semantic_scores = compute_semantic_scores(pairs, device=device)
    else:
        print("[info] Semantic similarity disabled by --no-semantic.")
        semantic_scores = [0.0] * len(rows)

    print("[info] Computing citation + keyword scores...")
    for row, sem in zip(rows, semantic_scores):
        citation, expected, hits = citation_recall(row["reference"], row["model_answer"])
        keyword = safe_keyword_recall(row["ground_truth"], row["model_answer"])
        row["semantic"] = sem
        row["citation"] = citation
        row["keyword"] = keyword
        row["expected_cites"] = expected
        row["hit_cites"] = hits


def escape_cell(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", "<br>")


_FALLBACK_STOPWORDS = {
    "va",
    "hoac",
    "cua",
    "la",
    "co",
    "khong",
    "duoc",
    "trong",
    "khi",
    "voi",
    "theo",
    "tai",
    "cho",
    "tu",
    "den",
    "nay",
    "do",
    "cac",
    "nhung",
    "mot",
    "bi",
    "da",
    "se",
    "dang",
    "thi",
    "ma",
    "neu",
    "vi",
    "boi",
    "ra",
    "vao",
    "ve",
    "tren",
    "duoi",
    "ngoai",
    "sau",
    "truoc",
    "bang",
    "phai",
    "can",
    "hay",
    "rang",
    "gi",
    "nao",
    "dau",
    "sao",
}
_WARNED_KEYWORD_FALLBACK = False


def fallback_keyword_recall(reference_text: str, model_text: str) -> float:
    def tokenize(text: str) -> set[str]:
        text = re.sub(r"```[\s\S]*?```", " ", text or "")
        text = re.sub(r"`[^`]*`", " ", text)
        tokens = re.findall(r"[a-z0-9_]+", fold_text(text))
        return {
            tok
            for tok in tokens
            if len(tok) > 1 and tok not in _FALLBACK_STOPWORDS and not (tok.isdigit() and len(tok) < 2)
        }

    expected = tokenize(reference_text)
    if not expected:
        return 0.0
    got = tokenize(model_text)
    if not got:
        return 0.0
    return len(expected & got) / len(expected)


def safe_keyword_recall(reference_text: str, model_text: str) -> float:
    global _WARNED_KEYWORD_FALLBACK
    try:
        return keyword_recall(reference_text, model_text)
    except ModuleNotFoundError as exc:
        if exc.name != "underthesea":
            raise
        if not _WARNED_KEYWORD_FALLBACK:
            print("[warn] underthesea is not installed; using regex fallback for keyword score.")
            _WARNED_KEYWORD_FALLBACK = True
        return fallback_keyword_recall(reference_text, model_text)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def append_summary_table(lines: list[str], rows: list[dict]) -> None:
    lines.append("| Scope | Questions | Semantic | Citation | Keyword | Overall | Grade |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    by_law: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_law[row["law_key"]].append(row)

    for spec in LAW_SPECS:
        law_rows = by_law.get(spec["key"], [])
        if not law_rows:
            continue
        sem = mean(row["semantic"] for row in law_rows)
        cit = mean(row["citation"] for row in law_rows)
        kw = mean(row["keyword"] for row in law_rows)
        ov = mean(overall(row) for row in law_rows)
        lines.append(
            f"| {escape_cell(spec['title'])} | {len(law_rows)} | "
            f"{sem:.3f} | {cit:.3f} | {kw:.3f} | **{ov:.3f}** | {grade(ov)} |"
        )

    sem_all = mean(row["semantic"] for row in rows)
    cit_all = mean(row["citation"] for row in rows)
    kw_all = mean(row["keyword"] for row in rows)
    ov_all = mean(overall(row) for row in rows)
    lines.append(
        f"| **ALL** | **{len(rows)}** | **{sem_all:.3f}** | **{cit_all:.3f}** | "
        f"**{kw_all:.3f}** | **{ov_all:.3f}** | **{grade(ov_all)}** |"
    )


def append_difficulty_table(lines: list[str], rows: list[dict]) -> None:
    lines.append("| Difficulty | Questions | Semantic | Citation | Keyword | Overall |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    by_diff: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_diff[row["difficulty"]].append(row)

    for diff in ("easy", "medium", "hard"):
        diff_rows = by_diff.get(diff, [])
        if not diff_rows:
            continue
        lines.append(
            f"| {diff} | {len(diff_rows)} | "
            f"{mean(row['semantic'] for row in diff_rows):.3f} | "
            f"{mean(row['citation'] for row in diff_rows):.3f} | "
            f"{mean(row['keyword'] for row in diff_rows):.3f} | "
            f"**{mean(overall(row) for row in diff_rows):.3f}** |"
        )


def render_report(
    rows: list[dict],
    *,
    output: Path,
    vector_dir: Path,
    groundtruth_path: Path,
    semantic_enabled: bool,
) -> None:
    lines: list[str] = []
    lines.append("# Vector-only RAG Benchmark Score\n")
    lines.append(f"- Vector answers: `{rel(vector_dir)}`")
    lines.append(f"- Groundtruth: `{rel(groundtruth_path)}`")
    lines.append(f"- Total rows: **{len(rows)}**")
    lines.append(
        f"- Weights: semantic **{WEIGHTS['semantic']:.0%}**, "
        f"citation **{WEIGHTS['citation']:.0%}**, keyword **{WEIGHTS['keyword']:.0%}**"
    )
    if not semantic_enabled:
        lines.append("- Semantic scoring: **disabled** (`--no-semantic`)")
    lines.append("")

    missing_gt = sum(1 for row in rows if not row.get("ground_truth"))
    missing_answer = sum(1 for row in rows if not row.get("model_answer"))
    if len(rows) != 90 or missing_gt or missing_answer:
        lines.append("## Data warnings\n")
        if len(rows) != 90:
            lines.append(f"- Expected 90 rows, parsed {len(rows)} rows.")
        if missing_gt:
            lines.append(f"- Missing groundtruth: {missing_gt} rows.")
        if missing_answer:
            lines.append(f"- Missing vector answer: {missing_answer} rows.")
        lines.append("")

    lines.append("## Overview\n")
    append_summary_table(lines, rows)

    lines.append("\n## By Difficulty\n")
    append_difficulty_table(lines, rows)

    by_law: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_law[row["law_key"]].append(row)

    for spec in LAW_SPECS:
        law_rows = by_law.get(spec["key"], [])
        if not law_rows:
            continue

        lines.append(f"\n## {spec['title']}\n")
        append_difficulty_table(lines, law_rows)

        lines.append("\n### Details\n")
        lines.append("| No. | ID | Difficulty | Reference | Semantic | Citation | Keyword | Overall |")
        lines.append("|---:|---|---|---|---:|---:|---:|---:|")
        for row in law_rows:
            lines.append(
                f"| {row['number']} | {escape_cell(row['id'])} | {row['difficulty']} | "
                f"{escape_cell(row['reference'])} | {row['semantic']:.3f} | "
                f"{row['citation']:.3f} | {row['keyword']:.3f} | **{overall(row):.3f}** |"
            )

        worst = sorted(law_rows, key=overall)[:5]
        lines.append("\n### Lowest 5\n")
        for row in worst:
            question = escape_cell(row["question"])[:240]
            lines.append(
                f"- **{row['number']}. {escape_cell(row['id'])}** ({row['difficulty']}): "
                f"overall `{overall(row):.3f}`, sem `{row['semantic']:.3f}`, "
                f"cit `{row['citation']:.3f}`, kw `{row['keyword']:.3f}`. "
                f"Question: {question}"
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vector-dir",
        default=str(ROOT / "benchmark" / "vector_benchmark"),
        help="Directory containing legal_qa_answers_vector_*.md files.",
    )
    parser.add_argument(
        "--groundtruth",
        default=None,
        help="Groundtruth MD path. Defaults to Dap_an_90_cau_hoi_groundtruth.md.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(ROOT / "benchmark" / "vector_benchmark" / "benchmark_vector_score_report.md"),
    )
    parser.add_argument("--device", default="gpu")
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip embedding similarity. Useful for validating Markdown parsing quickly.",
    )
    args = parser.parse_args()

    vector_dir = project_path(args.vector_dir)
    groundtruth_path = resolve_groundtruth(args.groundtruth)
    output = project_path(args.output)

    rows = collect_rows(vector_dir, groundtruth_path)
    if not rows:
        print("[error] No rows parsed from vector benchmark Markdown files.")
        return 1

    print(f"[info] Parsed {len(rows)} rows from {rel(vector_dir)}")
    if len(rows) != 90:
        print(f"[warn] Expected 90 rows, got {len(rows)}")

    score_rows(rows, device=args.device, semantic=not args.no_semantic)
    render_report(
        rows,
        output=output,
        vector_dir=vector_dir,
        groundtruth_path=groundtruth_path,
        semantic_enabled=not args.no_semantic,
    )

    print("\n=== Vector-only benchmark summary ===")
    by_law: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_law[row["law_key"]].append(row)
    for spec in LAW_SPECS:
        law_rows = by_law.get(spec["key"], [])
        if law_rows:
            print(f"  {spec['title']:<48} N={len(law_rows):3d} overall={mean(overall(r) for r in law_rows):.3f}")
    print(f"  {'ALL':<48} N={len(rows):3d} overall={mean(overall(r) for r in rows):.3f}")
    print(f"\n[done] Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
