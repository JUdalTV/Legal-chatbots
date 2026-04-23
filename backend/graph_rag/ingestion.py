"""
graph_rag/ingestion.py
Pipeline hoàn chỉnh cho Knowledge Graph:
  docx → extract → clean → chunk → NER + Rule → upsert Neo4j

Bao gồm:
  - Nạp cấu trúc: VanBan → Chuong → DieuLuat → KhoanMuc
  - Nạp nội dung:  KhaiNiemPhapLy, HanhViBiCam, Actor
  - Nạp liên kết:  THAM_CHIEU, LIEN_LUAT
  - ★ NEW: Nạp sửa đổi chi tiết cấp Điều + hiệu lực + chuyển tiếp

Chạy:
  python ingestion.py
"""

import os
import sys
import json
from pathlib import Path

# Thêm vector_rag vào sys.path để tái dụng extractor + chunker
sys.path.insert(0, str(Path(__file__).parent.parent / "vector_rag"))

from extractor import extract_docx, clean_text
from chunker import chunk_law, LawChunk
from ner_extractor import get_ner_extractor
from rule_extractors import (
    extract_khai_niem,
    extract_hanh_vi_bi_cam,
    extract_references,
    extract_lien_luat,
    extract_sua_doi_chi_tiet,
    extract_chuyen_tiep,
)
from neo4j_loader import Neo4jLegalKG
from ontology import (
    GIAI_THICH_DIEU,
    NGHIEM_CAM_DIEU,
    LIEN_LUAT_DIEU,
    SUA_DOI_DIEU,
    HIEU_LUC_DIEU,
    CHUYEN_TIEP_DIEU,
    VAN_BAN_META,
)

# ── Cấu hình ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent

RAW_FILES = {
    "LuatAnNinhMang2025": BASE_DIR / "data" / "raw" / "luatanm2025.docx",
    "LuatCNTT2006":       BASE_DIR / "data" / "raw" / "luatcntt2006.docx",
    "LuatVienThong2023":  BASE_DIR / "data" / "raw" / "luatvienthong2023.docx",
}

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

# Bật/tắt NER (tốn thời gian load model)
USE_NER = os.getenv("USE_NER", "true").lower() == "true"


def _make_chuong_id(law_name: str, chuong_so: str) -> str:
    return f"{law_name}_chuong_{chuong_so}"


def _is_giai_thich_dieu(law_name: str, dieu_so: str) -> bool:
    return GIAI_THICH_DIEU.get(law_name) == dieu_so


def _is_nghiem_cam_dieu(law_name: str, dieu_so: str) -> bool:
    return NGHIEM_CAM_DIEU.get(law_name) == dieu_so


def _is_lien_luat_dieu(law_name: str, dieu_so: str) -> bool:
    return dieu_so in LIEN_LUAT_DIEU.get(law_name, [])


def _is_sua_doi_dieu(law_name: str, dieu_so: str) -> bool:
    return dieu_so in SUA_DOI_DIEU.get(law_name, [])


def _is_hieu_luc_dieu(law_name: str, dieu_so: str) -> bool:
    return dieu_so in HIEU_LUC_DIEU.get(law_name, [])


def _is_chuyen_tiep_dieu(law_name: str, dieu_so: str) -> bool:
    return dieu_so in CHUYEN_TIEP_DIEU.get(law_name, [])


def run_ingestion():
    """Chạy toàn bộ pipeline Graph RAG ingestion."""

    # 1. Kết nối Neo4j
    print(f"Kết nối Neo4j: {NEO4J_URI}")
    kg = Neo4jLegalKG(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    kg.setup_schema()

    # 2. NER extractor (lazy load)
    ner = get_ner_extractor() if USE_NER else None

    # 3. Xử lý từng luật
    for law_name, file_path in RAW_FILES.items():
        if not file_path.exists():
            print(f"\n[WARN] Không tìm thấy: {file_path}, bỏ qua.")
            continue

        meta = VAN_BAN_META[law_name]
        print(f"\n{'='*55}")
        print(f"Processing KG: {law_name}  ({meta['so_hieu']})")

        # Extract + clean text
        raw   = extract_docx(str(file_path))
        clean = clean_text(raw)

        # Chunk theo cấu trúc Chương/Điều/Khoản
        chunks: list[LawChunk] = chunk_law(clean, law_name)
        print(f"  Chunks: {len(chunks)} "
              f"(dieu={sum(1 for c in chunks if c.chunk_type=='dieu')}, "
              f"khoan={sum(1 for c in chunks if c.chunk_type=='khoan')})")

        # Thống kê amendment
        amend_count = sum(1 for c in chunks if c.amendment_type and c.chunk_type == 'dieu')
        if amend_count:
            print(f"  Amendment Điều: {amend_count}")

        # ── A. VanBanPhapLuat node ───────────────────────────────
        kg.upsert_van_ban(
            law_id=law_name,
            ten=meta["ten"],
            so_hieu=meta["so_hieu"],
            nam=meta["nam"],
            loai=meta["loai"],
        )

        # Track Chương đã tạo
        seen_chuong: set[str] = set()

        # ── B. Duyệt qua chunks ──────────────────────────────────
        for chunk in chunks:
            # Chỉ xử lý chunk cấp DIEU để nạp KG
            # (khoan chunk chỉ dành cho Vector RAG)
            if chunk.chunk_type != "dieu":
                continue

            dieu_id   = chunk.neo4j_id
            chuong_id = _make_chuong_id(law_name, chunk.chuong_so)

            # ── B1. Chuong node ──────────────────────────────────
            if chuong_id not in seen_chuong:
                kg.upsert_chuong(
                    chuong_id=chuong_id,
                    so=chunk.chuong_so,
                    ten=chunk.chuong_ten,
                    law_id=law_name,
                )
                seen_chuong.add(chuong_id)

            # ── B2. DieuLuat node ────────────────────────────────
            kg.upsert_dieu_luat(
                dieu_id=dieu_id,
                so=chunk.dieu_so,
                ten=chunk.dieu_ten,
                noi_dung_tom=chunk.content,
                chuong_id=chuong_id,
                law_id=law_name,
                amendment_type=chunk.amendment_type,
            )

            # ── B3. KhoanMuc nodes (từ chunk khoan cùng Điều) ───
            # Tìm các chunk khoản tương ứng
            # (được chunk bởi chunker.py khi Điều > 600 ký tự)

            # ── B4. Rule: KhaiNiemPhapLy ─────────────────────────
            if _is_giai_thich_dieu(law_name, chunk.dieu_so):
                kns = extract_khai_niem(chunk.content, dieu_id)
                for kn in kns:
                    kg.upsert_khai_niem(
                        ten=kn["ten"],
                        dinh_nghia=kn["dinh_nghia"],
                        dieu_id=dieu_id,
                    )
                print(f"  [{chunk.dieu_so}] KhaiNiem: {len(kns)} khái niệm")

            # ── B5. Rule: HanhViBiCam ────────────────────────────
            if _is_nghiem_cam_dieu(law_name, chunk.dieu_so):
                hvs = extract_hanh_vi_bi_cam(chunk.content, dieu_id)
                for hv in hvs:
                    kg.upsert_hanh_vi_bi_cam(
                        ten=hv["ten"],
                        mo_ta=hv["mo_ta"],
                        dieu_id=dieu_id,
                    )
                print(f"  [{chunk.dieu_so}] HanhViBiCam: {len(hvs)} hành vi")

            # ── B6. Rule: THAM_CHIEU ─────────────────────────────
            refs = extract_references(chunk.content, chunk.dieu_so, law_name)
            for ref in refs:
                kg.add_tham_chieu(
                    from_id=ref["from_id"],
                    to_id=ref["to_id"],
                    context=ref["context"],
                )

            # ── B7. Rule: quan hệ liên luật ──────────────────────
            if _is_lien_luat_dieu(law_name, chunk.dieu_so):
                rels = extract_lien_luat(chunk.content, law_name)
                for rel in rels:
                    kg.add_lien_luat(
                        from_law_id=law_name,
                        to_so_hieu=rel["to_so_hieu"],
                        to_law_ten=rel["to_law_ten"],
                        rel_type=rel["rel_type"],
                    )
                if rels:
                    print(f"  [{chunk.dieu_so}] LienLuat: {len(rels)} quan hệ")

            # ── B8. NER: Actor nodes ─────────────────────────────
            if ner is not None:
                actors = ner.extract_actors(chunk.content, dieu_id)
                for actor in actors:
                    kg.upsert_actor(
                        ten=actor["text"],
                        label=actor["label"],
                        dieu_id=dieu_id,
                    )

            # ══════════════════════════════════════════════════════
            # ★ NEW: B9. Sửa đổi chi tiết cấp Điều
            # ══════════════════════════════════════════════════════
            if _is_sua_doi_dieu(law_name, chunk.dieu_so):
                sua_doi_items = extract_sua_doi_chi_tiet(
                    chunk.content, dieu_id, law_name
                )
                for item in sua_doi_items:
                    if item["type"] == "thay_cum_tu" and item.get("to_dieu_so"):
                        kg.add_sua_doi_dieu(
                            from_dieu_id=dieu_id,
                            to_so_hieu=item["to_so_hieu"],
                            to_dieu_so=item["to_dieu_so"],
                            context=f"Thay '{item.get('cum_tu_cu', '')}' → '{item.get('cum_tu_moi', '')}'",
                            rel_type="THAY_THE_CUM_TU",
                        )
                    elif item["type"] == "bai_bo_dieu" and item.get("to_dieu_so"):
                        kg.add_sua_doi_dieu(
                            from_dieu_id=dieu_id,
                            to_so_hieu=item.get("to_so_hieu", ""),
                            to_dieu_so=item["to_dieu_so"],
                            context=item.get("context", ""),
                            rel_type="BAI_BO_DIEU",
                        )
                        # Đánh dấu Điều bị bãi bỏ hết hiệu lực
                        if item.get("to_so_hieu"):
                            target_id = f"{item['to_so_hieu']}_dieu_{item['to_dieu_so']}"
                            kg.mark_dieu_bai_bo(target_id)
                    elif item["type"] == "sua_doi_dieu" and item.get("to_dieu_so"):
                        kg.add_sua_doi_dieu(
                            from_dieu_id=dieu_id,
                            to_so_hieu=item["to_so_hieu"],
                            to_dieu_so=item["to_dieu_so"],
                            context=item.get("context", ""),
                            rel_type="SUA_DOI_DIEU",
                        )
                    elif item["type"] == "het_hieu_luc":
                        # Đánh dấu VanBan cũ hết hiệu lực
                        kg.mark_van_ban_het_hieu_luc(
                            so_hieu=item["to_so_hieu"],
                            law_ten=item.get("to_law_ten", ""),
                        )
                        kg.add_bai_bo_van_ban(
                            from_law_id=law_name,
                            to_so_hieu=item["to_so_hieu"],
                            to_law_ten=item.get("to_law_ten", ""),
                        )

                if sua_doi_items:
                    print(f"  [{chunk.dieu_so}] SuaDoiChiTiet: "
                          f"{len(sua_doi_items)} mục "
                          f"({', '.join(set(i['type'] for i in sua_doi_items))})")

            # ══════════════════════════════════════════════════════
            # ★ NEW: B10. Hiệu lực thi hành
            # ══════════════════════════════════════════════════════
            if _is_hieu_luc_dieu(law_name, chunk.dieu_so):
                hieu_luc_items = extract_sua_doi_chi_tiet(
                    chunk.content, dieu_id, law_name
                )
                for item in hieu_luc_items:
                    if item["type"] == "het_hieu_luc":
                        kg.mark_van_ban_het_hieu_luc(
                            so_hieu=item["to_so_hieu"],
                            law_ten=item.get("to_law_ten", ""),
                        )
                        kg.add_bai_bo_van_ban(
                            from_law_id=law_name,
                            to_so_hieu=item["to_so_hieu"],
                            to_law_ten=item.get("to_law_ten", ""),
                        )

                if hieu_luc_items:
                    het_hl = [i for i in hieu_luc_items if i["type"] == "het_hieu_luc"]
                    if het_hl:
                        print(f"  [{chunk.dieu_so}] HieuLuc: "
                              f"{len(het_hl)} luật hết hiệu lực")

            # ══════════════════════════════════════════════════════
            # ★ NEW: B11. Quy định chuyển tiếp
            # ══════════════════════════════════════════════════════
            if _is_chuyen_tiep_dieu(law_name, chunk.dieu_so):
                ct_items = extract_chuyen_tiep(chunk.content, dieu_id)
                if ct_items:
                    print(f"  [{chunk.dieu_so}] ChuyenTiep: "
                          f"{len(ct_items)} quy định")
                    # Lưu liên kết tham chiếu đến các luật liên quan
                    for ct in ct_items:
                        for so_hieu in ct.get("affected_so_hieu", []):
                            kg.add_lien_luat(
                                from_law_id=law_name,
                                to_so_hieu=so_hieu,
                                to_law_ten="",
                                rel_type="SUA_DOI_BO_SUNG",
                            )

    # 4. Nạp KhoanMuc riêng (từ chunks khoan)
    print("\n--- Nạp KhoanMuc nodes ---")
    for law_name, file_path in RAW_FILES.items():
        if not file_path.exists():
            continue
        raw   = extract_docx(str(file_path))
        clean = clean_text(raw)
        chunks = chunk_law(clean, law_name)

        khoan_chunks = [c for c in chunks if c.chunk_type == "khoan"]
        for chunk in khoan_chunks:
            khoan_id = chunk.chunk_id
            kg.upsert_khoan_muc(
                khoan_id=khoan_id,
                so=chunk.khoan_so,
                noi_dung=chunk.content,
                dieu_id=chunk.neo4j_id,
            )
        print(f"  {law_name}: {len(khoan_chunks)} khoản")

    # 5. Thống kê
    print("\n✅ Knowledge Graph ingestion hoàn tất!")
    stats = kg.get_stats()
    for label, count in stats.items():
        print(f"  {label:<25}: {count:>5} nodes")

    # ★ NEW: Thống kê sửa đổi
    print("\n── Thống kê Sửa đổi/Bổ sung ──")
    try:
        amend_stats = kg.get_amendment_stats()
        for key, count in amend_stats.items():
            print(f"  {key:<30}: {count:>5}")
    except Exception as e:
        print(f"  [WARN] Không lấy được amendment stats: {e}")

    kg.close()


if __name__ == "__main__":
    run_ingestion()