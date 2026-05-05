"""
graph_retriever.py — Truy vấn KG cho Graph RAG (schema ontology v1.0).

Đầu vào: list ARTICLE id (vd 'LuatAnNinhMang2025_dieu_15') từ Vector RAG.
Đầu ra: context string đã format cho LLM.

Subgraph 1-hop quanh ARTICLE:
  - Cấu trúc: LAW, CHAPTER, CLAUSE
  - Quan hệ: REFERS_TO ↔ ARTICLE
  - Entities được mention trong điều: MENTIONS → (LEGAL_ACTOR, DATA, ...)
  - Edge ngữ nghĩa nội bộ: lấy các edge có article_id = current
"""
from __future__ import annotations

from .neo4j_loader import Neo4jKG


class GraphRetriever:
    def __init__(self, kg: Neo4jKG):
        self.kg = kg

    # ----------------------------------------------------------------
    def retrieve_context(self, article_ids: list[str]) -> str:
        if not article_ids:
            return ""
        seen, unique = set(), []
        for aid in article_ids:
            if aid in seen:
                continue
            seen.add(aid)
            unique.append(aid)

        parts = [self._format(aid) for aid in unique]
        return "\n\n---\n\n".join(p for p in parts if p)

    # ----------------------------------------------------------------
    def _format(self, article_id: str) -> str:
        with self.kg.driver.session() as s:
            row = s.run(
                """
                MATCH (a:ARTICLE {id: $aid})
                OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(a)
                OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(k:CLAUSE)
                OPTIONAL MATCH (a)-[:REFERS_TO]->(r:ARTICLE)
                OPTIONAL MATCH (a)-[:MENTIONS]->(ent)
                RETURN a, l.label AS law,
                       collect(DISTINCT k.content) AS clauses,
                       collect(DISTINCT r.id)      AS refs,
                       collect(DISTINCT {label: ent.label, type: labels(ent)[0]}) AS entities
                """,
                aid=article_id,
            ).single()
            if not row or not row["a"]:
                return ""

            edges = list(s.run(
                """
                MATCH (a)-[r]->(b)
                WHERE r.article_id = $aid OR $aid IN coalesce(r.article_ids, [])
                RETURN a.label AS frm, type(r) AS rtype,
                       r.modality AS modality,
                       r.condition AS condition, r.exception AS exception,
                       r.scope AS scope, r.time AS time,
                       b.label AS to
                LIMIT 30
                """,
                aid=article_id,
            ))

        a = row["a"]
        lines = [f"[{row['law']}] Điều {a['so']}. {a['label']}"]
        if not a.get("hieu_luc", True):
            lines.append("⚠️ ĐIỀU NÀY ĐÃ HẾT HIỆU LỰC")
        if a.get("amendment_type"):
            lines.append(f"[loại: {a['amendment_type']}]")

        clauses = [c for c in row["clauses"] if c]
        if clauses:
            lines.append("Khoản:")
            for c in clauses[:10]:
                lines.append(f"  • {c[:300]}")

        ents = [e for e in row["entities"] if e and e.get("label")]
        if ents:
            grouped: dict[str, list[str]] = {}
            for e in ents:
                grouped.setdefault(e["type"], []).append(e["label"])
            lines.append("Thực thể được nhắc:")
            for t, labels in grouped.items():
                lines.append(f"  • {t}: {', '.join(sorted(set(labels))[:6])}")

        if edges:
            lines.append("Quan hệ trong Điều:")
            for e in edges:
                tag = ""
                attrs = [
                    f"modality={e['modality']}" if e.get("modality") else None,
                    f"điều_kiện='{e['condition']}'" if e.get("condition") else None,
                    f"ngoại_lệ='{e['exception']}'" if e.get("exception") else None,
                    f"phạm_vi='{e['scope']}'" if e.get("scope") else None,
                    f"thời_hạn='{e['time']}'" if e.get("time") else None,
                ]
                attrs = [a for a in attrs if a]
                if attrs:
                    tag = "  [" + " ".join(attrs) + "]"
                lines.append(f"  • {e['frm']} —{e['rtype']}→ {e['to']}{tag}")

        refs = [r for r in row["refs"] if r]
        if refs:
            lines.append(f"Tham chiếu đến: {', '.join(refs[:6])}")

        return "\n".join(lines)
