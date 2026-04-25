"""
neo4j_loader.py — Toàn bộ thao tác Neo4j cho Legal KG (ontology v1.0).

Schema: label = NODE TYPE từ ontology (LAW, ARTICLE, CLAUSE, LEGAL_ACTOR, ...).
Mỗi node có:
  .id      (string, unique)
  .label   (text hiển thị, tiếng Việt)
  .layer   ('structural'|'normative'|'governance'|'system'|'cyber'|'telecom'|'it')
  + properties tuỳ kiểu

Edge:
  .type    đặt làm relationship type trong Cypher
  .modality, .condition, .exception, .scope, .time, .status, .classification, .level
  .evidence
  .source  ('llm' | 'rule')
  .article_id (id của ARTICLE chứa quan hệ — để truy nguồn)
  .sentence_idx
"""
from __future__ import annotations

import re
from typing import Optional

from .ontology import (
    ALL_RELATION_TYPES, CONSTRAINTS, FULLTEXT_INDEXES,
    LAYER_OF, get_layer,
)


# Cypher relationship types phải là identifier hợp lệ.
_REL_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_NODE_LABEL_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _safe_rel(t: str) -> str:
    if not _REL_TYPE_RE.match(t):
        raise ValueError(f"Invalid relationship type: {t!r}")
    return t


def _safe_label(t: str) -> str:
    if not _NODE_LABEL_RE.match(t):
        raise ValueError(f"Invalid node label: {t!r}")
    return t


class Neo4jKG:
    def __init__(self, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError("pip install neo4j")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ════════════════════════════════════════════════════════════════
    # Schema lifecycle
    # ════════════════════════════════════════════════════════════════
    def wipe(self):
        """DELETE toàn bộ graph (nodes + edges + indexes)."""
        with self.driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")
            # drop fulltext indexes (ignore lỗi nếu chưa tồn tại)
            for name in ("article_fts", "clause_fts", "entity_fts"):
                try:
                    s.run(f"DROP INDEX {name} IF EXISTS")
                except Exception:
                    pass
        print("[neo4j] Wiped all nodes/edges.")

    def setup_schema(self):
        with self.driver.session() as s:
            for stmt in CONSTRAINTS:
                s.run(stmt)
            for stmt in FULLTEXT_INDEXES:
                try:
                    s.run(stmt)
                except Exception as e:
                    print(f"  [WARN] Index: {e}")
        print("[neo4j] Schema constraints + indexes created.")

    # ════════════════════════════════════════════════════════════════
    # Structural nodes (Layer 1)
    # ════════════════════════════════════════════════════════════════
    def upsert_law(self, law_id: str, ten: str, so_hieu: str,
                   nam: str, loai: str):
        with self.driver.session() as s:
            s.run("""
                MERGE (l:LAW {id: $id})
                SET l.label    = $ten,
                    l.so_hieu  = $so_hieu,
                    l.nam      = $nam,
                    l.loai     = $loai,
                    l.layer    = 'structural',
                    l.hieu_luc = true
            """, id=law_id, ten=ten, so_hieu=so_hieu, nam=nam, loai=loai)

    def upsert_chapter(self, chapter_id: str, so: str, ten: str, law_id: str):
        with self.driver.session() as s:
            s.run("""
                MERGE (c:CHAPTER {id: $id})
                SET c.label = $ten, c.so = $so, c.layer = 'structural'
                WITH c
                MATCH (l:LAW {id: $law_id})
                MERGE (l)-[:HAS_CHAPTER]->(c)
            """, id=chapter_id, so=so, ten=ten, law_id=law_id)

    def upsert_article(self, article_id: str, so: str, ten: str,
                       content: str, chapter_id: str, law_id: str,
                       amendment_type: Optional[str] = None):
        with self.driver.session() as s:
            s.run("""
                MERGE (a:ARTICLE {id: $id})
                SET a.label          = $ten,
                    a.so             = $so,
                    a.content        = $content,
                    a.amendment_type = $amend,
                    a.layer          = 'structural',
                    a.hieu_luc       = true
                WITH a
                MATCH (c:CHAPTER {id: $chapter_id})
                MERGE (c)-[:HAS_ARTICLE]->(a)
                WITH a
                MATCH (l:LAW {id: $law_id})
                MERGE (l)-[:HAS_ARTICLE]->(a)
            """, id=article_id, so=so, ten=ten,
                 content=content[:2000], amend=amendment_type,
                 chapter_id=chapter_id, law_id=law_id)

    def upsert_clause(self, clause_id: str, so: str, content: str,
                      article_id: str):
        with self.driver.session() as s:
            s.run("""
                MERGE (k:CLAUSE {id: $id})
                SET k.label   = 'Khoản ' + $so,
                    k.so      = $so,
                    k.content = $content,
                    k.layer   = 'structural'
                WITH k
                MATCH (a:ARTICLE {id: $article_id})
                MERGE (a)-[:HAS_CLAUSE]->(k)
            """, id=clause_id, so=so, content=content[:1500],
                 article_id=article_id)

    # ════════════════════════════════════════════════════════════════
    # Entity nodes (L2 normative-as-node, L4 license/cert, L5, domain)
    # ════════════════════════════════════════════════════════════════
    def upsert_entity(self, node_id: str, etype: str, label: str,
                      *, article_id: Optional[str] = None,
                      clause_id:   Optional[str] = None,
                      sentence_idx: Optional[int] = None,
                      score: Optional[float] = None,
                      subclass: Optional[str] = None,
                      source: str = "ner"):
        """
        Upsert 1 entity node.
        - Tạo edge MENTIONS từ ARTICLE/CLAUSE → entity để truy nguồn.
        """
        lbl = _safe_label(etype)
        layer = get_layer(etype)
        with self.driver.session() as s:
            s.run(f"""
                MERGE (n:{lbl} {{id: $id}})
                SET n.label    = $label,
                    n.layer    = $layer,
                    n.subclass = coalesce($subclass, n.subclass),
                    n.score    = coalesce($score, n.score),
                    n.source   = coalesce($source, n.source)
            """, id=node_id, label=label, layer=layer,
                 subclass=subclass, score=score, source=source)

            anchor_id = clause_id or article_id
            if anchor_id:
                # Anchor có thể là CLAUSE hoặc ARTICLE → MATCH bằng id (cả 2 label đều unique)
                s.run(f"""
                    MATCH (anchor) WHERE anchor.id = $anchor
                    MATCH (n:{lbl} {{id: $id}})
                    MERGE (anchor)-[m:MENTIONS]->(n)
                    SET  m.sentence_idx = $sidx
                """, anchor=anchor_id, id=node_id, sidx=sentence_idx)

    # ════════════════════════════════════════════════════════════════
    # Edges from LLM extraction
    # ════════════════════════════════════════════════════════════════
    def upsert_edge(self, from_id: str, to_id: str, rel_type: str,
                    *, modality: Optional[str] = None,
                    condition: Optional[str] = None,
                    exception: Optional[str] = None,
                    scope:     Optional[str] = None,
                    time:      Optional[str] = None,
                    status:    Optional[str] = None,
                    classification: Optional[str] = None,
                    level:     Optional[str] = None,
                    evidence:  Optional[str] = None,
                    article_id: Optional[str] = None,
                    sentence_idx: Optional[int] = None,
                    source: str = "llm"):
        if rel_type not in ALL_RELATION_TYPES:
            return
        rt = _safe_rel(rel_type)
        with self.driver.session() as s:
            s.run(f"""
                MATCH (a {{id: $from_id}})
                MATCH (b {{id: $to_id}})
                MERGE (a)-[r:{rt}]->(b)
                SET r.modality       = $modality,
                    r.condition      = $condition,
                    r.exception      = $exception,
                    r.scope          = $scope,
                    r.time           = $time,
                    r.status         = $status,
                    r.classification = $classification,
                    r.level          = $level,
                    r.evidence       = $evidence,
                    r.article_id     = $article_id,
                    r.sentence_idx   = $sentence_idx,
                    r.source         = $source
            """,
                from_id=from_id, to_id=to_id,
                modality=modality, condition=condition, exception=exception,
                scope=scope, time=time, status=status,
                classification=classification, level=level,
                evidence=(evidence or "")[:300],
                article_id=article_id, sentence_idx=sentence_idx,
                source=source)

    # ════════════════════════════════════════════════════════════════
    # THAM_CHIEU (rule-based) — REFERS_TO giữa ARTICLE
    # ════════════════════════════════════════════════════════════════
    def add_refers_to(self, from_article_id: str, to_article_id: str,
                      context: str, cross_law: bool = False):
        """REFERS_TO edge giữa 2 ARTICLE. Tạo node đích nếu chưa có."""
        with self.driver.session() as s:
            s.run("""
                MATCH (a:ARTICLE {id: $from_id})
                MERGE (b:ARTICLE {id: $to_id})
                ON CREATE SET b.label    = 'Điều ' + $to_so,
                              b.so       = $to_so,
                              b.layer    = 'structural',
                              b.hieu_luc = true
                MERGE (a)-[r:REFERS_TO]->(b)
                SET r.evidence  = $context,
                    r.cross_law = $cross_law,
                    r.source    = 'rule'
            """,
                from_id=from_article_id,
                to_id=to_article_id,
                to_so=to_article_id.split("_dieu_")[-1],
                context=context[:300],
                cross_law=cross_law)

    # ════════════════════════════════════════════════════════════════
    # Stats
    # ════════════════════════════════════════════════════════════════
    def stats(self) -> dict:
        out: dict[str, int] = {}
        with self.driver.session() as s:
            for lbl in sorted(set(LAYER_OF.keys())):
                r = s.run(f"MATCH (n:{lbl}) RETURN count(n) AS c").single()
                if r and r["c"]:
                    out[lbl] = r["c"]
            r = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            out["__edges__"] = r["c"] if r else 0
        return out
