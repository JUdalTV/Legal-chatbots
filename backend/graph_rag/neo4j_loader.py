"""
neo4j_loader.py
Toàn bộ thao tác Neo4j cho Legal Knowledge Graph.

Mọi node và edge đều đi qua class này.
Connection: bolt://localhost:7687 (default)
"""

from __future__ import annotations
from typing import Optional
from ontology import NodeLabel, EdgeType, CONSTRAINTS, FULLTEXT_INDEXES


class Neo4jLegalKG:

    def __init__(self, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError("pip install neo4j")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ── Schema setup ─────────────────────────────────────────────────

    def setup_schema(self):
        """Tạo constraints và full-text indexes."""
        with self.driver.session() as s:
            for stmt in CONSTRAINTS:
                s.run(stmt)
            for stmt in FULLTEXT_INDEXES:
                try:
                    s.run(stmt)
                except Exception as e:
                    print(f"  [WARN] Index: {e}")
        print("Schema đã tạo xong.")

    # ════════════════════════════════════════════════════════════════
    # STRUCTURAL NODES
    # ════════════════════════════════════════════════════════════════

    def upsert_van_ban(self, law_id: str, ten: str, so_hieu: str,
                       nam: str, loai: str):
        """VanBanPhapLuat node."""
        with self.driver.session() as s:
            s.run(f"""
                MERGE (v:{NodeLabel.VAN_BAN} {{id: $id}})
                SET v.ten      = $ten,
                    v.so_hieu  = $so_hieu,
                    v.nam      = $nam,
                    v.loai     = $loai,
                    v.hieu_luc = true
            """, id=law_id, ten=ten, so_hieu=so_hieu, nam=nam, loai=loai)

    def upsert_chuong(self, chuong_id: str, so: str, ten: str, law_id: str):
        """Chuong node + edge VanBan→Chuong."""
        with self.driver.session() as s:
            s.run(f"""
                MERGE (c:{NodeLabel.CHUONG} {{id: $id}})
                SET c.so  = $so,
                    c.ten = $ten
                WITH c
                MATCH (v:{NodeLabel.VAN_BAN} {{id: $law_id}})
                MERGE (v)-[:{EdgeType.CO_CHUONG}]->(c)
            """, id=chuong_id, so=so, ten=ten, law_id=law_id)

    def upsert_dieu_luat(self, dieu_id: str, so: str, ten: str,
                          noi_dung_tom: str, chuong_id: str, law_id: str,
                          amendment_type: Optional[str] = None):
        """
        DieuLuat node + edges:
          Chuong     → [:CO_DIEU] → DieuLuat
          VanBanPhapLuat → [:CO_DIEU] → DieuLuat  (shortcut)
        """
        with self.driver.session() as s:
            s.run(f"""
                MERGE (d:{NodeLabel.DIEU} {{id: $id}})
                SET d.so             = $so,
                    d.ten            = $ten,
                    d.noi_dung_tom   = $tom,
                    d.amendment_type = $amendment_type,
                    d.hieu_luc       = true
                WITH d
                MATCH (c:{NodeLabel.CHUONG} {{id: $chuong_id}})
                MERGE (c)-[:{EdgeType.CO_DIEU}]->(d)
                WITH d
                MATCH (v:{NodeLabel.VAN_BAN} {{id: $law_id}})
                MERGE (v)-[:{EdgeType.CO_DIEU}]->(d)
            """, id=dieu_id, so=so, ten=ten,
                 tom=noi_dung_tom[:400],
                 chuong_id=chuong_id, law_id=law_id,
                 amendment_type=amendment_type)

    def upsert_khoan_muc(self, khoan_id: str, so: str,
                          noi_dung: str, dieu_id: str):
        """KhoanMuc node + edge DieuLuat → KhoanMuc."""
        with self.driver.session() as s:
            s.run(f"""
                MERGE (k:{NodeLabel.KHOAN} {{id: $id}})
                SET k.so        = $so,
                    k.noi_dung  = $noi_dung
                WITH k
                MATCH (d:{NodeLabel.DIEU} {{id: $dieu_id}})
                MERGE (d)-[:{EdgeType.CO_KHOAN}]->(k)
            """, id=khoan_id, so=so,
                 noi_dung=noi_dung[:500], dieu_id=dieu_id)

    # ════════════════════════════════════════════════════════════════
    # SEMANTIC NODES (rule-based)
    # ════════════════════════════════════════════════════════════════

    def upsert_khai_niem(self, ten: str, dinh_nghia: str, dieu_id: str):
        """
        KhaiNiemPhapLy node + edge DieuLuat →[:DINH_NGHIA]→ KhaiNiem.
        """
        with self.driver.session() as s:
            s.run(f"""
                MERGE (kn:{NodeLabel.KHAI_NIEM} {{ten: $ten}})
                SET kn.dinh_nghia = $dinh_nghia
                WITH kn
                MATCH (d:{NodeLabel.DIEU} {{id: $dieu_id}})
                MERGE (d)-[:{EdgeType.DINH_NGHIA}]->(kn)
            """, ten=ten, dinh_nghia=dinh_nghia, dieu_id=dieu_id)

    def upsert_hanh_vi_bi_cam(self, ten: str, mo_ta: str, dieu_id: str):
        """
        HanhViBiCam node + edge DieuLuat →[:QUY_DINH_CAM]→ HanhVi.
        """
        with self.driver.session() as s:
            s.run(f"""
                MERGE (hv:{NodeLabel.HANH_VI_BI_CAM} {{ten: $ten}})
                SET hv.mo_ta = $mo_ta
                WITH hv
                MATCH (d:{NodeLabel.DIEU} {{id: $dieu_id}})
                MERGE (d)-[:{EdgeType.QUY_DINH_CAM}]->(hv)
            """, ten=ten, mo_ta=mo_ta, dieu_id=dieu_id)

    # ════════════════════════════════════════════════════════════════
    # ACTOR NODES (từ NER)
    # ════════════════════════════════════════════════════════════════

    def upsert_actor(self, ten: str, label: str, dieu_id: str):
        """
        Upsert Actor node (CoQuanNhaNuoc | DoanhNghiep |
        ToChucKhac | ChucDanh) và edge phù hợp.
        """
        edge_map = {
            NodeLabel.CO_QUAN:       EdgeType.GIAO_TRACH_NHIEM,
            NodeLabel.DOANH_NGHIEP:  EdgeType.AP_DUNG_VOI,
            NodeLabel.TO_CHUC_KHAC:  EdgeType.AP_DUNG_VOI,
            NodeLabel.CHUC_DANH:     EdgeType.GIAO_QUYEN_HAN,
        }
        edge = edge_map.get(label, EdgeType.AP_DUNG_VOI)

        with self.driver.session() as s:
            s.run(f"""
                MERGE (a:{label} {{ten: $ten}})
                WITH a
                MATCH (d:{NodeLabel.DIEU} {{id: $dieu_id}})
                MERGE (d)-[:{edge}]->(a)
            """, ten=ten, dieu_id=dieu_id)

    # ════════════════════════════════════════════════════════════════
    # RELATIONSHIP NODES
    # ════════════════════════════════════════════════════════════════

    def add_tham_chieu(self, from_id: str, to_id: str, context: str):
        """
        THAM_CHIEU edge giữa 2 DieuLuat.
        Chỉ tạo nếu cả 2 node tồn tại.
        """
        with self.driver.session() as s:
            s.run(f"""
                MATCH (a:{NodeLabel.DIEU} {{id: $from_id}})
                MATCH (b:{NodeLabel.DIEU} {{id: $to_id}})
                MERGE (a)-[r:{EdgeType.THAM_CHIEU}]->(b)
                SET r.context = $context
            """, from_id=from_id, to_id=to_id, context=context[:200])

    def add_lien_luat(self, from_law_id: str, to_so_hieu: str,
                       to_law_ten: str, rel_type: str):
        """
        BAI_BO hoặc SUA_DOI_BO_SUNG giữa VanBanPhapLuat.
        Tạo node luật liên quan nếu chưa có.
        """
        with self.driver.session() as s:
            s.run(f"""
                MATCH (a:{NodeLabel.VAN_BAN} {{id: $from_id}})
                MERGE (b:{NodeLabel.VAN_BAN} {{so_hieu: $so_hieu}})
                ON CREATE SET b.id     = $so_hieu,
                              b.ten    = $ten,
                              b.hieu_luc = false
                MERGE (a)-[:{rel_type}]->(b)
            """, from_id=from_law_id, so_hieu=to_so_hieu,
                 ten=to_law_ten, rel_type=rel_type)

    # ════════════════════════════════════════════════════════════════
    # ★ NEW: AMENDMENT-SPECIFIC METHODS
    # ════════════════════════════════════════════════════════════════

    def add_sua_doi_dieu(self, from_dieu_id: str, to_so_hieu: str,
                          to_dieu_so: str, context: str,
                          rel_type: str = "SUA_DOI_DIEU"):
        """
        Tạo edge sửa đổi cấp Điều.
        from_dieu_id: Điều đang thực hiện sửa đổi (VD: VT2023_dieu_71)
        to_so_hieu:   Số hiệu luật đích (VD: 67/2006/QH11)
        to_dieu_so:   Số Điều đích (VD: 76)
        rel_type:     SUA_DOI_DIEU | BAI_BO_DIEU | THAY_THE_CUM_TU
        """
        with self.driver.session() as s:
            # Tìm VanBan đích theo so_hieu
            # Tạo DieuLuat đích nếu chưa tồn tại (để có target cho edge)
            s.run(f"""
                MATCH (a:{NodeLabel.DIEU} {{id: $from_id}})
                MERGE (b_law:{NodeLabel.VAN_BAN} {{so_hieu: $to_so_hieu}})
                ON CREATE SET b_law.id = $to_so_hieu, b_law.hieu_luc = false
                WITH a, b_law
                MERGE (b:{NodeLabel.DIEU} {{id: $to_dieu_id}})
                ON CREATE SET b.so  = $to_dieu_so,
                              b.ten = 'Điều ' + $to_dieu_so,
                              b.hieu_luc = true
                MERGE (b_law)-[:{EdgeType.CO_DIEU}]->(b)
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.context    = $context,
                    r.so_hieu_dich = $to_so_hieu
            """, from_id=from_dieu_id,
                 to_so_hieu=to_so_hieu,
                 to_dieu_id=f"{to_so_hieu}_dieu_{to_dieu_so}",
                 to_dieu_so=to_dieu_so,
                 context=context[:300],
                 rel_type=rel_type)

    def mark_dieu_bai_bo(self, dieu_id: str):
        """Đánh dấu Điều đã bị bãi bỏ (hieu_luc = false)."""
        with self.driver.session() as s:
            s.run(f"""
                MATCH (d:{NodeLabel.DIEU} {{id: $id}})
                SET d.hieu_luc = false
            """, id=dieu_id)

    def mark_van_ban_het_hieu_luc(self, so_hieu: str, law_ten: str):
        """
        Đánh dấu VanBanPhapLuat hết hiệu lực.
        Tạo node nếu chưa tồn tại.
        """
        with self.driver.session() as s:
            s.run(f"""
                MERGE (v:{NodeLabel.VAN_BAN} {{so_hieu: $so_hieu}})
                ON CREATE SET v.id  = $so_hieu,
                              v.ten = $ten
                SET v.hieu_luc = false
            """, so_hieu=so_hieu, ten=law_ten)

    def add_bai_bo_van_ban(self, from_law_id: str, to_so_hieu: str,
                            to_law_ten: str):
        """
        Tạo edge BAI_BO giữa VanBan mới → VanBan cũ (hết hiệu lực).
        """
        with self.driver.session() as s:
            s.run(f"""
                MATCH (a:{NodeLabel.VAN_BAN} {{id: $from_id}})
                MERGE (b:{NodeLabel.VAN_BAN} {{so_hieu: $so_hieu}})
                ON CREATE SET b.id     = $so_hieu,
                              b.ten    = $ten
                SET b.hieu_luc = false
                MERGE (a)-[:{EdgeType.BAI_BO}]->(b)
            """, from_id=from_law_id, so_hieu=to_so_hieu, ten=to_law_ten)

    # ════════════════════════════════════════════════════════════════
    # QUERY HELPERS (dùng trong graph_retriever)
    # ════════════════════════════════════════════════════════════════

    def get_dieu_with_neighbors(self, dieu_id: str) -> dict:
        """
        Lấy DieuLuat + tất cả node liên quan (1 hop).
        Bao gồm cả thông tin sửa đổi/bãi bỏ.
        Dùng cho Graph RAG context generation.
        """
        with self.driver.session() as s:
            result = s.run(f"""
                MATCH (d:{NodeLabel.DIEU} {{id: $id}})
                OPTIONAL MATCH (d)-[r1:{EdgeType.THAM_CHIEU}]->(d2:{NodeLabel.DIEU})
                OPTIONAL MATCH (d)-[r2:{EdgeType.DINH_NGHIA}]->(kn:{NodeLabel.KHAI_NIEM})
                OPTIONAL MATCH (d)-[r3:{EdgeType.QUY_DINH_CAM}]->(hv:{NodeLabel.HANH_VI_BI_CAM})
                OPTIONAL MATCH (d)-[r4:{EdgeType.GIAO_TRACH_NHIEM}]->(cq:{NodeLabel.CO_QUAN})
                OPTIONAL MATCH (d)-[r5:{EdgeType.AP_DUNG_VOI}]->(dn)
                OPTIONAL MATCH (d)-[r6:{EdgeType.SUA_DOI_DIEU}|{EdgeType.BAI_BO_DIEU}|{EdgeType.THAY_THE_CUM_TU}]->(d_amended:{NodeLabel.DIEU})
                OPTIONAL MATCH (d)<-[r7:{EdgeType.SUA_DOI_DIEU}|{EdgeType.BAI_BO_DIEU}|{EdgeType.THAY_THE_CUM_TU}]-(d_amender:{NodeLabel.DIEU})
                RETURN d,
                       collect(DISTINCT d2.ten)  AS tham_chieu,
                       collect(DISTINCT kn.ten)  AS khai_niem,
                       collect(DISTINCT hv.ten)  AS hanh_vi_cam,
                       collect(DISTINCT cq.ten)  AS co_quan,
                       collect(DISTINCT dn.ten)  AS doi_tuong,
                       collect(DISTINCT d_amended.id)  AS sua_doi_dieu,
                       collect(DISTINCT d_amender.id)  AS bi_sua_doi_boi
            """, id=dieu_id)

            row = result.single()
            if not row:
                return {}

            d = row["d"]
            return {
                "id":              d["id"],
                "so":              d["so"],
                "ten":             d["ten"],
                "noi_dung_tom":    d.get("noi_dung_tom", ""),
                "amendment_type":  d.get("amendment_type"),
                "hieu_luc":        d.get("hieu_luc", True),
                "tham_chieu":      [x for x in row["tham_chieu"] if x],
                "khai_niem":       [x for x in row["khai_niem"]  if x],
                "hanh_vi_cam":     [x for x in row["hanh_vi_cam"] if x],
                "co_quan":         [x for x in row["co_quan"]    if x],
                "doi_tuong":       [x for x in row["doi_tuong"]  if x],
                "sua_doi_dieu":    [x for x in row["sua_doi_dieu"] if x],
                "bi_sua_doi_boi":  [x for x in row["bi_sua_doi_boi"] if x],
            }

    def search_fulltext(self, query: str, limit: int = 5) -> list[dict]:
        """Full-text search trên DieuLuat."""
        with self.driver.session() as s:
            result = s.run("""
                CALL db.index.fulltext.queryNodes('dieu_fts', $query)
                YIELD node, score
                RETURN node.id AS id, node.so AS so,
                       node.ten AS ten, node.noi_dung_tom AS tom,
                       score
                ORDER BY score DESC LIMIT $limit
            """, query=query, limit=limit)
            return [dict(r) for r in result]

    def get_stats(self) -> dict:
        """Thống kê số node theo label."""
        stats = {}
        labels = [
            NodeLabel.VAN_BAN, NodeLabel.CHUONG, NodeLabel.DIEU,
            NodeLabel.KHOAN, NodeLabel.KHAI_NIEM, NodeLabel.HANH_VI_BI_CAM,
            NodeLabel.CO_QUAN, NodeLabel.DOANH_NGHIEP,
            NodeLabel.TO_CHUC_KHAC, NodeLabel.CHUC_DANH,
        ]
        with self.driver.session() as s:
            for label in labels:
                r = s.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                stats[label] = r.single()["cnt"]
        return stats

    def get_amendment_stats(self) -> dict:
        """★ NEW: Thống kê sửa đổi/bãi bỏ."""
        with self.driver.session() as s:
            result = s.run(f"""
                MATCH (d:{NodeLabel.DIEU})
                WHERE d.amendment_type IS NOT NULL
                RETURN d.amendment_type AS type, count(d) AS cnt
                ORDER BY cnt DESC
            """)
            stats = {row["type"]: row["cnt"] for row in result}

            # Đếm edges sửa đổi
            for rel_type in [EdgeType.SUA_DOI_DIEU, EdgeType.BAI_BO_DIEU, EdgeType.THAY_THE_CUM_TU]:
                r = s.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt")
                stats[f"edge_{rel_type}"] = r.single()["cnt"]

            # Đếm VanBan hết hiệu lực
            r = s.run(f"MATCH (v:{NodeLabel.VAN_BAN}) WHERE v.hieu_luc = false RETURN count(v) AS cnt")
            stats["van_ban_het_hieu_luc"] = r.single()["cnt"]

        return stats