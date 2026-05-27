"""
FastAPI surface for the Hybrid Legal RAG service.

Run locally:
    uvicorn api.main:app --port 8000

KHÔNG dùng `--reload` khi đang chạy thử retrieval: mỗi lần file .py thay đổi,
uvicorn tear down lifespan → re-instantiate HybridRAGService → reload
Vietnamese_Embedding + Vietnamese_Reranker (mỗi model ~10-15s, sẽ thấy
nhiều progress bar "Loading weights" trong log). Mở nhiều tab UI/chat
KHÔNG gây reload — chỉ file edit + `--reload` mới gây reload.

Endpoints:
    GET  /api/health         — liveness probe.
    GET  /api/laws           — list ingested laws from Neo4j.
    POST /api/chat           — ask a question through the hybrid pipeline.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.services.hybrid_rag_service import (
    HybridRAGService,
    THINKING_MODES,
    _resolve_thinking,
)

from .schemas import ChatRequest, ChatResponse, GraphSubgraphRequest, LawInfo, RefinedInfo


_service: Optional[HybridRAGService] = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _service
    _service = HybridRAGService(
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "12345678"),
        device=os.getenv("RAG_DEVICE", "gpu"),
    )

    # Warm-up underthesea word_tokenize singleton trước khi nhận request.
    # Why: lazy-init của underthesea không thread-safe — câu hỏi đầu tiên
    # thường tách thành ≥2 sub-query và encode_query song song → race trên
    # `word_tokenize_model.featurizer` → AttributeError: 'NoneType' ... 'process'.
    from backend.vector_rag.sparse_encoder import tokenize as _ut_warmup
    _ut_warmup("khởi động bộ tách từ tiếng việt")

    try:
        yield
    finally:
        if _service is not None:
            _service.close()


app = FastAPI(title="Legal-chatbots API", version="0.1.0", lifespan=_lifespan)

_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("API_CORS_ORIGINS", "*").split(",") if o.strip()
]
# "*" fallback OK vì allow_credentials=False. Cho phép cả file:// (Origin=null).
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_service() -> HybridRAGService:
    if _service is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return _service


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ready": _service is not None}


@app.get("/api/laws", response_model=list[LawInfo])
def list_laws() -> list[LawInfo]:
    svc = _require_service()
    with svc.kg.driver.session() as s:
        rows = list(s.run(
            "MATCH (l:LAW) RETURN l.id AS id, l.label AS label ORDER BY l.label"
        ))
    return [LawInfo(id=r["id"], label=r["label"] or r["id"]) for r in rows]


@app.post("/api/graph/subgraph")
def graph_subgraph(req: GraphSubgraphRequest) -> dict:
    svc = _require_service()
    article_ids = _unique_ids(req.article_ids)[:24]
    if not article_ids:
        return {"nodes": [], "edges": []}

    limit = max(20, min(req.limit, 300))
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}

    def add_node(n) -> str:
        props = _jsonable_props(dict(n.items()))
        element_id = getattr(n, "element_id", None) or getattr(n, "id", None)
        node_id = str(props.get("id") or element_id)
        labels = sorted(list(n.labels))
        nodes[node_id] = {
            "id": node_id,
            "labels": labels,
            "label": props.get("label") or props.get("id") or node_id,
            "properties": props,
        }
        return node_id

    def add_edge(r, source_id: str, target_id: str) -> None:
        props = _jsonable_props(dict(r.items()))
        element_id = getattr(r, "element_id", None) or getattr(r, "id", None)
        edge_id = str(element_id or f"{source_id}:{r.type}:{target_id}:{len(edges)}")
        edges[edge_id] = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "type": r.type,
            "properties": props,
        }

    with svc.kg.driver.session() as s:
        rows = list(s.run(
            """
            MATCH (a:ARTICLE)
            WHERE a.id IN $article_ids
            OPTIONAL MATCH (l:LAW)-[lawRel:HAS_ARTICLE]->(a)
            OPTIONAL MATCH (c:CHAPTER)-[chapRel:HAS_ARTICLE]->(a)
            OPTIONAL MATCH (a)-[clauseRel:HAS_CLAUSE]->(k:CLAUSE)
            OPTIONAL MATCH (a)-[mentionRel:MENTIONS]->(ent)
            OPTIONAL MATCH (a)-[refRel:REFERS_TO]->(ref:ARTICLE)
            RETURN a, l, lawRel, c, chapRel, k, clauseRel, ent, mentionRel, ref, refRel
            LIMIT $limit
            """,
            article_ids=article_ids,
            limit=limit,
        ))
        for row in rows:
            article_id = add_node(row["a"])
            for node_key, rel_key, direction in (
                ("l", "lawRel", "in"),
                ("c", "chapRel", "in"),
                ("k", "clauseRel", "out"),
                ("ent", "mentionRel", "out"),
                ("ref", "refRel", "out"),
            ):
                node = row.get(node_key)
                rel = row.get(rel_key)
                if node is None or rel is None:
                    continue
                other_id = add_node(node)
                if direction == "in":
                    add_edge(rel, other_id, article_id)
                else:
                    add_edge(rel, article_id, other_id)

        semantic_rows = list(s.run(
            """
            MATCH (from)-[r]->(to)
            WHERE r.article_id IN $article_ids
               OR any(aid IN coalesce(r.article_ids, []) WHERE aid IN $article_ids)
            RETURN from, r, to
            LIMIT $limit
            """,
            article_ids=article_ids,
            limit=limit,
        ))
        for row in semantic_rows:
            source_id = add_node(row["from"])
            target_id = add_node(row["to"])
            add_edge(row["r"], source_id, target_id)

    return {"nodes": list(nodes.values()), "edges": list(edges.values())}


def _unique_ids(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _jsonable_props(props: dict) -> dict:
    out = {}
    for key, value in props.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            out[key] = _truncate_prop(value)
        elif isinstance(value, list):
            out[key] = [_truncate_prop(v) for v in value[:24]]
        else:
            out[key] = _truncate_prop(value)
    return out


def _truncate_prop(value):
    text = value if isinstance(value, (int, float, bool)) else str(value)
    if isinstance(text, str) and len(text) > 700:
        return text[:700] + "..."
    return text


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    svc = _require_service()
    if req.thinking_mode not in THINKING_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"thinking_mode must be one of {list(THINKING_MODES)}",
        )

    try:
        result = svc.answer(
            req.query,
            law_id=req.law_id,
            top_k=req.top_k,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            thinking_mode=req.thinking_mode,
        )
    except Exception as ex:  # surface upstream errors as 500
        raise HTTPException(status_code=500, detail=f"{type(ex).__name__}: {ex}")

    intent = (result.refined or {}).get("intent") or "thematic"
    thinking_used = _resolve_thinking(req.thinking_mode, intent)

    refined = RefinedInfo(
        original=result.refined.get("original", req.query),
        intent=result.refined.get("intent"),
        objective=result.refined.get("objective", "") or "",
        refined=result.refined.get("refined", req.query),
    )

    return ChatResponse(
        answer=result.answer,
        refined=refined,
        intent=intent,
        thinking_used=thinking_used,
        vector_context=result.vector_context if req.include_context else None,
        graph_context=result.graph_context if req.include_context else None,
        graph_article_ids=result.graph_article_ids if req.include_context else None,
        vector_results=result.vector_results if req.include_context else None,
    )


def _sse(event_type: str, payload: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **payload}, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """
    Server-Sent Events stream. Emits JSON objects of shape:
      {"type":"meta",     "refined":..., "intent":..., "thinking_used":bool, ...}
      {"type":"thinking", "delta":"..."}    (zero or more)
      {"type":"answer",   "delta":"..."}    (zero or more)
      {"type":"done",     "answer":"...", "thinking":"..."}
      {"type":"error",    "message":"..."}
    """
    svc = _require_service()
    if req.thinking_mode not in THINKING_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"thinking_mode must be one of {list(THINKING_MODES)}",
        )

    def event_gen():
        try:
            for kind, data in svc.answer_stream(
                req.query,
                law_id=req.law_id,
                top_k=req.top_k,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                thinking_mode=req.thinking_mode,
                include_context=req.include_context,
            ):
                if kind in ("meta", "done"):
                    yield _sse(kind, data)
                else:  # "thinking" | "answer"
                    yield _sse(kind, {"delta": data})
        except Exception as ex:
            yield _sse("error", {"message": f"{type(ex).__name__}: {ex}"})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disable nginx buffering if proxied
        },
    )
