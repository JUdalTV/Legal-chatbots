"""
strip_thinking.py — Loại bỏ phần thinking (`<think>...</think>`) khỏi các file MD
benchmark đã chạy với reasoning mode, chỉ giữ Question + Answer cuối cùng.

Pattern: trong mỗi block `## Câu N`, sau `**Answer:**` thường có 1 đoạn thinking
dài rồi tới `</think>` mới là answer thật. Script này:
  - Tìm `</think>` đầu tiên sau `**Answer:**` trong mỗi câu.
  - Xoá toàn bộ text từ ngay sau `**Answer:**` đến và bao gồm `</think>`.
  - Giữ nguyên cấu trúc + answer cuối.
  - Câu không có `</think>` → giữ nguyên, in cảnh báo.

Mặc định in-place trên toàn bộ thư mục `benchmark/claude_benchmark/vector_reasoning/`.
Có thể chỉ định path khác qua argv.

Chạy:
    & .venv\\Scripts\\python.exe benchmark\\strip_thinking.py
    & .venv\\Scripts\\python.exe benchmark\\strip_thinking.py <other-dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "benchmark" / "claude_benchmark" / "vector_reasoning"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Split file theo header câu (`## Câu N`). Giữ luôn header trong block tiếp theo.
_RX_QCAU = re.compile(r"(?m)^## Câu \d+\s*$")

# Trong 1 block, match cụm từ `**Answer:**` đến hết `</think>` (kèm whitespace sau).
_RX_THINK_AFTER_ANSWER = re.compile(
    r"(\*\*Answer:\*\*[ \t]*\n)"   # group 1: header **Answer:**\n
    r".*?"                          # thinking content (non-greedy)
    r"</think>[ \t]*\n*",           # kết thúc tại </think>
    re.DOTALL,
)


def strip_block(block: str) -> tuple[str, bool]:
    """
    Trả (block_đã_clean, có_xoá_thinking_hay_không).
    """
    new, n = _RX_THINK_AFTER_ANSWER.subn(r"\1", block, count=1)
    return new, bool(n)


def process_file(path: Path) -> tuple[int, int]:
    """Trả (n_stripped, n_skipped) — số câu đã clean và số câu không có </think>."""
    text = path.read_text(encoding="utf-8")

    # Split giữ delimiter: dùng re.split với capture group để giữ header
    parts = _RX_QCAU.split(text)
    headers = _RX_QCAU.findall(text)

    if not headers:
        # Không phát hiện câu nào → bỏ qua
        return 0, 0

    # parts[0] là phần trước "## Câu 1" (preamble). parts[i] (i>=1) là body của câu thứ i.
    preamble = parts[0]
    bodies = parts[1:]
    assert len(headers) == len(bodies), f"mismatch in {path}"

    n_stripped = n_skipped = 0
    new_blocks: list[str] = [preamble]
    for hdr, body in zip(headers, bodies):
        new_body, changed = strip_block(body)
        if changed:
            n_stripped += 1
        else:
            # Vẫn có thể có thinking nhưng không close </think> → ghi nhận
            if "**Answer:**" in body and "</think>" not in body:
                n_skipped += 1
        new_blocks.append(hdr + "\n" + new_body.lstrip("\n"))

    # Cleanup: collapse 3+ newline → 2
    final = "".join(new_blocks)
    final = re.sub(r"\n{3,}", "\n\n", final)

    path.write_text(final, encoding="utf-8", newline="\n")
    return n_stripped, n_skipped


def main(argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else DEFAULT_DIR
    if not target.exists():
        print(f"[error] không tìm thấy {target}")
        return 1

    files = sorted(target.rglob("*.md"))
    if not files:
        print(f"[warn] không có file .md nào trong {target}")
        return 0

    total_stripped = total_skipped = 0
    for f in files:
        n, sk = process_file(f)
        total_stripped += n
        total_skipped += sk
        rel = f.relative_to(target.parent if target.is_file() else target)
        flag = "" if sk == 0 else f"  (⚠ {sk} câu không có </think>)"
        print(f"  [{n:>2} stripped] {rel}{flag}")

    print(f"\n[done] {len(files)} files · {total_stripped} câu đã clean · "
          f"{total_skipped} câu bỏ qua (không có </think>).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
