"""
chunker.py
Chunking văn bản pháp luật theo cấu trúc: Chương → Điều → Khoản.

Chiến lược:
  - Chunk cấp DIEU: toàn bộ nội dung 1 Điều (ngữ cảnh đầy đủ)
  - Chunk cấp KHOAN: từng Khoản riêng (nếu Điều > 600 ký tự)
  - Mỗi chunk mang đầy đủ metadata để filter trong Qdrant
  - chunk_id là cầu nối sang Neo4j (neo4j_id)
  - amendment_type: nhận diện Điều sửa đổi/bổ sung/bãi bỏ/chuyển tiếp
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


# ── Amendment type constants ────────────────────────────────────────
AMENDMENT_SUA_DOI    = "sua_doi"       # Điều sửa đổi, bổ sung luật khác
AMENDMENT_BAI_BO     = "bai_bo"        # Điều bãi bỏ
AMENDMENT_HIEU_LUC   = "hieu_luc"      # Điều hiệu lực thi hành
AMENDMENT_CHUYEN_TIEP = "chuyen_tiep"  # Điều khoản chuyển tiếp


@dataclass
class LawChunk:
    chunk_id: str            # UUID duy nhất  → Qdrant point id
    neo4j_id: str            # ID DieuLuat trong Neo4j  → cầu nối
    law_name: str            # VD: "LuatAnNinhMang2025"
    so_hieu: str             # VD: "116/2025/QH15"
    chuong_so: str           # VD: "I"
    chuong_ten: str          # VD: "NHỮNG QUY ĐỊNH CHUNG"
    dieu_so: str             # VD: "2"
    dieu_ten: str            # VD: "Giải thích từ ngữ"
    khoan_so: Optional[str]  # VD: "1", None nếu chunk cả Điều
    chunk_type: str          # "dieu" | "khoan"
    content: str             # Nội dung gốc (trả cho LLM)
    content_for_embed: str   # Nội dung đã normalize (để embed)
    # ── Amendment metadata ──────────────────────────────────────
    amendment_type: Optional[str] = None   # None | "sua_doi" | "bai_bo" | "hieu_luc" | "chuyen_tiep"
    affected_laws: list[str] = field(default_factory=list)  # Danh sách số hiệu luật bị ảnh hưởng


# ── Regex patterns ──────────────────────────────────────────────────

# Sau khi extract từ docx, mỗi đoạn nằm trên 1 dòng.
# "Chương I NHỮNG QUY ĐỊNH CHUNG"  (tất cả trên 1 dòng)
CHUONG_PATTERN = re.compile(
    r"^Chương\s+([IVXivx\d]+)\s+(.*?)$",
    re.MULTILINE
)

# "Điều 1. Tên điều Nội dung khoản 1..."  (tất cả trên 1 dòng hoặc nhiều dòng)
DIEU_PATTERN = re.compile(
    r"^[ĐĐ]iều\s+(\d+[a-z]?)\.\s+(.+)",
    re.MULTILINE
)

# ── Amendment detection patterns ────────────────────────────────────
_AMEND_SUA_DOI_RE = re.compile(
    r"sửa đổi[,\s]*bổ sung|thay thế[,\s]*(một số|cụm từ)|thay cụm từ",
    re.IGNORECASE
)
_AMEND_BAI_BO_RE = re.compile(
    r"bãi bỏ",
    re.IGNORECASE
)
_AMEND_HIEU_LUC_RE = re.compile(
    r"hiệu lực thi hành|có hiệu lực",
    re.IGNORECASE
)
_AMEND_CHUYEN_TIEP_RE = re.compile(
    r"chuyển tiếp|điều khoản chuyển tiếp|quy định chuyển tiếp",
    re.IGNORECASE
)

# Pattern tìm số hiệu luật bị ảnh hưởng (Unicode-aware)
_AFFECTED_LAW_RE = re.compile(
    r"(?:Luật|Nghị quyết|Pháp lệnh)\s+[\w\sĐđÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỂưăạảấầẩẫậắằẳẵặẹẻẽềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴỶỸửữựỳỵỷỹ,]+?\s+số\s+(\d+/\d{4}/\w+)",
    re.IGNORECASE
)

# ── Law metadata ────────────────────────────────────────────────────
LAW_META = {
    "LuatAnNinhMang2025": {
        "so_hieu": "116/2025/QH15",
        "ten":     "Luật An ninh mạng 2025",
    },
    "LuatCNTT2006": {
        "so_hieu": "67/2006/QH11",
        "ten":     "Luật Công nghệ thông tin 2006",
    },
    "LuatVienThong2023": {
        "so_hieu": "24/2023/QH15",
        "ten":     "Luật Viễn thông 2023",
    },
}


def _make_chunk_id(law_name: str, dieu_so: str, khoan_so: Optional[str]) -> tuple[str, str]:
    """Trả về (chunk_id UUID, neo4j_id string)."""
    if khoan_so:
        raw_id = f"{law_name}_dieu_{dieu_so}_khoan_{khoan_so}"
    else:
        raw_id = f"{law_name}_dieu_{dieu_so}"
    neo4j_id = f"{law_name}_dieu_{dieu_so}"
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
    return chunk_id, neo4j_id


def _normalize_for_embed(text: str) -> str:
    """Chuẩn hóa text dùng để tạo embedding."""
    text = re.sub(r"\s+", " ", text)
    text = text.lower()
    # Bỏ số thứ tự đầu khoản (không cần thiết cho embedding)
    text = re.sub(r"^\d+\.\s+", "", text)
    return text.strip()


def _detect_amendment_type(dieu_ten: str, dieu_content: str) -> Optional[str]:
    """
    Nhận diện loại Điều sửa đổi/bổ sung dựa trên tên và nội dung.
    Trả về amendment_type hoặc None nếu là Điều thông thường.
    """
    ten_lower = dieu_ten.lower()

    # Ưu tiên check theo tên Điều (chính xác hơn)
    if _AMEND_CHUYEN_TIEP_RE.search(ten_lower):
        return AMENDMENT_CHUYEN_TIEP
    if _AMEND_HIEU_LUC_RE.search(ten_lower):
        return AMENDMENT_HIEU_LUC
    # Sửa đổi/bãi bỏ phải liên quan đến LUẬT hoặc ĐIỀU (tránh false positive
    # với "sửa đổi, bổ sung giấy phép" — đó là thủ tục hành chính, không phải sửa luật)
    if _AMEND_SUA_DOI_RE.search(ten_lower):
        # Chỉ coi là amendment nếu tên chứa "luật" hoặc "điều" hoặc "quy định"
        if re.search(r"(luật|điều|quy định|pháp lệnh|nghị quyết)", ten_lower):
            return AMENDMENT_SUA_DOI
    if _AMEND_BAI_BO_RE.search(ten_lower):
        if re.search(r"(luật|điều|quy định|pháp lệnh|nghị quyết)", ten_lower):
            return AMENDMENT_BAI_BO

    # Fallback: check nội dung (chỉ cho một số trường hợp tên ngắn)
    # Chỉ check 500 ký tự đầu để tránh false positive
    content_head = dieu_content[:500].lower()
    if "sửa đổi, bổ sung một số điều" in content_head:
        return AMENDMENT_SUA_DOI
    if "hết hiệu lực kể từ ngày" in content_head:
        return AMENDMENT_HIEU_LUC

    return None


def _extract_affected_law_ids(content: str) -> list[str]:
    """
    Extract danh sách số hiệu luật bị ảnh hưởng trong nội dung Điều sửa đổi.
    VD: "67/2006/QH11", "86/2015/QH13"
    """
    matches = _AFFECTED_LAW_RE.findall(content)
    # Dedup giữ thứ tự
    seen = set()
    result = []
    for so_hieu in matches:
        if so_hieu not in seen:
            seen.add(so_hieu)
            result.append(so_hieu)
    return result


def _parse_chapters(text: str) -> list[dict]:
    """
    Phân tách text thành danh sách Chương.
    Format thực tế: "Chương I NHỮNG QUY ĐỊNH CHUNG" (cùng 1 dòng)
    """
    chapters = []
    matches = list(CHUONG_PATTERN.finditer(text))
    if not matches:
        return [{"so": "I", "ten": "", "content": text}]

    for i, m in enumerate(matches):
        so  = m.group(1).upper()
        ten = m.group(2).strip().title() if m.group(2).strip() else ""
        start = m.end()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end]
        chapters.append({"so": so, "ten": ten, "content": content})

    return chapters


def chunk_law(text: str, law_name: str) -> list[LawChunk]:
    """
    Hàm chính: nhận toàn bộ text văn bản + tên luật,
    trả về danh sách LawChunk.

    Cấu trúc thực tế sau extract từ docx:
      - Mỗi đoạn trên 1 dòng (extractor đã gộp wrap)
      - Chương: "Chương I NHỮNG QUY ĐỊNH CHUNG"
      - Điều: "Điều 1. Tên điều [khoản 1 text...] [khoản 2 text...]"
      - Khoản: KHÔNG có số đầu dòng riêng — đã nằm trong dòng Điều
               hoặc là các dòng kế tiếp liệt kê điểm a, b, c
    """
    meta = LAW_META.get(law_name, {"so_hieu": "", "ten": law_name})
    chunks: list[LawChunk] = []
    chapters = _parse_chapters(text)

    for chap in chapters:
        chuong_so  = chap["so"]
        chuong_ten = chap["ten"]
        chap_text  = chap["content"]

        # Tìm vị trí tất cả Điều trong Chương
        dieu_matches = list(DIEU_PATTERN.finditer(chap_text))
        if not dieu_matches:
            continue

        for j, dm in enumerate(dieu_matches):
            dieu_so   = dm.group(1)
            # Lấy phần còn lại sau "Điều X. " cho đến Điều tiếp theo
            d_start   = dm.start()
            d_end     = dieu_matches[j + 1].start() if j + 1 < len(dieu_matches) else len(chap_text)
            dieu_block = chap_text[d_start:d_end].strip()

            # Tên Điều: phần sau "Điều X. " đến trước nội dung khoản 1
            # Dùng heuristic: tên kết thúc khi gặp từ khóa nội dung khoản
            # hoặc khi gặp số khoản "1." ở vị trí đầu câu trong header
            first_line = dieu_block.split("\n")[0]
            header_match = re.match(r"^[ĐĐ]iều\s+\d+[a-z]?\.\s+(.+)", first_line)
            if header_match:
                raw_ten = header_match.group(1)
                # Tên Điều thường trước dấu chấm đầu tiên nếu nội dung khoản bắt đầu bằng số
                # Cắt tại " 1. " hoặc "Trong Luật" hoặc giới hạn 100 ký tự
                for stopper in [" 1. ", " 1.  ", "\n1.", "Trong Luật",
                                 "Luật này", "Tổ chức", "Cơ quan", "Doanh nghiệp"]:
                    idx = raw_ten.find(stopper)
                    if idx > 5:
                        raw_ten = raw_ten[:idx]
                        break
                dieu_ten = raw_ten.strip().rstrip(".")[:120]
            else:
                dieu_ten = f"Điều {dieu_so}"

            # ── Detect amendment type ────────────────────────────
            amendment_type = _detect_amendment_type(dieu_ten, dieu_block)
            affected_laws = (
                _extract_affected_law_ids(dieu_block) if amendment_type else []
            )

            # ── Chunk cấp DIEU ──────────────────────────────────
            cid, nid = _make_chunk_id(law_name, dieu_so, None)
            # KHÔNG prepend header riêng — đã có trong dieu_block
            context_header = (
                f"[{meta['ten']} | Chương {chuong_so}: {chuong_ten}]\n"
            )
            # Thêm amendment tag vào content cho embedding hiểu context
            if amendment_type:
                amend_label = {
                    AMENDMENT_SUA_DOI: "SỬA ĐỔI BỔ SUNG",
                    AMENDMENT_BAI_BO: "BÃI BỎ",
                    AMENDMENT_HIEU_LUC: "HIỆU LỰC THI HÀNH",
                    AMENDMENT_CHUYEN_TIEP: "QUY ĐỊNH CHUYỂN TIẾP",
                }.get(amendment_type, "")
                context_header += f"[LOẠI ĐIỀU: {amend_label}]\n"

            full_content = context_header + dieu_block

            chunks.append(LawChunk(
                chunk_id=cid,
                neo4j_id=nid,
                law_name=law_name,
                so_hieu=meta["so_hieu"],
                chuong_so=chuong_so,
                chuong_ten=chuong_ten,
                dieu_so=dieu_so,
                dieu_ten=dieu_ten,
                khoan_so=None,
                chunk_type="dieu",
                content=full_content,
                content_for_embed=_normalize_for_embed(full_content),
                amendment_type=amendment_type,
                affected_laws=affected_laws,
            ))

            # ── Chunk cấp KHOAN ────────────────────────────────
            # Khoản là các dòng trong dieu_block không phải dòng đầu (header)
            # Tách theo các dòng bắt đầu bằng chữ thường/dấu đầu dòng
            body_lines = dieu_block.split("\n")[1:]  # bỏ dòng "Điều X. ..."
            khoan_buffer: list[tuple[str, str]] = []  # (so_khoan, content)
            current_khoan_lines: list[str] = []
            current_khoan_so: str = ""

            # Pattern khoản đầu dòng: số + dấu chấm + khoảng trắng
            KHOAN_START = re.compile(r"^(\d+)\.\s+\S")

            for line in body_lines:
                km = KHOAN_START.match(line)
                if km:
                    # Lưu khoản trước (nếu có)
                    if current_khoan_lines and current_khoan_so:
                        khoan_buffer.append(
                            (current_khoan_so, "\n".join(current_khoan_lines))
                        )
                    current_khoan_so = km.group(1)
                    current_khoan_lines = [line]
                else:
                    if current_khoan_so:
                        current_khoan_lines.append(line)

            # Lưu khoản cuối
            if current_khoan_lines and current_khoan_so:
                khoan_buffer.append(
                    (current_khoan_so, "\n".join(current_khoan_lines))
                )

            # Chỉ tạo chunk khoản nếu Điều có ≥ 2 khoản VÀ mỗi khoản đủ dài
            if len(khoan_buffer) >= 2:
                for k_so, k_body in khoan_buffer:
                    k_body = k_body.strip()
                    if len(k_body) < 30:
                        continue
                    cid_k, nid_k = _make_chunk_id(law_name, dieu_so, k_so)
                    khoan_header = (
                        f"[{meta['ten']} | Chương {chuong_so}: {chuong_ten}]\n"
                        f"Điều {dieu_so}. {dieu_ten} — Khoản {k_so}\n"
                    )
                    khoan_content = khoan_header + k_body
                    chunks.append(LawChunk(
                        chunk_id=cid_k,
                        neo4j_id=nid_k,
                        law_name=law_name,
                        so_hieu=meta["so_hieu"],
                        chuong_so=chuong_so,
                        chuong_ten=chuong_ten,
                        dieu_so=dieu_so,
                        dieu_ten=dieu_ten,
                        khoan_so=k_so,
                        chunk_type="khoan",
                        content=khoan_content,
                        content_for_embed=_normalize_for_embed(khoan_content),
                        amendment_type=amendment_type,
                        affected_laws=affected_laws,
                    ))

    return chunks