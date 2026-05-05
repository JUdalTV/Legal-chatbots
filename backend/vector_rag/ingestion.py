"""
ingestion.py — Vector RAG ingest pipeline cho 1 file luật.

  .docx | .pdf
    → extract_text + clean_text                    (vector_rag/extractor.py)
    → parse_to_articles → chunk_legal_document      (chunker_v2.py)
    → BM25Encoder.fit + encode_doc (CPU)         ┐
                                                 ├─ song song (ThreadPool)
    → Embedder.encode (GPU, fp16)                ┘
    → VectorStore.upsert_chunks (dense + sparse)   (vector_store.py)
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .chunker_v2 import LegalChunk, chunk_legal_document, parse_to_articles
from .embedder import Embedder
from .extractor import clean_text, extract_text
from .sparse_encoder import DEFAULT_BM25_PATH, BM25Encoder
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
    bm25_path: str | Path = DEFAULT_BM25_PATH,
) -> dict:
    """E2E ingest cho 1 file. Trả dict thống kê."""
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

    # 4. Init Qdrant
    store = VectorStore(host=qdrant_host, port=qdrant_port)
    store.init_collection(dim=embedder.dim, recreate=recreate)

    # 5. Fit BM25 trên chunks này
    contents = [c.content for c in chunks]
    bm25 = BM25Encoder().fit(contents)
    bm25.save(bm25_path)
    print(f"  bm25: vocab={len(bm25.vocab)}  avgdl={bm25.avgdl:.1f}  → {bm25_path}")

    # 6. Encode dense (GPU) + sparse (CPU) song song
    print(f"  encoding {len(chunks)} chunks (dense+sparse parallel, batch={embed_batch})...")
    with ThreadPoolExecutor(max_workers=2) as ex:
        dense_fut  = ex.submit(
            embedder.encode, contents,
            batch_size=embed_batch, show_progress=True,
        )
        sparse_fut = ex.submit(
            lambda: [bm25.encode_doc(t) for t in contents]
        )
        dense_vectors  = dense_fut.result()
        sparse_vectors = sparse_fut.result()

    # 7. Upsert
    store.upsert_chunks(chunks, dense_vectors, sparse_vectors)

    info = store.get_collection_info()
    print(f"\n[vector_rag] DONE  points={info['points_count']}  status={info['status']}")
    return {
        "law_id":     law_id,
        "articles":   len(articles),
        "chunks":     len(chunks),
        "by_type": {
            "article_summary": n_summary,
            "clause":          n_clause,
            "point_group":     n_points,
        },
        "bm25_vocab": len(bm25.vocab),
        "qdrant":     info,
    }
