"""
extractor.py
Trích xuất raw text từ file .docx (Luật pháp luật tiếng Việt).
Output: chuỗi văn bản thuần, đã gộp các dòng bị xuống hàng lạ.
"""

import re
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