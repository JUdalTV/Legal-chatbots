"""
extractor.py
Trích xuất raw text từ file văn bản pháp luật tiếng Việt (.docx | .pdf).
Output: chuỗi văn bản thuần, đã gộp các dòng bị xuống hàng lạ.
"""

import re
from pathlib import Path

from docx import Document


def extract_docx(path: str) -> str:
    """
    Đọc file .docx và trả về toàn bộ văn bản dạng string.
    Gộp các đoạn bị wrap (xuống hàng giữa câu do định dạng Word).
    """
    doc = Document(path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    raw = "\n".join(lines)

    # Gộp dòng bị wrap: nếu dòng trước không kết thúc bằng dấu câu
    # hoặc bắt đầu bằng chữ thường/số tiếp theo → gộp lại
    raw = _merge_wrapped_lines(raw)
    return raw


def extract_pdf(path: str) -> str:
    """
    Đọc file .pdf bằng PyMuPDF (`fitz`) và trả về raw text.

    Xử lý cơ bản:
      - Bỏ header/footer lặp lại trên các trang (số trang, tên luật)
      - Loại bỏ hyphen wrap "viễn-\nthông" → "viễnthông"
      - Sau đó dùng `_merge_wrapped_lines` (giống .docx) để gộp wrap
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError(
            "Thiếu PyMuPDF cho PDF. Cài: pip install pymupdf"
        ) from e

    doc = fitz.open(path)
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()

    text = "\n".join(pages)

    # Bỏ hyphen wrap cuối dòng: "viễn-\nthông" → "viễnthông"
    text = re.sub(r"-\n(?=\w)", "", text)

    # Bỏ các dòng chỉ chứa số trang (1–4 chữ số) hoặc "Trang N/M"
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)
    text = re.sub(r"(?m)^\s*Trang\s+\d+(?:\s*/\s*\d+)?\s*$", "", text, flags=re.IGNORECASE)

    # Bỏ các dòng lặp lại nhiều lần (header/footer xuất hiện trên >= 3 trang)
    text = _drop_repeated_short_lines(text, min_repeat=3, max_len=80)

    return _merge_wrapped_lines(text)


def extract_text(path: str) -> str:
    """Dispatch theo đuôi file: .docx → extract_docx, .pdf → extract_pdf."""
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".pdf":
        return extract_pdf(path)
    raise ValueError(f"Định dạng không hỗ trợ: {ext!r}. Chỉ chấp nhận .docx hoặc .pdf")


def _drop_repeated_short_lines(text: str, min_repeat: int = 3, max_len: int = 80) -> str:
    """Loại bỏ các dòng ngắn xuất hiện ≥ min_repeat lần (header/footer điển hình)."""
    lines = text.split("\n")
    counts: dict[str, int] = {}
    for ln in lines:
        s = ln.strip()
        if 0 < len(s) <= max_len:
            counts[s] = counts.get(s, 0) + 1
    drop = {s for s, c in counts.items() if c >= min_repeat}
    return "\n".join(ln for ln in lines if ln.strip() not in drop)


def _merge_wrapped_lines(text: str) -> str:
    """
    Gộp các dòng bị xuống hàng do wrap trong Word.
    Giữ nguyên xuống hàng khi:
      - Dòng kế tiếp bắt đầu bằng 'Điều', 'Chương', 'Mục', số thứ tự 'N.'
      - Dòng trước kết thúc bằng dấu câu kết (.  ;  :)
    """
    lines = text.split("\n")
    result = []
    buffer = ""

    KEEP_NEWLINE_START = re.compile(
        r"^(Điều\s+\d|Chương\s+[IVX\d]|Mục\s+\d|[1-9]\d*\.\s+[A-ZĐÁÀẢÃẠ]"
        r"|[a-zđ]\)\s|LUẬT|CỘNG HÒA|QUỐC HỘI)"
    )
    SENTENCE_END = re.compile(r"[.;:]\s*$")

    for line in lines:
        if not line.strip():
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append("")
            continue

        if not buffer:
            buffer = line
        elif KEEP_NEWLINE_START.match(line) or SENTENCE_END.search(buffer):
            result.append(buffer)
            buffer = line
        else:
            # wrap → gộp với khoảng trắng
            buffer = buffer.rstrip() + " " + line.lstrip()

    if buffer:
        result.append(buffer)

    return "\n".join(result)


def clean_text(text: str) -> str:
    """
    Normalize text sau khi extract:
    - Xóa ký tự rác, chuẩn hóa khoảng trắng
    - Giữ nguyên dấu câu tiếng Việt
    """
    # Xóa ký tự điều khiển (trừ newline)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Chuẩn hóa nhiều newline liên tiếp
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Bỏ khoảng trắng đầu/cuối mỗi dòng
    lines = [l.strip() for l in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()