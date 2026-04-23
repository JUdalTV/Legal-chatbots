"""
vector_store.py
Quản lý Qdrant collection cho Vector RAG.

Schema Qdrant Point:
  id      : UUID (từ chunk_id)
  vector  : {"dense": [float × 1024]}   ← bge-m3
  payload : xem PAYLOAD_SCHEMA bên dưới

PAYLOAD_SCHEMA:
  neo4j_id        : str   ← cầu nối sang Neo4j DieuLuat node  ★ bắt buộc
  chunk_id        : str   ← UUID trùng với point id
  chunk_type      : str   ← "dieu" | "khoan"
  law_name        : str   ← "LuatAnNinhMang2025"
  so_hieu         : str   ← "116/2025/QH15"
  chuong_so       : str   ← "I"
  chuong_ten      : str   ← "NHỮNG QUY ĐỊNH CHUNG"
  dieu_so         : str   ← "2"
  dieu_ten        : str   ← "Giải thích từ ngữ"
  khoan_so        : str | null
  content         : str   ← text gốc (trả cho LLM)
  content_for_embed: str  ← text đã normalize (đã dùng để embed)
  amendment_type  : str | null  ← "sua_doi" | "bai_bo" | "hieu_luc" | "chuyen_tiep"
  affected_laws   : list[str]   ← ["67/2006/QH11", ...]
"""

from __future__ import annotations
from typing import List, Optional, Any


COLLECTION_NAME = "law_chunks"
VECTOR_DIM = 1024


class VectorStore:
    """
    Wrapper quanh QdrantClient.
    Mọi thao tác với Qdrant đi qua class này.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import (
                VectorParams, Distance,
                SparseVectorParams, SparseIndexParams,
            )
        except ImportError:
            raise ImportError("pip install qdrant-client")

        self.client = QdrantClient(host=host, port=port)
        self._QdrantClient = QdrantClient
        self._VectorParams = VectorParams
        self._Distance = Distance
        self._SparseVectorParams = SparseVectorParams
        self._SparseIndexParams = SparseIndexParams

    # ── Khởi tạo collection ───────────────────────────────────────

    def init_collection(self, recreate: bool = False):
        """
        Tạo collection với:
          - dense  vector (bge-m3, 1024 dim, COSINE)
          - sparse vector (BM25 keyword)  → hybrid search
        """
        from qdrant_client.models import (
            VectorParams, Distance,
            SparseVectorParams, SparseIndexParams,
        )

        existing = [c.name for c in self.client.get_collections().collections]

        if COLLECTION_NAME in existing:
            if recreate:
                self.client.delete_collection(COLLECTION_NAME)
            else:
                print(f"Collection '{COLLECTION_NAME}' đã tồn tại, bỏ qua.")
                return

        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )

        # Payload indexes để filter nhanh
        from qdrant_client.models import PayloadSchemaType
        for field_name in ["law_name", "chunk_type", "dieu_so", "chuong_so", "amendment_type"]:
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=PayloadSchemaType.KEYWORD,
            )

        print(f"Đã tạo collection '{COLLECTION_NAME}' — dim={VECTOR_DIM}, COSINE")

    # ── Upsert points ─────────────────────────────────────────────

    def upsert_chunks(self, chunks: list, dense_vectors: List[List[float]]):
        """
        Upload chunks + dense vectors vào Qdrant.
        chunks: List[LawChunk]
        dense_vectors: List[List[float]] cùng thứ tự
        """
        from qdrant_client.models import PointStruct

        points = []
        for chunk, vec in zip(chunks, dense_vectors):
            points.append(PointStruct(
                id=chunk.chunk_id,
                vector={"dense": vec},
                payload={
                    # ── Cầu nối Neo4j ──────────────────────────────
                    "neo4j_id":          chunk.neo4j_id,
                    # ── Identity ───────────────────────────────────
                    "chunk_id":          chunk.chunk_id,
                    "chunk_type":        chunk.chunk_type,
                    # ── Provenance ─────────────────────────────────
                    "law_name":          chunk.law_name,
                    "so_hieu":           chunk.so_hieu,
                    "chuong_so":         chunk.chuong_so,
                    "chuong_ten":        chunk.chuong_ten,
                    "dieu_so":           chunk.dieu_so,
                    "dieu_ten":          chunk.dieu_ten,
                    "khoan_so":          chunk.khoan_so,
                    # ── Content ────────────────────────────────────
                    "content":           chunk.content,
                    "content_for_embed": chunk.content_for_embed,
                    # ── Amendment ★ NEW ────────────────────────────
                    "amendment_type":    chunk.amendment_type,
                    "affected_laws":     chunk.affected_laws,
                }
            ))

        # Batch upsert
        BATCH = 64
        for i in range(0, len(points), BATCH):
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i:i + BATCH],
            )

        print(f"Đã upsert {len(points)} points vào Qdrant.")

    # ── Search ────────────────────────────────────────────────────

    def search_dense(
        self,
        query_vector: List[float],
        top_k: int = 10,
        law_name: Optional[str] = None,
        chunk_type: Optional[str] = None,
    ) -> list:
        """
        Semantic search bằng dense vector.
        Có thể filter theo law_name và chunk_type.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        filter_conditions = []
        if law_name:
            filter_conditions.append(
                FieldCondition(key="law_name", match=MatchValue(value=law_name))
            )
        if chunk_type:
            filter_conditions.append(
                FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type))
            )

        query_filter = (
            Filter(must=filter_conditions) if filter_conditions else None
        )

        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=("dense", query_vector),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return results

    def get_collection_info(self) -> dict:
        info = self.client.get_collection(COLLECTION_NAME)
        return {
            "vectors_count": getattr(info, "vectors_count", getattr(info, "indexed_vectors_count", info.points_count)),
            "points_count":  info.points_count,
            "status":        str(info.status),
        }