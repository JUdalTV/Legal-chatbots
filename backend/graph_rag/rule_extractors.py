"""
rule_extractors.py  —  Rule-based extractors cho noi dung phap ly

Bao gom:
  1. KhaiNiemPhapLy
  2. HanhViBiCam
  3. THAM_CHIEU
  4. Quan he lien luat (BAI_BO, SUA_DOI_BO_SUNG)
  5. Chi tiet sua doi cap Dieu/Khoan
  6. Quy dinh chuyen tiep
"""
from __future__ import annotations
import re

# ====================================================================
# 1. KhaiNiemPhapLy
# ====================================================================

_KN_NUMBERED = re.compile(
    r"^\d+\.{1,2}\s*([^.\n\r]{3,80}?)\s+l\u00e0\s+(.+?)$",
    re.MULTILINE,
)
_KN_NO_NUMBER = re.compile(
    r"^([A-Z\u0110\u00c1\u00c0\u1ea2\u00c3\u1ea0\u0102\u1eac\u1eae\u1eb0\u1eb2\u1eb4\u1eb6\u00c2\u1ea4\u1ea6\u1ea8\u1eaa\u1eac"
    r"\u00c9\u00c8\u1eba\u1ebc\u1eb8\u00ca\u1ebe\u1ec0\u1ec2\u1ec4\u1ec6"
    r"\u00cd\u00cc\u1ec8\u0128\u1eca"
    r"\u00d3\u00d2\u1ece\u00d5\u1ecc\u00d4\u1ed0\u1ed2\u1ed4\u1ed6\u1ed8\u01a0\u1eda\u1edc\u1ede\u1ee0\u1ee2"
    r"\u00da\u00d9\u1ee6\u0168\u1ee4\u01af\u1ee8\u1eea\u1eec\u1eee\u1ef0"
    r"\u00dd\u1ef2\u1ef6\u1ef8\u1ef4]"
    r"[^.\n\r]{2,70}?)\s+l\u00e0\s+(.+?)$",
    re.MULTILINE,
)

_SKIP_KW = ["lu\u1eadt n\u00e0y", "\u0111i\u1ec1u n\u00e0y", "kho\u1ea3n",
            "theo quy \u0111\u1ecbnh", "ch\u00ednh ph\u1ee7",
            "t\u1ed5 ch\u1ee9c", "c\u00e1 nh\u00e2n", "c\u01a1 quan",
            "doanh nghi\u1ec7p"]


def extract_khai_niem(dieu_content: str, dieu_id: str) -> list[dict]:
    result, seen = [], set()

    def _add(ten: str, dinh_nghia: str):
        ten = ten.strip().strip("*_ .")
        dinh_nghia = re.sub(r"\s+", " ", dinh_nghia.strip())
        if len(ten) < 3 or len(dinh_nghia) < 10 or len(ten) > 80:
            return
        if any(kw in ten.lower() for kw in _SKIP_KW):
            return
        if ten in seen:
            return
        seen.add(ten)
        result.append({"ten": ten, "dinh_nghia": dinh_nghia[:600], "dieu_id": dieu_id})

    for pat in (_KN_NUMBERED, _KN_NO_NUMBER):
        for m in pat.finditer(dieu_content):
            _add(m.group(1), m.group(2))

    return result


# ====================================================================
# 2. HanhViBiCam
# ====================================================================

_CAM_KHOAN = re.compile(r"^(\d+)\.\s+(.{15,}?)$", re.MULTILINE)
_CAM_DIEM  = re.compile(r"^([a-z\u0111])\)\s+(.{10,}?)$", re.MULTILINE)


def extract_hanh_vi_bi_cam(dieu_content: str, dieu_id: str) -> list[dict]:
    result, seen = [], set()

    def _add(noi_dung: str):
        noi_dung = re.sub(r"\s+", " ", noi_dung.strip())
        if len(noi_dung) < 15:
            return
        ten = noi_dung[:120]
        if ten in seen:
            return
        seen.add(ten)
        result.append({"ten": ten, "mo_ta": noi_dung[:600], "dieu_id": dieu_id})

    for m in _CAM_KHOAN.finditer(dieu_content):
        _add(m.group(2))
    for m in _CAM_DIEM.finditer(dieu_content):
        _add(m.group(2))

    return result


# ====================================================================
# 3. THAM_CHIEU
# ====================================================================

_REF_PATTERN = re.compile(
    r"(?:theo quy \u0111\u1ecbnh t\u1ea1i|quy \u0111\u1ecbnh t\u1ea1i|c\u0103n c\u1ee9 v\u00e0o|c\u0103n c\u1ee9|theo|t\u1ea1i)\s+"
    r"(?:kho\u1ea3n\s+\d+[,\s]*(?:v\u00e0\s+kho\u1ea3n\s+\d+\s*)?)?"
    r"[\u0110\u0111]i\u1ec1u\s+(\d+[a-z]?)",
    re.IGNORECASE,
)


def extract_references(content: str, from_dieu_so: str, law_name: str) -> list[dict]:
    refs, seen = [], set()
    for m in _REF_PATTERN.finditer(content):
        to_so = m.group(1)
        if to_so == from_dieu_so or to_so in seen:
            continue
        seen.add(to_so)
        start = max(0, m.start() - 60)
        end   = min(len(content), m.end() + 60)
        context = content[start:end].replace("\n", " ").strip()
        refs.append({
            "from_id": f"{law_name}_dieu_{from_dieu_so}",
            "to_id":   f"{law_name}_dieu_{to_so}",
            "context": context,
        })
    return refs


# ====================================================================
# 4. Quan he lien luat
# ====================================================================

# Unicode-aware regex cho ten luat co dau tieng Viet
_LUAT_ID_PATTERN = re.compile(
    r"(?:Lu\u1eadt|Ngh\u1ecb quy\u1ebft|Ph\u00e1p l\u1ec7nh)\s+"
    r"([\w\s\-,\u0111\u0110\u00e0\u00e1\u00e2\u00e3\u00e8\u00e9\u00ea\u00ec\u00ed\u00f2\u00f3\u00f4\u00f5\u00f9\u00fa"
    r"\u0103\u0129\u0169\u01a1\u01b0\u1ea1\u1ea3\u1ea5\u1ea7\u1ea9\u1eab\u1ead\u1eaf\u1eb1\u1eb3\u1eb5\u1eb7"
    r"\u1eb9\u1ebb\u1ebd\u1ebf\u1ec1\u1ec3\u1ec5\u1ec7\u1ec9\u1ecb\u1ecd\u1ecf\u1ed1\u1ed3\u1ed5\u1ed7\u1ed9"
    r"\u1edb\u1edd\u1edf\u1ee1\u1ee3\u1ee5\u1ee7\u1ee9\u1eeb\u1eed\u1eef\u1ef1\u1ef3\u1ef5\u1ef7\u1ef9]+?)"
    r"\s+s\u1ed1\s+(\d+/\d{4}/\w+)",
    re.IGNORECASE,
)
_BAI_BO_KW  = ["h\u1ebft hi\u1ec7u l\u1ef1c", "b\u00e3i b\u1ecf",
               "kh\u00f4ng c\u00f2n hi\u1ec7u l\u1ef1c"]
_SUA_DOI_KW = ["s\u1eeda \u0111\u1ed5i", "b\u1ed5 sung",
               "thay th\u1ebf c\u1ee5m t\u1eeb", "thay th\u1ebf m\u1ed9t s\u1ed1",
               "thay c\u1ee5m t\u1eeb"]


def extract_lien_luat(content: str, from_law_id: str) -> list[dict]:
    rels, seen = [], set()
    for line in content.split("\n"):
        ll = line.lower()
        if any(kw in ll for kw in _BAI_BO_KW):
            rel_type = "BAI_BO"
        elif any(kw in ll for kw in _SUA_DOI_KW):
            rel_type = "SUA_DOI_BO_SUNG"
        else:
            continue
        for m in _LUAT_ID_PATTERN.finditer(line):
            key = (rel_type, m.group(2))
            if key in seen:
                continue
            seen.add(key)
            rels.append({
                "from_law":   from_law_id,
                "to_law_ten": m.group(1).strip(),
                "to_so_hieu": m.group(2).strip(),
                "rel_type":   rel_type,
            })
    return rels


# ====================================================================
# 5. Chi tiet sua doi cap Dieu/Khoan
# ====================================================================

# Quote character class for matching quoted text
_Q = '[\u0022\u201c\u201d\u2018\u2019]'  # " \u201c \u201d \u2018 \u2019

# Pattern: "Thay cum tu X bang cum tu Y tai ... Dieu Z ... cua Luat ABC so NN/YYYY/QH"
_THAY_CUM_TU_RE = re.compile(
    r"[Tt]hay\s+(?:th\u1ebf\s+)?c\u1ee5m\s+t\u1eeb\s+" + _Q + r"(.+?)" + _Q
    + r"\s+(?:b\u1eb1ng\s+c\u1ee5m\s+t\u1eeb\s+" + _Q + r"(.+?)" + _Q + r")?"
    + r".*?[\u0110\u0111]i\u1ec1u\s+(\d+[a-z]?)"
    + r".*?(?:Lu\u1eadt|Ngh\u1ecb quy\u1ebft)\s+.+?\s+s\u1ed1\s+(\d+/\d{4}/\w+)",
    re.DOTALL,
)

# Pattern: "Bai bo khoan X Dieu Y" hoac "Bai bo Dieu Y"
_BAI_BO_DIEU_RE = re.compile(
    r"[Bb]\u00e3i\s+b\u1ecf\s+(?:kho\u1ea3n\s+\d+\s+)?"
    r"[\u0110\u0111]i\u1ec1u\s+(\d+[a-z]?)"
    r"(?:.*?(?:Lu\u1eadt|Ngh\u1ecb quy\u1ebft)\s+.+?\s+s\u1ed1\s+(\d+/\d{4}/\w+))?",
    re.DOTALL,
)

# Pattern: "Sua doi, bo sung diem X muc Y" hoac "Sua doi, bo sung Dieu Z"
_SUA_DOI_DIEU_RE = re.compile(
    r"[Ss]\u1eeda\s+\u0111\u1ed5i[,\s]*b\u1ed5\s+sung\s+"
    r"(?:(?:\u0111i\u1ec3m|kho\u1ea3n|m\u1ee5c)\s+[\w.]+\s+)*"
    r"(?:[\u0110\u0111]i\u1ec1u\s+(\d+[a-z]?))?"
    r"(?:.*?(?:Lu\u1eadt|Ngh\u1ecb quy\u1ebft)\s+.+?\s+s\u1ed1\s+(\d+/\d{4}/\w+))?",
    re.DOTALL,
)

# Pattern: "Luat XYZ so NN/YYYY/QH ... het hieu luc"
_HET_HIEU_LUC_RE = re.compile(
    r"(?:Lu\u1eadt|Ngh\u1ecb quy\u1ebft)\s+"
    r"([\w\s\-,\u0111\u0110\u00e0\u00e1\u00e2\u00e3\u00e8\u00e9\u00ea\u00ec\u00ed\u00f2\u00f3\u00f4\u00f5\u00f9\u00fa"
    r"\u0103\u0129\u0169\u01a1\u01b0\u1ea1\u1ea3\u1ea5\u1ea7\u1ea9\u1eab\u1ead\u1eaf\u1eb1\u1eb3\u1eb5\u1eb7"
    r"\u1eb9\u1ebb\u1ebd\u1ebf\u1ec1\u1ec3\u1ec5\u1ec7\u1ec9\u1ecb\u1ecd\u1ecf\u1ed1\u1ed3\u1ed5\u1ed7\u1ed9"
    r"\u1edb\u1edd\u1edf\u1ee1\u1ee3\u1ee5\u1ee7\u1ee9\u1eeb\u1eed\u1eef\u1ef1\u1ef3\u1ef5\u1ef7\u1ef9]+?)"
    r"\s+s\u1ed1\s+(\d+/\d{4}/\w+)"
    r".*?h\u1ebft\s+hi\u1ec7u\s+l\u1ef1c",
    re.DOTALL | re.IGNORECASE,
)


def extract_sua_doi_chi_tiet(content: str, from_dieu_id: str,
                              from_law_name: str) -> list[dict]:
    """
    Extract chi tiet sua doi tu noi dung Dieu sua doi.
    Tra ve list dict:
      - type: "thay_cum_tu" | "bai_bo_dieu" | "sua_doi_dieu" | "het_hieu_luc"
      - from_id: ID Dieu nguon (dang sua doi)
      - to_so_hieu: so hieu luat dich
      - to_dieu_so: so Dieu dich (neu co)
      - cum_tu_cu: cum tu cu (neu la thay cum tu)
      - cum_tu_moi: cum tu moi (neu la thay cum tu)
      - context: doan text boi canh
    """
    results = []
    seen = set()

    # 1. Thay cum tu
    for m in _THAY_CUM_TU_RE.finditer(content):
        cum_tu_cu = m.group(1)
        cum_tu_moi = m.group(2) or ""
        to_dieu_so = m.group(3)
        to_so_hieu = m.group(4)
        key = ("thay_cum_tu", to_so_hieu, to_dieu_so)
        if key not in seen:
            seen.add(key)
            results.append({
                "type":       "thay_cum_tu",
                "from_id":    from_dieu_id,
                "to_so_hieu": to_so_hieu,
                "to_dieu_so": to_dieu_so,
                "cum_tu_cu":  cum_tu_cu[:200],
                "cum_tu_moi": cum_tu_moi[:200],
                "context":    content[max(0, m.start()-30):m.end()+30][:300],
            })

    # 2. Bai bo Dieu/khoan cu the
    for m in _BAI_BO_DIEU_RE.finditer(content):
        to_dieu_so = m.group(1)
        to_so_hieu = m.group(2) or ""
        key = ("bai_bo_dieu", to_so_hieu, to_dieu_so)
        if key not in seen:
            seen.add(key)
            results.append({
                "type":       "bai_bo_dieu",
                "from_id":    from_dieu_id,
                "to_so_hieu": to_so_hieu,
                "to_dieu_so": to_dieu_so,
                "context":    content[max(0, m.start()-30):m.end()+30][:300],
            })

    # 3. Sua doi, bo sung Dieu cu the
    for m in _SUA_DOI_DIEU_RE.finditer(content):
        to_dieu_so = m.group(1) or ""
        to_so_hieu = m.group(2) or ""
        if not to_so_hieu:
            continue  # Bo qua neu khong xac dinh duoc luat dich
        key = ("sua_doi_dieu", to_so_hieu, to_dieu_so)
        if key not in seen:
            seen.add(key)
            results.append({
                "type":       "sua_doi_dieu",
                "from_id":    from_dieu_id,
                "to_so_hieu": to_so_hieu,
                "to_dieu_so": to_dieu_so,
                "context":    content[max(0, m.start()-30):m.end()+30][:300],
            })

    # 4. Luat het hieu luc
    for m in _HET_HIEU_LUC_RE.finditer(content):
        to_law_ten = m.group(1).strip()
        to_so_hieu = m.group(2)
        key = ("het_hieu_luc", to_so_hieu)
        if key not in seen:
            seen.add(key)
            results.append({
                "type":       "het_hieu_luc",
                "from_id":    from_dieu_id,
                "to_so_hieu": to_so_hieu,
                "to_law_ten": to_law_ten,
                "context":    content[max(0, m.start()-30):m.end()+30][:300],
            })

    return results


# ====================================================================
# 6. Quy dinh chuyen tiep
# ====================================================================

_CHUYEN_TIEP_ITEM_RE = re.compile(
    r"^(\d+)\.\s+(.+?)$",
    re.MULTILINE,
)


def extract_chuyen_tiep(content: str, dieu_id: str) -> list[dict]:
    """
    Extract cac quy dinh chuyen tiep.
    Tra ve list dict:
      - khoan_so: so khoan
      - noi_dung: noi dung quy dinh chuyen tiep
      - affected_so_hieu: list so hieu luat lien quan
    """
    results = []
    for m in _CHUYEN_TIEP_ITEM_RE.finditer(content):
        khoan_so = m.group(1)
        noi_dung = m.group(2).strip()
        if len(noi_dung) < 30:
            continue

        # Tim so hieu luat trong noi dung khoan
        affected = []
        for lm in _LUAT_ID_PATTERN.finditer(noi_dung):
            so_hieu = lm.group(2)
            if so_hieu not in affected:
                affected.append(so_hieu)

        results.append({
            "dieu_id":          dieu_id,
            "khoan_so":         khoan_so,
            "noi_dung":         noi_dung[:600],
            "affected_so_hieu": affected,
        })

    return results