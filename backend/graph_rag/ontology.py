"""
ontology.py
Định nghĩa Ontology (schema) cho Legal Knowledge Graph.

Node Labels:
  ┌─ Cấu trúc văn bản (từ Rule/chunker) ──────────────────────┐
  │  VanBanPhapLuat  → Chuong → DieuLuat → KhoanMuc           │
  └───────────────────────────────────────────────────────────┘
  ┌─ Semantic / Nội dung (từ Rule-based extractor) ────────────┐
  │  KhaiNiemPhapLy   : khái niệm được định nghĩa trong luật  │
  │  HanhViBiCam      : hành vi bị nghiêm cấm                 │
  └───────────────────────────────────────────────────────────┘
  ┌─ Actors (từ NER — chỉ ORG/PER) ───────────────────────────┐
  │  CoQuanNhaNuoc    : Bộ Công an, Chính phủ, UBND...        │
  │  DoanhNghiep      : doanh nghiệp viễn thông, CNTT...      │
  │  ToChucKhac       : tổ chức chính trị, xã hội...          │
  │  ChucDanh         : Bộ trưởng, Thủ tướng... (NER PER)    │
  └───────────────────────────────────────────────────────────┘

Edge Types:
  Cấu trúc:
    (VanBanPhapLuat)-[:CO_CHUONG]        ->(Chuong)
    (VanBanPhapLuat)-[:CO_DIEU]          ->(DieuLuat)
    (Chuong)        -[:CO_DIEU]          ->(DieuLuat)
    (DieuLuat)      -[:CO_KHOAN]         ->(KhoanMuc)
  Nội dung:
    (DieuLuat)      -[:DINH_NGHIA]       ->(KhaiNiemPhapLy)
    (DieuLuat)      -[:QUY_DINH_CAM]     ->(HanhViBiCam)
    (DieuLuat)      -[:GIAO_TRACH_NHIEM] ->(CoQuanNhaNuoc)
    (DieuLuat)      -[:AP_DUNG_VOI]      ->(DoanhNghiep|ToChucKhac)
    (DieuLuat)      -[:GIAO_QUYEN_HAN]   ->(ChucDanh)
  Liên kết:
    (DieuLuat)      -[:THAM_CHIEU]       ->(DieuLuat)
    (VanBanPhapLuat)-[:BAI_BO]           ->(VanBanPhapLuat)
    (VanBanPhapLuat)-[:SUA_DOI_BO_SUNG]  ->(VanBanPhapLuat)
  Sửa đổi chi tiết (cấp Điều):
    (DieuLuat)      -[:SUA_DOI_DIEU]     ->(DieuLuat)      ★ NEW
    (DieuLuat)      -[:BAI_BO_DIEU]      ->(DieuLuat)      ★ NEW
    (DieuLuat)      -[:THAY_THE_CUM_TU]  ->(DieuLuat)      ★ NEW
"""

# ── Node label constants ─────────────────────────────────────────────
class NodeLabel:
    VAN_BAN          = "VanBanPhapLuat"
    CHUONG           = "Chuong"
    DIEU             = "DieuLuat"
    KHOAN            = "KhoanMuc"
    KHAI_NIEM        = "KhaiNiemPhapLy"
    HANH_VI_BI_CAM   = "HanhViBiCam"
    CO_QUAN          = "CoQuanNhaNuoc"
    DOANH_NGHIEP     = "DoanhNghiep"
    TO_CHUC_KHAC     = "ToChucKhac"
    CHUC_DANH        = "ChucDanh"


# ── Edge type constants ──────────────────────────────────────────────
class EdgeType:
    CO_CHUONG         = "CO_CHUONG"
    CO_DIEU           = "CO_DIEU"
    CO_KHOAN          = "CO_KHOAN"
    DINH_NGHIA        = "DINH_NGHIA"
    QUY_DINH_CAM      = "QUY_DINH_CAM"
    GIAO_TRACH_NHIEM  = "GIAO_TRACH_NHIEM"
    AP_DUNG_VOI       = "AP_DUNG_VOI"
    GIAO_QUYEN_HAN    = "GIAO_QUYEN_HAN"
    THAM_CHIEU        = "THAM_CHIEU"
    # ── Quan hệ liên luật (cấp VanBan) ──────────────────────
    BAI_BO            = "BAI_BO"
    SUA_DOI_BO_SUNG   = "SUA_DOI_BO_SUNG"


# ── Cypher constraint + index statements ────────────────────────────
CONSTRAINTS = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.VAN_BAN})        REQUIRE n.id   IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.CHUONG})         REQUIRE n.id   IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.DIEU})           REQUIRE n.id   IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.KHOAN})          REQUIRE n.id   IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.KHAI_NIEM})      REQUIRE n.ten  IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.HANH_VI_BI_CAM}) REQUIRE n.ten  IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.CO_QUAN})        REQUIRE n.ten  IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.DOANH_NGHIEP})   REQUIRE n.ten  IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.TO_CHUC_KHAC})   REQUIRE n.ten  IS UNIQUE",
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{NodeLabel.CHUC_DANH})      REQUIRE n.ten  IS UNIQUE",
]

FULLTEXT_INDEXES = [
    f"""CREATE FULLTEXT INDEX dieu_fts IF NOT EXISTS
        FOR (d:{NodeLabel.DIEU}) ON EACH [d.ten, d.noi_dung_tom]""",
    f"""CREATE FULLTEXT INDEX khainiemphaplyfts IF NOT EXISTS
        FOR (kn:{NodeLabel.KHAI_NIEM}) ON EACH [kn.ten, kn.dinh_nghia]""",
    f"""CREATE FULLTEXT INDEX hanhvibicam_fts IF NOT EXISTS
        FOR (hv:{NodeLabel.HANH_VI_BI_CAM}) ON EACH [hv.ten, hv.mo_ta]""",
]


# ── Mapping: law_name → Điều đặc biệt ────────────────────────────────
GIAI_THICH_DIEU = {
    "LuatAnNinhMang2025": "2",
    "LuatCNTT2006":       "4",
    "LuatVienThong2023":  "3",
}

NGHIEM_CAM_DIEU = {
    "LuatAnNinhMang2025": "7",
    "LuatCNTT2006":       "12",
    "LuatVienThong2023":  "9",
}

LIEN_LUAT_DIEU = {
    "LuatAnNinhMang2025": ["43", "44"],
    "LuatCNTT2006":       [],
    "LuatVienThong2023":  ["71", "72"],
}

# ★ NEW: Mapping điều sửa đổi/bổ sung chi tiết
SUA_DOI_DIEU = {
    "LuatAnNinhMang2025": ["43"],         # Điều 43: sửa đổi luật liên quan
    "LuatCNTT2006":       [],
    "LuatVienThong2023":  ["71"],          # Điều 71: sửa đổi luật liên quan
}

# ★ NEW: Mapping điều hiệu lực thi hành
HIEU_LUC_DIEU = {
    "LuatAnNinhMang2025": ["44"],         # Điều 44: hiệu lực thi hành
    "LuatCNTT2006":       [],
    "LuatVienThong2023":  ["72"],          # Điều 72: hiệu lực thi hành
}

# ★ NEW: Mapping điều chuyển tiếp
CHUYEN_TIEP_DIEU = {
    "LuatAnNinhMang2025": ["45"],         # Điều 45: điều khoản chuyển tiếp
    "LuatCNTT2006":       [],
    "LuatVienThong2023":  ["73"],          # Điều 73: quy định chuyển tiếp
}

# Metadata cố định
VAN_BAN_META = {
    "LuatAnNinhMang2025": {
        "so_hieu": "116/2025/QH15",
        "ten":     "Luật An ninh mạng",
        "nam":     "2025",
        "loai":    "Luật",
    },
    "LuatCNTT2006": {
        "so_hieu": "67/2006/QH11",
        "ten":     "Luật Công nghệ thông tin",
        "nam":     "2006",
        "loai":    "Luật",
    },
    "LuatVienThong2023": {
        "so_hieu": "24/2023/QH15",
        "ten":     "Luật Viễn thông",
        "nam":     "2023",
        "loai":    "Luật",
    },
}