"""
graph_rag/graph_retriever.py
Truy vấn Knowledge Graph để lấy context cho Graph RAG.

Luồng:
  1. Nhận neo4j_ids từ Vector RAG (top-k chunks)
  2. Với mỗi DieuLuat → lấy subgraph 1-hop
  3. Format thành context string cho LLM
  4. ★ Bao gồm thông tin sửa đổi/bãi bỏ/chuyển tiếp
"""

from __future__ import annotations
from neo4j_loader import Neo4jLegalKG


class GraphRetriever:

    def __init__(self, kg: Neo4jLegalKG):
        self.kg = kg

    def retrieve_context(self, neo4j_ids: list[str]) -> str:
        """
        Nhận list neo4j_id (DieuLuat IDs từ Qdrant payload),
        truy vấn Neo4j lấy subgraph context.
        Trả về context string cho LLM.
        """
        if not neo4j_ids:
            return ""

        # Dedup và giữ thứ tự
        seen: set[str] = set()
        unique_ids = []
        for nid in neo4j_ids:
            if nid not in seen:
                seen.add(nid)
                unique_ids.append(nid)

        parts = []
        for dieu_id in unique_ids:
            node_data = self.kg.get_dieu_with_neighbors(dieu_id)
            if not node_data:
                continue
            parts.append(self._format_node(node_data))

        return "\n\n".join(parts)

    def _format_node(self, data: dict) -> str:
        """Format subgraph data thành text dễ đọc cho LLM."""
        lines = [f"Điều {data['so']}. {data['ten']}"]

        # ★ NEW: Thông tin hiệu lực
        if not data.get("hieu_luc", True):
            lines.append("⚠️ ĐIỀU NÀY ĐÃ BỊ BÃI BỎ / HẾT HIỆU LỰC")

        # ★ NEW: Loại Điều sửa đổi
        amendment_type = data.get("amendment_type")
        if amendment_type:
            amend_labels = {
                "sua_doi":     "Điều sửa đổi, bổ sung",
                "bai_bo":      "Điều bãi bỏ",
                "hieu_luc":    "Điều hiệu lực thi hành",
                "chuyen_tiep": "Điều quy định chuyển tiếp",
            }
            label = amend_labels.get(amendment_type, amendment_type)
            lines.append(f"[Loại: {label}]")

        if data.get("noi_dung_tom"):
            lines.append(f"Nội dung: {data['noi_dung_tom'][:300]}")

        if data.get("khai_niem"):
            lines.append(f"Khái niệm liên quan: {', '.join(data['khai_niem'][:5])}")

        if data.get("hanh_vi_cam"):
            lines.append(f"Hành vi bị cấm: {'; '.join(data['hanh_vi_cam'][:3])}")

        if data.get("co_quan"):
            lines.append(f"Cơ quan thực hiện: {', '.join(data['co_quan'][:4])}")

        if data.get("doi_tuong"):
            lines.append(f"Áp dụng với: {', '.join(data['doi_tuong'][:4])}")

        if data.get("tham_chieu"):
            lines.append(f"Tham chiếu: {', '.join(data['tham_chieu'][:4])}")

        # ★ NEW: Quan hệ sửa đổi cấp Điều
        if data.get("sua_doi_dieu"):
            lines.append(f"Sửa đổi/bãi bỏ các điều: {', '.join(data['sua_doi_dieu'][:5])}")

        if data.get("bi_sua_doi_boi"):
            lines.append(f"Đã bị sửa đổi bởi: {', '.join(data['bi_sua_doi_boi'][:5])}")

        return "\n".join(lines)

    def traverse_references(self, dieu_id: str, depth: int = 2) -> list[dict]:
        """
        Duyệt các Điều tham chiếu theo chiều sâu.
        Dùng cho multi-hop reasoning.
        """
        visited: set[str] = set()
        result: list[dict] = []

        def _dfs(nid: str, current_depth: int):
            if current_depth > depth or nid in visited:
                return
            visited.add(nid)

            node = self.kg.get_dieu_with_neighbors(nid)
            if not node:
                return
            result.append(node)

            for ref_ten in node.get("tham_chieu", []):
                # Tìm ID từ tên (đơn giản hóa)
                # Trong thực tế cần query Neo4j thêm
                pass

        _dfs(dieu_id, 0)
        return result