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
                 content=content, amend=amendment_type,
                 chapter_id=chapter_id, law_id=law_id)

    def upsert_clause(self, clause_id: str, so: str, content: str,
                      article_id: str):
        article_so = article_id.split("_dieu_")[-1]
        with self.driver.session() as s:
            s.run("""
                MERGE (k:CLAUSE {id: $id})
                SET k.label   = 'Điều ' + $article_so + ', Khoản ' + $so,
                    k.so      = $so,
                    k.article_id = $article_id,
                    k.content = $content,
                    k.layer   = 'structural'
                WITH k
                MATCH (a:ARTICLE {id: $article_id})
                MERGE (a)-[:HAS_CLAUSE]->(k)
            """, id=clause_id, so=so, article_so=article_so, content=content[:1500],
                 article_id=article_id)

    # ════════════════════════════════════════════════════════════════
    # Entity nodes (L2 normative-as-node, L4 license/cert, L5, domain)
    # ════════════════════════════════════════════════════════════════
    def upsert_entity(self, node_id: str, etype: str, label: str,
                      *, article_id: Optional[str] = None,
                      clause_id:   Optional[str] = None,
                      canonical_key: Optional[str] = None,
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
                ON CREATE SET n.label = $label,
                              n.aliases = [],
                              n.article_ids = [],
                              n.clause_ids = [],
                              n.sources = [],
                              n.mention_count = 0
                SET n.layer = $layer,
                    n.entity_type = $etype,
                    n.canonical_key = coalesce(n.canonical_key, $canonical_key),
                    n.subclass = coalesce($subclass, n.subclass),
                    n.score = CASE
                        WHEN $score IS NULL THEN n.score
                        WHEN n.score IS NULL OR $score > n.score THEN $score
                        ELSE n.score
                    END,
                    n.source = coalesce(n.source, $source),
                    n.aliases = CASE
                        WHEN $label IS NULL THEN coalesce(n.aliases, [])
                        WHEN $label IN coalesce(n.aliases, []) THEN coalesce(n.aliases, [])
                        ELSE coalesce(n.aliases, []) + $label
                    END,
                    n.article_ids = CASE
                        WHEN $article_id IS NULL THEN coalesce(n.article_ids, [])
                        WHEN $article_id IN coalesce(n.article_ids, []) THEN coalesce(n.article_ids, [])
                        ELSE coalesce(n.article_ids, []) + $article_id
                    END,
                    n.clause_ids = CASE
                        WHEN $clause_id IS NULL THEN coalesce(n.clause_ids, [])
                        WHEN $clause_id IN coalesce(n.clause_ids, []) THEN coalesce(n.clause_ids, [])
                        ELSE coalesce(n.clause_ids, []) + $clause_id
                    END,
                    n.sources = CASE
                        WHEN $source IS NULL THEN coalesce(n.sources, [])
                        WHEN $source IN coalesce(n.sources, []) THEN coalesce(n.sources, [])
                        ELSE coalesce(n.sources, []) + $source
                    END,
                    n.mention_count = coalesce(n.mention_count, 0) + 1
            """, id=node_id, label=label, canonical_key=canonical_key, layer=layer,
                 etype=etype, subclass=subclass, score=score, source=source,
                 article_id=article_id, clause_id=clause_id)

            if article_id:
                s.run(f"""
                    MATCH (a:ARTICLE {{id: $article_id}})
                    MATCH (n:{lbl} {{id: $id}})
                    MERGE (a)-[m:MENTIONS]->(n)
                    SET m.source = coalesce(m.source, $source),
                        m.count = coalesce(m.count, 0) + 1,
                        m.sentence_idx = coalesce(m.sentence_idx, $sidx),
                        m.sentence_idxs = CASE
                            WHEN $sidx IS NULL THEN coalesce(m.sentence_idxs, [])
                            WHEN $sidx IN coalesce(m.sentence_idxs, []) THEN coalesce(m.sentence_idxs, [])
                            ELSE coalesce(m.sentence_idxs, []) + $sidx
                        END
                """, article_id=article_id, id=node_id, sidx=sentence_idx, source=source)

            if clause_id:
                s.run(f"""
                    MATCH (k:CLAUSE {{id: $clause_id}})
                    MATCH (n:{lbl} {{id: $id}})
                    MERGE (k)-[m:MENTIONS]->(n)
                    SET m.source = coalesce(m.source, $source),
                        m.count = coalesce(m.count, 0) + 1,
                        m.sentence_idx = coalesce(m.sentence_idx, $sidx),
                        m.sentence_idxs = CASE
                            WHEN $sidx IS NULL THEN coalesce(m.sentence_idxs, [])
                            WHEN $sidx IN coalesce(m.sentence_idxs, []) THEN coalesce(m.sentence_idxs, [])
                            ELSE coalesce(m.sentence_idxs, []) + $sidx
                        END
                """, clause_id=clause_id, id=node_id, sidx=sentence_idx, source=source)

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
        evidence = (evidence or "").strip()[:300]
        with self.driver.session() as s:
            s.run(f"""
                MATCH (a {{id: $from_id}})
                MATCH (b {{id: $to_id}})
                MERGE (a)-[r:{rt}]->(b)
                ON CREATE SET r.evidences = [],
                              r.article_ids = [],
                              r.sources = [],
                              r.sentence_idxs = [],
                              r.conditions = [],
                              r.exceptions = [],
                              r.scopes = [],
                              r.times = [],
                              r.statuses = [],
                              r.classifications = [],
                              r.levels = [],
                              r.mention_count = 0
                SET r.modality       = coalesce(r.modality, $modality),
                    r.condition      = coalesce(r.condition, $condition),
                    r.exception      = coalesce(r.exception, $exception),
                    r.scope          = coalesce(r.scope, $scope),
                    r.time           = coalesce(r.time, $time),
                    r.status         = coalesce(r.status, $status),
                    r.classification = coalesce(r.classification, $classification),
                    r.level          = coalesce(r.level, $level),
                    r.evidence       = CASE
                        WHEN coalesce(r.evidence, '') = '' AND $evidence <> '' THEN $evidence
                        ELSE r.evidence
                    END,
                    r.article_id     = coalesce(r.article_id, $article_id),
                    r.sentence_idx   = coalesce(r.sentence_idx, $sentence_idx),
                    r.source         = coalesce(r.source, $source),
                    r.evidences = CASE
                        WHEN $evidence = '' THEN coalesce(r.evidences, [])
                        WHEN $evidence IN coalesce(r.evidences, []) THEN coalesce(r.evidences, [])
                        ELSE coalesce(r.evidences, []) + $evidence
                    END,
                    r.article_ids = CASE
                        WHEN $article_id IS NULL THEN coalesce(r.article_ids, [])
                        WHEN $article_id IN coalesce(r.article_ids, []) THEN coalesce(r.article_ids, [])
                        ELSE coalesce(r.article_ids, []) + $article_id
                    END,
                    r.sources = CASE
                        WHEN $source IS NULL THEN coalesce(r.sources, [])
                        WHEN $source IN coalesce(r.sources, []) THEN coalesce(r.sources, [])
                        ELSE coalesce(r.sources, []) + $source
                    END,
                    r.sentence_idxs = CASE
                        WHEN $sentence_idx IS NULL THEN coalesce(r.sentence_idxs, [])
                        WHEN $sentence_idx IN coalesce(r.sentence_idxs, []) THEN coalesce(r.sentence_idxs, [])
                        ELSE coalesce(r.sentence_idxs, []) + $sentence_idx
                    END,
                    r.conditions = CASE
                        WHEN $condition IS NULL OR $condition = '' THEN coalesce(r.conditions, [])
                        WHEN $condition IN coalesce(r.conditions, []) THEN coalesce(r.conditions, [])
                        ELSE coalesce(r.conditions, []) + $condition
                    END,
                    r.exceptions = CASE
                        WHEN $exception IS NULL OR $exception = '' THEN coalesce(r.exceptions, [])
                        WHEN $exception IN coalesce(r.exceptions, []) THEN coalesce(r.exceptions, [])
                        ELSE coalesce(r.exceptions, []) + $exception
                    END,
                    r.scopes = CASE
                        WHEN $scope IS NULL OR $scope = '' THEN coalesce(r.scopes, [])
                        WHEN $scope IN coalesce(r.scopes, []) THEN coalesce(r.scopes, [])
                        ELSE coalesce(r.scopes, []) + $scope
                    END,
                    r.times = CASE
                        WHEN $time IS NULL OR $time = '' THEN coalesce(r.times, [])
                        WHEN $time IN coalesce(r.times, []) THEN coalesce(r.times, [])
                        ELSE coalesce(r.times, []) + $time
                    END,
                    r.statuses = CASE
                        WHEN $status IS NULL OR $status = '' THEN coalesce(r.statuses, [])
                        WHEN $status IN coalesce(r.statuses, []) THEN coalesce(r.statuses, [])
                        ELSE coalesce(r.statuses, []) + $status
                    END,
                    r.classifications = CASE
                        WHEN $classification IS NULL OR $classification = '' THEN coalesce(r.classifications, [])
                        WHEN $classification IN coalesce(r.classifications, []) THEN coalesce(r.classifications, [])
                        ELSE coalesce(r.classifications, []) + $classification
                    END,
                    r.levels = CASE
                        WHEN $level IS NULL OR $level = '' THEN coalesce(r.levels, [])
                        WHEN $level IN coalesce(r.levels, []) THEN coalesce(r.levels, [])
                        ELSE coalesce(r.levels, []) + $level
                    END,
                    r.mention_count = coalesce(r.mention_count, 0) + 1
            """,
                from_id=from_id, to_id=to_id,
                modality=modality, condition=condition, exception=exception,
                scope=scope, time=time, status=status,
                classification=classification, level=level,
                evidence=evidence,
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
                ON CREATE SET r.evidences = []
                SET r.evidence  = CASE
                        WHEN coalesce(r.evidence, '') = '' AND $context <> '' THEN $context
                        ELSE r.evidence
                    END,
                    r.evidences = CASE
                        WHEN $context = '' THEN coalesce(r.evidences, [])
                        WHEN $context IN coalesce(r.evidences, []) THEN coalesce(r.evidences, [])
                        ELSE coalesce(r.evidences, []) + $context
                    END,
                    r.cross_law = $cross_law,
                    r.source    = 'rule'
            """,
                from_id=from_article_id,
                to_id=to_article_id,
                to_so=to_article_id.split("_dieu_")[-1],
                context=(context or "")[:300],
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
