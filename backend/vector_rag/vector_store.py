"""
vector_store.py — Qdrant collection cho Vector RAG (LegalChunk).

Collection schema:
  - vector "dense" : float, COSINE
  - quantization   : SCALAR INT8 (always_ram=True) — search nhanh hơn 4x
  - rescore        : oversampling=2.0 trên fp32 raw để giữ recall

Payload schema (LegalChunk → point.payload):
  chunk_id, law_id, chapter, article (= neo4j_id), clause, points, content,
  token_count, chunk_type, refs[], metadata{...}
"""
from __future__ import annotations

from typing import Any, List, Optional


COLLECTION_NAME = "law_chunks"


class VectorStore:
    """Wrapper QdrantClient. Mọi thao tác với Qdrant đi qua class này."""

    def __init__(self, host: str = "localhost", port: int = 6333):
        try:
            from qdrant_client import QdrantClient
        except ImportError as e:
            raise ImportError("pip install qdrant-client") from e
        self.client = QdrantClient(host=host, port=port)

    # ════════════════════════════════════════════════════════════════
    # Collection lifecycle
    # ════════════════════════════════════════════════════════════════
    def init_collection(self, dim: int, recreate: bool = False) -> None:
        from qdrant_client.models import (
            Distance, PayloadSchemaType,
            ScalarQuantization, ScalarQuantizationConfig, ScalarType,
            VectorParams,
        )

        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME in existing:
            if recreate:
                self.client.delete_collection(COLLECTION_NAME)
            else:
                print(f"[vector_store] Collection {COLLECTION_NAME!r} đã tồn tại.")
                return

        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(size=dim, distance=Distance.COSINE),
            },
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8,
                    quantile=0.99,       # robust với outlier
                    always_ram=True,     # quantized vectors trong RAM → search nhanh
                ),
            ),
        )

        # Payload indexes — filter nhanh
        for field in ("law_id", "article", "chunk_type", "chapter"):
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )

        print(f"[vector_store] Created {COLLECTION_NAME!r}  dim={dim}  COSINE  INT8")

    # ════════════════════════════════════════════════════════════════
    # Upsert
    # ════════════════════════════════════════════════════════════════
    def upsert_chunks(self, chunks: list, dense_vectors: List[List[float]]) -> None:
        """chunks: list[LegalChunk]; dense_vectors cùng thứ tự."""
        from qdrant_client.models import PointStruct

        points: list[PointStruct] = []
        for c, vec in zip(chunks, dense_vectors):
            points.append(PointStruct(
                id=c.chunk_id,
                vector={"dense": vec},
                payload={
                    "chunk_id":    c.chunk_id,
                    "law_id":      c.law_id,
                    "chapter":     c.chapter,
                    "article":     c.article,        # = neo4j_id (cầu sang Graph RAG)
                    "clause":      c.clause,
                    "points":      c.points,
                    "content":     c.content,
                    "token_count": c.token_count,
                    "chunk_type":  c.chunk_type,
                    "refs":        c.refs,
                    "metadata":    c.metadata,
                },
            ))

        BATCH = 64
        for i in range(0, len(points), BATCH):
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i:i + BATCH],
            )
        print(f"[vector_store] Upserted {len(points)} points.")

    # ════════════════════════════════════════════════════════════════
    # Search — int8 + rescore với fp32 raw
    # ════════════════════════════════════════════════════════════════
    def search_dense(
        self,
        query_vector: List[float],
        top_k: int = 10,
        law_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
        oversampling: float = 2.0,
    ) -> list:
        """
        Search trên int8 quantized vectors → rescore với fp32 raw để giữ recall.
        oversampling=2.0 nghĩa là Qdrant lấy 2*top_k candidates ở int8 rồi rescore.
        """
        from qdrant_client.models import (
            FieldCondition, Filter, MatchValue,
            QuantizationSearchParams, SearchParams,
        )

        must: list[FieldCondition] = []
        if law_id:
            must.append(FieldCondition(key="law_id", match=MatchValue(value=law_id)))
        if chunk_type:
            must.append(FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type)))
        flt = Filter(must=must) if must else None

        # qdrant-client ≥ 1.10: dùng query_points (search() đã deprecated/bỏ)
        resp = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            using="dense",
            query_filter=flt,
            limit=top_k,
            with_payload=True,
            search_params=SearchParams(
                quantization=QuantizationSearchParams(
                    ignore=False,            # dùng int8 cho first-pass
                    rescore=True,            # rescore với fp32 raw
                    oversampling=oversampling,
                ),
            ),
        )
        return resp.points

    def get_by_article(
        self,
        article_id: str,
        *,
        law_id: Optional[str] = None,
        limit: int = 30,
    ) -> list:
        """Fetch chunks that belong to one ARTICLE id, e.g. LuatAnNinhMang2025_dieu_10."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        must = [FieldCondition(key="article", match=MatchValue(value=article_id))]
        if law_id:
            must.append(FieldCondition(key="law_id", match=MatchValue(value=law_id)))
        points, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(must=must),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return points

    # ════════════════════════════════════════════════════════════════
    # Stats
    # ════════════════════════════════════════════════════════════════
    def get_collection_info(self) -> dict[str, Any]:
        info = self.client.get_collection(COLLECTION_NAME)
        return {
            "points_count":  info.points_count,
            "vectors_count": getattr(info, "vectors_count", info.points_count),
            "status":        str(info.status),
        }
