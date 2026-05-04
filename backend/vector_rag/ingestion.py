"""
ingestion.py — Vector RAG ingest pipeline cho 1 file luật.

  .docx | .pdf
    → extract_text + clean_text                       (vector_rag/extractor.py)
    → parse_to_articles → chunk_legal_document         (chunker_v2.py)
    → Embedder.encode (fp16)                           (embedder.py)
    → VectorStore.upsert_chunks (Qdrant int8 collection) (vector_store.py)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .chunker_v2 import LegalChunk, chunk_legal_document, parse_to_articles
from .embedder import Embedder
from .extractor import clean_text, extract_text
from .vector_store import VectorStore


def ingest_file(
    file_path: str | Path,
    law_id: str,
    *,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    recreate: bool = False,
    device: str = "gpu",
    min_tokens: int = 100,
    max_tokens: int = 500,
    embed_batch: int = 24,
) -> dict:
    """Chạy E2E ingest cho 1 file. Trả dict thống kê."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    print(f"\n{'=' * 60}\n[vector_rag] ingest {law_id}\n  file: {file_path}")

    # 1. Extract + clean
    raw  = extract_text(str(file_path))
    text = clean_text(raw)

    # 2. Embedder (load early — count_tokens cần tokenizer)
    embedder = Embedder(device=device)

    # 3. Parse + chunk
    articles = parse_to_articles(text, law_id)
    chunks: list[LegalChunk] = chunk_legal_document(
        articles,
        law_id=law_id,
        count_tokens=embedder.count_tokens,
        min_tokens=min_tokens,
        max_tokens=max_tokens,
    )
    n_summary = sum(1 for c in chunks if c.chunk_type == "article_summary")
    n_clause  = sum(1 for c in chunks if c.chunk_type == "clause")
    n_points  = sum(1 for c in chunks if c.chunk_type == "point_group")
    print(f"  articles={len(articles)}  chunks={len(chunks)} "
          f"(summary={n_summary}, clause={n_clause}, point_group={n_points})")

    if not chunks:
        print("[vector_rag] Không có chunk nào — kiểm tra file/law_id.")
        return {"chunks": 0, "articles": len(articles)}

    # 4. Init collection (cần biết dim từ embedder)
    store = VectorStore(host=qdrant_host, port=qdrant_port)
    store.init_collection(dim=embedder.dim, recreate=recreate)

    # 5. Embed
    print(f"  embedding {len(chunks)} chunks (batch={embed_batch})...")
    vectors = embedder.encode(
        [c.content for c in chunks],
        batch_size=embed_batch,
        show_progress=True,
    )

    # 6. Upsert
    store.upsert_chunks(chunks, vectors)

    info = store.get_collection_info()
    print(f"\n[vector_rag] DONE  points={info['points_count']}  status={info['status']}")
    return {
        "law_id":         law_id,
        "articles":       len(articles),
        "chunks":         len(chunks),
        "by_type": {
            "article_summary": n_summary,
            "clause":          n_clause,
            "point_group":     n_points,
        },
        "qdrant":         info,
    }
