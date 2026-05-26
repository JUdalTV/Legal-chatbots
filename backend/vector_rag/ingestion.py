"""
ingestion.py — Vector RAG ingest pipeline cho 1 file luật.

  .docx | .pdf
    → extract_text + clean_text                       (vector_rag/extractor.py)
    → parse_to_articles → chunk_legal_document         (chunker_v2.py)
    → Embedder.encode dense (GPU, fp16) chunks mới
    → VectorStore.upsert_chunks (dense, sparse rỗng)   (vector_store.py)
    → scroll TOÀN BỘ collection → BM25Encoder.fit
    → encode_doc sparse cho all → update_vectors(sparse only)
"""
from __future__ import annotations

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

    # 5. Encode dense (GPU) cho chunks mới — sparse sẽ encode sau khi refit BM25 toàn corpus
    contents = [c.content for c in chunks]
    print(f"  encoding {len(chunks)} chunks (dense, batch={embed_batch})...")
    dense_vectors = embedder.encode(
        contents, batch_size=embed_batch, show_progress=True,
    )

    # 6. Upsert chunks mới (sparse rỗng tạm thời) — để scroll bước 7 bao gồm cả chunks này
    empty_sparse: list[tuple[list[int], list[float]]] = [([], []) for _ in chunks]
    store.upsert_chunks(chunks, dense_vectors, empty_sparse)

    # 7. Refit BM25 trên TOÀN BỘ corpus trong collection (gồm các luật đã ingest trước đó)
    all_pairs = store.scroll_all_contents()
    all_ids       = [pid for pid, _ in all_pairs]
    all_contents  = [txt for _, txt in all_pairs]
    bm25 = BM25Encoder().fit(all_contents)
    bm25.save(bm25_path)
    print(f"  bm25 (full corpus): docs={len(all_contents)}  vocab={len(bm25.vocab)}  "
          f"avgdl={bm25.avgdl:.1f}  → {bm25_path}")

    # 8. Encode sparse cho toàn bộ + update_vectors (chỉ ghi đè sparse, giữ dense + payload)
    print(f"  encoding sparse for {len(all_contents)} points...")
    all_sparse = [bm25.encode_doc(t) for t in all_contents]
    store.update_sparse_vectors(all_ids, all_sparse)

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
