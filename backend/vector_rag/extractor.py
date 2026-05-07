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

    # VBHN: inline chú thích bãi bỏ vào body TRƯỚC khi strip [N], để giữ
    # thông tin "Điều X bị bãi bỏ theo Luật Y số NN/YYYY/QH" trong content.
    raw = _inline_vbhn_abrogation_notes(raw)

    # Strip footnote refs `[N]` trước merge để không phá pattern "Điều X." / "N."
    # (VBHN có "Điều 10.[6]" và "9.[2]" — phải normalize trước khi parse line)
    raw = _strip_footnote_refs(raw)

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

    # Strip footnote refs sớm (PDF VBHN cũng có thể có)
    text = _strip_footnote_refs(text)

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
        r"^(Điều\s+\d|Chương\s+[IVX\d]|Mục\s+\d|[1-9]\d*\.\s+\S"
        r"|[a-zđ]\)\s|LUẬT|CỘNG HÒA|QUỐC HỘI|[_=\-]{5,}\s*$)"
    )
    SENTENCE_END = re.compile(r"[.;:]\s*$")
    # Buffer là dòng tiêu đề "Điều X. <Title>" — chặn merge body vào tiêu đề.
    # Nhưng cho phép merge khi buffer kết thúc bằng dấu phẩy/chấm phẩy (title
    # dài bị wrap qua nhiều paragraph trong docx, line tiếp là phần còn lại
    # của title chứ không phải body).
    ARTICLE_HEADER_BUFFER = re.compile(r"^Điều\s+\d+[a-z]?\.\s+\S")
    TITLE_CONTINUES = re.compile(r"[,;]\s*$")

    for line in lines:
        if not line.strip():
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append("")
            continue

        is_article_header_complete = (
            ARTICLE_HEADER_BUFFER.match(buffer)
            and not TITLE_CONTINUES.search(buffer)
        )
        if not buffer:
            buffer = line
        elif (KEEP_NEWLINE_START.match(line)
              or SENTENCE_END.search(buffer)
              or is_article_header_complete):
            result.append(buffer)
            buffer = line
        else:
            # wrap → gộp với khoảng trắng
            buffer = buffer.rstrip() + " " + line.lstrip()

    if buffer:
        result.append(buffer)

    return "\n".join(result)


def _strip_vbhn_footnotes(text: str) -> str:
    """
    Văn bản hợp nhất (VBHN) có section ghi chú ở cuối, dạng:

        ______________________________
        [1] Luật Quy hoạch số 21/2017/QH14 ...
        [2] Khoản này được bãi bỏ theo ...

    Section này chứa lại các "Điều 58", "Điều 53"... của luật khác,
    nếu để nguyên sẽ bị chunker parse nhầm thành nội dung luật chính.
    Cắt từ separator dấu gạch dưới hoặc từ footnote `[1]` đầu dòng.
    """
    # Pattern 1: separator + nội dung sau (đã bị merge bởi _merge_wrapped_lines)
    # vd "______________________________ Luật Quy hoạch ..."
    m = re.search(r"[_=\-]{5,}", text)
    if m:
        return text[:m.start()].rstrip()
    # Pattern 2: footnote 1 đầu dòng (chưa strip [N])
    m = re.search(r"(?m)^\[1\]\s+", text)
    if m:
        return text[:m.start()].rstrip()
    # Pattern 3: footnote 1 inline (đã strip [1] nhưng pattern còn dấu vết)
    m = re.search(r"\[1\]\s+(?:Luật|Khoản|Điều|Mục|Điểm)\s+", text)
    if m:
        return text[:m.start()].rstrip()
    return text


def _inline_vbhn_abrogation_notes(text: str) -> str:
    """
    Trong VBHN, body có markers `[N]` (vd "Điều 10.[6] (được bãi bỏ)") và phần
    cuối sau separator `______` có chú thích "[N] Điều này được bãi bỏ theo...".
    Pipeline cũ strip [N] mất link, làm mất context bãi bỏ.

    Hàm này:
      1. Parse footnote section (mỗi dòng `[N] <text>`)
      2. Chỉ giữ note nói về 'bãi bỏ' / 'hết hiệu lực'
      3. Replace marker `[N]` trong body bằng " [⚠️ <note text>]"
    Footnote section sau đó vẫn được _strip_vbhn_footnotes cắt bỏ ở clean_text.
    """
    sep_match = re.search(r"\n[_=\-]{5,}", text)
    if not sep_match:
        return text
    body = text[:sep_match.start()]
    fn_section = text[sep_match.end():]

    notes: dict[str, str] = {}
    for line in fn_section.split("\n"):
        m = re.match(r"^\s*\[(\d+)\]\s+(.+)", line)
        if not m:
            continue
        idx, txt = m.group(1), m.group(2).strip()
        if re.search(r"bãi bỏ|hết hiệu lực", txt, re.IGNORECASE):
            notes[idx] = txt

    if not notes:
        return text

    def repl(m: re.Match) -> str:
        n = m.group(1)
        return f" [⚠️ {notes[n]}]" if n in notes else ""

    new_body = re.sub(r"\[(\d+)\]", repl, body)
    return new_body + text[sep_match.start():]


def _strip_footnote_refs(text: str) -> str:
    """
    Strip footnote inline markers `[N]` trong VBHN.
    VD: "Điều 10.[6] (được bãi bỏ)" → "Điều 10. (được bãi bỏ)"
        "9.[2] (được bãi bỏ)"        → "9. (được bãi bỏ)"
        "thông tin[1]."               → "thông tin."
    """
    return re.sub(r"\[\d+\]", "", text)


def clean_text(text: str) -> str:
    """
    Normalize text sau khi extract:
    - Xóa ký tự rác, chuẩn hóa khoảng trắng
    - Strip footnote section (VBHN) + [N] markers
    - Giữ nguyên dấu câu tiếng Việt
    """
    # 1. Cắt section footnote ở cuối (chỉ áp dụng cho VBHN; no-op với luật thường)
    text = _strip_vbhn_footnotes(text)
    # 2. Bỏ marker [N] inline
    text = _strip_footnote_refs(text)
    # 3. Xóa ký tự điều khiển (trừ newline) — \xa0 cũng được normalize về space
    text = re.sub(r"[^\S\n]+", " ", text)
    # 4. Chuẩn hóa nhiều newline liên tiếp
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 5. Bỏ khoảng trắng đầu/cuối mỗi dòng
    lines = [l.strip() for l in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()