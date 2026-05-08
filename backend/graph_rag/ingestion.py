"""
ingestion.py — Pipeline KG cho 1 file luật do người dùng tải lên.

Entry point:
    ingest_docx(file_path, law_id, ten, so_hieu, nam, loai, *, wipe=False)

Flow (per file):
  1. extract_docx → clean_text
  2. chunk_law → list[LawChunk]   (cấp dieu + khoan)
  3. Upsert LAW + CHAPTER + ARTICLE + CLAUSE  (Layer 1 — 100% node)
  4. Per chunk:
       a. NER → entities (đã có sentence_idx)
       b. Filter: NODE  → upsert entity nodes + MENTIONS edge
                  EDGE  → giữ lại để gắn vào quan hệ (modality/condition/...)
       c. Rule-based: REFERS_TO (THAM_CHIEU)
       d. LLM (Qwen3.5-9B): chunk + node-entities → list edges
       e. Merge edge-attrs cùng câu vào edges từ LLM
       f. Upsert tất cả edges
"""
from __future__ import annotations

import os
import re
import socket
import sys
import unicodedata
import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Cho phép import trực tiếp module trong cùng package khi chạy file này standalone
_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent.parent))           # backend/
from vector_rag.extractor import extract_text, clean_text       # noqa: E402
from vector_rag.chunker   import chunk_law, LawChunk, LAW_META  # noqa: E402

from graph_rag.ner_extractor import get_ner_extractor, split_sentences  # noqa: E402
from graph_rag.tham_chieu  import extract_tham_chieu                    # noqa: E402
from graph_rag.llm_relation import LlmRelationExtractor                 # noqa: E402
from graph_rag.neo4j_loader import Neo4jKG                              # noqa: E402
from graph_rag.ontology import (                                        # noqa: E402
    ALL_NODE_TYPES, STRUCTURAL_NODES, is_node, edge_attr_role,
)
try:
    from backend.services.llm_config import (                            # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
        get_llm_model,
    )
except ImportError:
    from services.llm_config import (                                    # noqa: E402
        DEFAULT_LLM_ENDPOINT,
        DEFAULT_LLM_MODEL,
        get_llm_model,
    )


SO_HIEU_TO_LAW_ID = {meta["so_hieu"]: lid for lid, meta in LAW_META.items()}
ENTITY_NODE_TYPES = ALL_NODE_TYPES - STRUCTURAL_NODES
MAX_ARTICLE_RELATION_NODES = 30


# ── Defaults ─────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

LLM_ENDPOINT   = DEFAULT_LLM_ENDPOINT
LLM_MODEL      = DEFAULT_LLM_MODEL


# ── Helpers ───────────────────────────────────────────────────────────
_ENTITY_PREFIXES = (
    "cac loai", "mot so", "doi voi", "cac", "nhung", "mot", "ve",
)


def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _canonical_entity_text(text: str) -> str:
    value = _strip_accents((text or "").replace("_", " ").lower())
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    changed = True
    while changed:
        changed = False
        for prefix in _ENTITY_PREFIXES:
            marker = prefix + " "
            if value.startswith(marker) and len(value) > len(marker) + 2:
                value = value[len(marker):].strip()
                changed = True
    return value


def _canonical_entity_key(etype: str, text: str) -> str:
    return f"{etype}:{_canonical_entity_text(text)}"


def _make_node_id(etype: str, text: str) -> str:
    canonical = _canonical_entity_text(text)
    slug = re.sub(r"\s+", "_", canonical).strip("_")
    if not slug:
        slug = hashlib.sha1((text or etype).encode("utf-8")).hexdigest()[:12]
    return f"ent_{etype.lower()}_{slug[:80]}"


def _make_chapter_id(law_id: str, chuong_so: str) -> str:
    return f"{law_id}_chuong_{chuong_so}"


def _make_clause_id(article_id: str, khoan_so: str) -> str:
    return f"{article_id}_khoan_{khoan_so}"


def _classify_entity(e: dict) -> tuple[str, dict | None]:
    """
    Trả ('node', enriched_e) | ('edge_attr', role_dict) | ('skip', None).
    """
    etype = e["type"]
    if etype in STRUCTURAL_NODES:
        return ("skip", None)
    if etype in ENTITY_NODE_TYPES and is_node(etype):
        nid = _make_node_id(etype, e["text"])
        return ("node", {
            "id":           nid,
            "type":         etype,
            "label":        e["text"],
            "canonical_key": _canonical_entity_key(etype, e["text"]),
            "score":        e.get("score"),
            "subclass":     e.get("subclass"),
            "sentence_idx": e.get("sentence_idx", 0),
            "source":       e.get("source", "model"),
        })
    role = edge_attr_role(etype)
    if role:
        return ("edge_attr", {
            "role":         role[0],         # 'modality' | 'logic' | 'governance'
            "key":          role[1],         # 'OBLIGATION' | 'condition' | 'AUDIT' | ...
            "value":        e["text"],
            "sentence_idx": e.get("sentence_idx", 0),
        })
    return ("skip", None)


def _attach_edge_attrs(edges: list[dict], edge_attrs: list[dict]) -> list[dict]:
    """
    Ghép edge attrs (từ NER) cùng sentence_idx vào edge (từ LLM).
    LLM có thể đã set modality/condition; nếu chưa, lấy từ NER.
    """
    if not edge_attrs:
        return edges
    by_sent: dict[int, list[dict]] = {}
    for ea in edge_attrs:
        by_sent.setdefault(ea["sentence_idx"], []).append(ea)

    for ed in edges:
        sidx = ed.get("sentence_idx")
        if sidx is None:
            continue
        for ea in by_sent.get(sidx, []):
            role, key, val = ea["role"], ea["key"], ea["value"]
            if role == "modality":
                ed.setdefault("modality", key)  # OBLIGATION / PROHIBITION / PERMISSION
            elif role == "logic":
                ed.setdefault(key, val)          # condition / exception / time / ...
            elif role == "governance":
                # Governance từ NER là gợi ý — không override edge.type của LLM,
                # chỉ thêm vào property `governance_tag` để tham khảo.
                ed.setdefault("governance_tag", key)
    return edges


def _ensure_llm_endpoint_available(endpoint: str, timeout: float = 2.0) -> None:
    """
    Fail fast when the OpenAI-compatible LLM server is not listening.
    Otherwise ingestion prints the same connection error once per chunk.
    """
    parsed = urlparse(endpoint)
    host = parsed.hostname
    if not host:
        raise RuntimeError(f"Invalid LLM endpoint: {endpoint!r}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return
    except OSError as ex:
        raise RuntimeError(
            "LLM endpoint is not reachable: "
            f"{endpoint}. Start an OpenAI-compatible server at this address, "
            "set --llm-endpoint/LLM_ENDPOINT to the correct URL, or rerun with --no-llm."
        ) from ex


# ── Main API ──────────────────────────────────────────────────────────
def ingest_docx(file_path: str | Path,
                law_id:   str,
                ten:      str,
                so_hieu:  str,
                nam:      str,
                loai:     str = "Luật",
                *,
                wipe:           bool = False,
                ner_model_dir:  Optional[str] = None,
                llm_endpoint:   str = LLM_ENDPOINT,
                llm_model:      str = LLM_MODEL,
                neo4j_uri:      str = NEO4J_URI,
                neo4j_user:     str = NEO4J_USER,
                neo4j_password: str = NEO4J_PASSWORD,
                use_llm:        bool = True) -> dict:
    """
    Chạy toàn bộ KG ingestion cho 1 file docx.
    Trả dict thống kê: {chunks, articles, clauses, entities, edges, refers_to}.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    print(f"\n{'=' * 60}\n[ingest] {law_id}  ({so_hieu})\n  file: {file_path}")

    # ── 1. Extract + chunk ─────────────────────────────────────────
    raw   = extract_text(str(file_path))
    text  = clean_text(raw)
    chunks: list[LawChunk] = chunk_law(text, law_id)
    print(f"  chunks: {len(chunks)}  "
          f"(dieu={sum(1 for c in chunks if c.chunk_type == 'dieu')}, "
          f"khoan={sum(1 for c in chunks if c.chunk_type == 'khoan')})")

    if use_llm:
        llm_model = get_llm_model(llm_model)
        _ensure_llm_endpoint_available(llm_endpoint)

    # ── 2. Setup Neo4j ─────────────────────────────────────────────
    kg = Neo4jKG(neo4j_uri, neo4j_user, neo4j_password)
    if wipe:
        kg.wipe()
    kg.setup_schema()

    # ── 3. Layer 1 nodes (LAW + CHAPTER + ARTICLE + CLAUSE) ───────
    kg.upsert_law(law_id=law_id, ten=ten, so_hieu=so_hieu,
                  nam=nam, loai=loai)

    seen_chapters: set[str] = set()
    article_ids:   set[str] = set()

    for chunk in chunks:
        if chunk.chunk_type != "dieu":
            continue
        chapter_id = _make_chapter_id(law_id, chunk.chuong_so)
        if chapter_id not in seen_chapters:
            kg.upsert_chapter(chapter_id, chunk.chuong_so,
                              chunk.chuong_ten, law_id)
            seen_chapters.add(chapter_id)
        kg.upsert_article(
            article_id=chunk.neo4j_id,
            so=chunk.dieu_so, ten=chunk.dieu_ten,
            content=chunk.content,
            chapter_id=chapter_id, law_id=law_id,
            amendment_type=chunk.amendment_type,
        )
        article_ids.add(chunk.neo4j_id)

    # CLAUSE từ chunk khoan
    for chunk in chunks:
        if chunk.chunk_type != "khoan":
            continue
        clause_id = _make_clause_id(chunk.neo4j_id, chunk.khoan_so)
        kg.upsert_clause(clause_id, chunk.khoan_so,
                         chunk.content, chunk.neo4j_id)

    # ── 4a. Rule-based REFERS_TO — chạy 1 lần / Điều, dùng full content ──
    total_refs = 0
    for chunk in chunks:
        if chunk.chunk_type != "dieu":
            continue
        article_id = chunk.neo4j_id
        refs = extract_tham_chieu(chunk.content, chunk.dieu_so, law_id)
        for r in refs:
            if r["cross_law"]:
                target_lid = SO_HIEU_TO_LAW_ID.get(r["to_law_id"])
                if target_lid:
                    to_aid = f"{target_lid}_dieu_{r['to_dieu_so']}"
                else:
                    safe = r["to_law_id"].replace("/", "_")
                    to_aid = f"{safe}_dieu_{r['to_dieu_so']}"
            else:
                to_aid = f"{r['to_law_id']}_dieu_{r['to_dieu_so']}"
            kg.add_refers_to(article_id, to_aid, r["context"], r["cross_law"])
            total_refs += 1

    # ── 4b. Per-chunk: NER + LLM ───────────────────────────────────
    ner = get_ner_extractor(ner_model_dir)
    llm = LlmRelationExtractor(endpoint=llm_endpoint, model=llm_model) if use_llm else None

    total_entities = 0
    total_edges    = 0
    article_texts = {
        c.neo4j_id: c.content for c in chunks if c.chunk_type == "dieu"
    }
    article_nodes: dict[str, dict[str, dict]] = {}

    # Chỉ chạy NER+LLM trên cấp khoan (granular hơn) hoặc trên dieu nếu Điều
    # không bị split khoan. → tránh trùng lặp.
    chunks_for_extraction = _select_extraction_chunks(chunks)
    extraction_chunk_counts: dict[str, int] = {}
    for c in chunks_for_extraction:
        extraction_chunk_counts[c.neo4j_id] = extraction_chunk_counts.get(c.neo4j_id, 0) + 1
    print(f"  extraction chunks: {len(chunks_for_extraction)}")

    for chunk in chunks_for_extraction:
        article_id = chunk.neo4j_id
        anchor_clause = (
            _make_clause_id(article_id, chunk.khoan_so)
            if chunk.chunk_type == "khoan" else None
        )

        # 4a. NER
        entities = ner.extract(chunk.content)

        # 4b. Phân loại
        node_entities: list[dict] = []
        edge_attrs:    list[dict] = []
        for e in entities:
            kind, payload = _classify_entity(e)
            if kind == "node":
                node_entities.append(payload)
            elif kind == "edge_attr":
                edge_attrs.append(payload)

        # Dedup node entities theo id
        seen_nid: set[str] = set()
        nodes_to_upsert: list[dict] = []
        for n in node_entities:
            if n["id"] in seen_nid:
                continue
            seen_nid.add(n["id"])
            nodes_to_upsert.append(n)

        # Upsert node entities
        for n in nodes_to_upsert:
            kg.upsert_entity(
                node_id=n["id"], etype=n["type"], label=n["label"],
                canonical_key=n.get("canonical_key"),
                article_id=article_id, clause_id=anchor_clause,
                sentence_idx=n["sentence_idx"], score=n["score"],
                subclass=n.get("subclass"), source=n.get("source", "ner"),
            )
            article_nodes.setdefault(article_id, {})[n["id"]] = n
        total_entities += len(nodes_to_upsert)

        # 4c. LLM extract edges
        if not llm or len(nodes_to_upsert) < 2:
            continue
        # Gắn sentence_idx vào edges (dùng sentence của from-node làm proxy)
        nodes_idx = {n["id"]: n["sentence_idx"] for n in nodes_to_upsert}
        edges = llm.extract(chunk.content, nodes_to_upsert)
        for ed in edges:
            ed["sentence_idx"] = nodes_idx.get(ed["from_id"])
            ed["article_id"]   = article_id

        edges = _attach_edge_attrs(edges, edge_attrs)

        for ed in edges:
            kg.upsert_edge(
                from_id=ed["from_id"], to_id=ed["to_id"], rel_type=ed["type"],
                modality=ed.get("modality"),
                condition=ed.get("condition"),
                exception=ed.get("exception"),
                scope=ed.get("scope"),
                time=ed.get("time"),
                status=ed.get("status"),
                classification=ed.get("classification"),
                level=ed.get("level"),
                evidence=ed.get("evidence"),
                article_id=ed.get("article_id"),
                sentence_idx=ed.get("sentence_idx"),
                source="llm",
            )
        total_edges += len(edges)

    # 4c. Article-level relation repair. Chunk-level extraction is precise, but
    # can miss relations whose subject/object are split across neighboring chunks.
    if llm:
        for article_id, by_id in article_nodes.items():
            if extraction_chunk_counts.get(article_id, 0) < 2:
                continue
            nodes = _select_article_relation_nodes(list(by_id.values()))
            if len(nodes) < 2:
                continue
            edges = llm.extract(article_texts.get(article_id, ""), nodes)
            for ed in edges:
                ed["article_id"] = article_id
                kg.upsert_edge(
                    from_id=ed["from_id"], to_id=ed["to_id"], rel_type=ed["type"],
                    modality=ed.get("modality"),
                    condition=ed.get("condition"),
                    exception=ed.get("exception"),
                    scope=ed.get("scope"),
                    time=ed.get("time"),
                    status=ed.get("status"),
                    classification=ed.get("classification"),
                    level=ed.get("level"),
                    evidence=ed.get("evidence"),
                    article_id=article_id,
                    sentence_idx=ed.get("sentence_idx"),
                    source="llm_article",
                )
            total_edges += len(edges)

    # ── 5. Stats ───────────────────────────────────────────────────
    stats = kg.stats()
    kg.close()

    summary = {
        "chunks":         len(chunks),
        "articles":       len(article_ids),
        "entities":       total_entities,
        "llm_edges":      total_edges,
        "refers_to":      total_refs,
        "neo4j_stats":    stats,
    }
    print(f"\n[ingest] DONE  {law_id}")
    for k, v in summary.items():
        print(f"  {k:<14}: {v}")
    return summary


def _select_extraction_chunks(chunks: list[LawChunk]) -> list[LawChunk]:
    """
    Tránh chạy NER+LLM lặp trên (Điều, các Khoản con của Điều đó):
      - Nếu 1 Điều có ≥ 1 chunk khoan → chỉ extract trên các khoan.
      - Nếu Điều không bị split → extract trên chunk dieu.
    """
    has_khoan: dict[str, bool] = {}
    for c in chunks:
        if c.chunk_type == "khoan":
            has_khoan[c.neo4j_id] = True
    out = []
    for c in chunks:
        if c.chunk_type == "khoan":
            out.append(c)
        elif c.chunk_type == "dieu" and not has_khoan.get(c.neo4j_id):
            out.append(c)
    return out


_RELATION_NODE_PRIORITY = {
    "LEGAL_ACTOR": 0,
    "CYBER_ACTOR": 0,
    "IT_ACTOR": 0,
    "TELECOM_OPERATOR": 0,
    "SYSTEM": 1,
    "DATA": 1,
    "DATA_TYPE": 1,
    "LEGAL_ACTION": 2,
    "VIOLATION": 2,
    "SANCTION": 2,
    "LEGAL_CONCEPT": 3,
}


def _select_article_relation_nodes(nodes: list[dict]) -> list[dict]:
    """Keep article-level repair prompts bounded and deterministic."""
    best: dict[str, dict] = {}
    for n in nodes:
        current = best.get(n["id"])
        if current is None or float(n.get("score") or 0.0) > float(current.get("score") or 0.0):
            best[n["id"]] = n

    ordered = sorted(
        best.values(),
        key=lambda n: (
            _RELATION_NODE_PRIORITY.get(n.get("type"), 9),
            -float(n.get("score") or 0.0),
            len(n.get("label") or ""),
            n["id"],
        ),
    )
    return ordered[:MAX_ARTICLE_RELATION_NODES]


# ── CLI test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("file", help="Đường dẫn file .docx")
    p.add_argument("--law-id",  required=True, help="VD: LuatAnNinhMang2025")
    p.add_argument("--ten",     required=True)
    p.add_argument("--so-hieu", required=True, help="VD: 116/2025/QH15")
    p.add_argument("--nam",     required=True)
    p.add_argument("--loai",    default="Luật")
    p.add_argument("--wipe",    action="store_true")
    p.add_argument("--no-llm",  action="store_true")
    args = p.parse_args()

    ingest_docx(
        args.file, law_id=args.law_id, ten=args.ten,
        so_hieu=args.so_hieu, nam=args.nam, loai=args.loai,
        wipe=args.wipe, use_llm=not args.no_llm,
    )
