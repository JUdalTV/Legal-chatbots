"""
vector_store.py — Qdrant collection cho Vector RAG (LegalChunk).

Collection schema:
  - vector "dense"  : float, COSINE  (+ ScalarQuantization INT8 + rescore)
  - vector "sparse" : SparseVector  (BM25 weights — hybrid search)

Payload: chunk_id, law_id, chapter, article, clause, points, content,
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
            SparseIndexParams, SparseVectorParams,
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
            sparse_vectors_config={
                "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False)),
            },
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True,
                ),
            ),
        )

        for field in ("law_id", "article", "chunk_type", "chapter"):
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )

        print(f"[vector_store] Created {COLLECTION_NAME!r}  dim={dim}  COSINE+INT8  +sparse")

    # ════════════════════════════════════════════════════════════════
    # Upsert
    # ════════════════════════════════════════════════════════════════
    def upsert_chunks(
        self,
        chunks: list,
        dense_vectors: List[List[float]],
        sparse_vectors: List[tuple[List[int], List[float]]],
    ) -> None:
        """chunks/dense/sparse cùng thứ tự. sparse = list[(indices, values)]."""
        from qdrant_client.models import PointStruct, SparseVector

        points: list[PointStruct] = []
        for c, d, s in zip(chunks, dense_vectors, sparse_vectors):
            ids, vals = s
            vec: dict[str, Any] = {"dense": d}
            if ids:
                vec["sparse"] = SparseVector(indices=ids, values=vals)
            points.append(PointStruct(
                id=c.chunk_id,
                vector=vec,
                payload={
                    "chunk_id":    c.chunk_id,
                    "law_id":      c.law_id,
                    "chapter":     c.chapter,
                    "article":     c.article,
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
        print(f"[vector_store] Upserted {len(points)} points (dense+sparse).")

    # ════════════════════════════════════════════════════════════════
    # Search
    # ════════════════════════════════════════════════════════════════
    def search_dense(
        self,
        query_vector: List[float],
        top_k: int = 10,
        law_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
        oversampling: float = 2.0,
        with_vectors: bool = False,
    ) -> list:
        """Search trên int8 quantized vectors → rescore với fp32 raw."""
        from qdrant_client.models import (
            QuantizationSearchParams, SearchParams,
        )
        flt = self._build_filter(law_id, chunk_type)

        resp = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            using="dense",
            query_filter=flt,
            limit=top_k,
            with_payload=True,
            with_vectors=with_vectors,
            search_params=SearchParams(
                quantization=QuantizationSearchParams(
                    ignore=False, rescore=True, oversampling=oversampling,
                ),
            ),
        )
        return resp.points

    def search_sparse(
        self,
        indices: List[int],
        values: List[float],
        top_k: int = 10,
        law_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
    ) -> list:
        """BM25 sparse search."""
        if not indices:
            return []
        from qdrant_client.models import SparseVector
        flt = self._build_filter(law_id, chunk_type)

        try:
            resp = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=SparseVector(indices=indices, values=values),
                using="sparse",
                query_filter=flt,
                limit=top_k,
                with_payload=True,
            )
            return resp.points
        except Exception as ex:
            # Collection cũ chưa có sparse index → trả empty
            print(f"[vector_store] sparse search skipped: {ex}")
            return []

    # ════════════════════════════════════════════════════════════════
    def get_by_article(
        self,
        article_id: str,
        law_id: Optional[str] = None,
        limit: int = 50,
    ) -> list:
        """Lookup direct theo article id (cho intent='lookup')."""
        from qdrant_client.models import (
            FieldCondition, Filter, MatchValue,
        )
        must = [FieldCondition(key="article", match=MatchValue(value=article_id))]
        if law_id:
            must.append(FieldCondition(key="law_id", match=MatchValue(value=law_id)))
        flt = Filter(must=must)
        resp = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=flt,
            limit=limit,
            with_payload=True,
        )
        return resp[0]  # tuple(points, next_offset)

    # ────────────────────────────────────────────────────────────────
    def _build_filter(
        self,
        law_id: Optional[str],
        chunk_type: Optional[str],
    ):
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        must: list[FieldCondition] = []
        if law_id:
            must.append(FieldCondition(key="law_id", match=MatchValue(value=law_id)))
        if chunk_type:
            must.append(FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type)))
        return Filter(must=must) if must else None

    # ════════════════════════════════════════════════════════════════
    def get_collection_info(self) -> dict[str, Any]:
        info = self.client.get_collection(COLLECTION_NAME)
        return {
            "points_count":  info.points_count,
            "vectors_count": getattr(info, "vectors_count", info.points_count),
            "status":        str(info.status),
        }
