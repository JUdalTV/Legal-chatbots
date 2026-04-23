"""
ingestion.py
Pipeline hoàn chỉnh cho Vector RAG:
  docx → extract → clean → chunk → embed → upsert Qdrant

Chạy:
  python ingestion.py
"""

import os
import json
from pathlib import Path

from extractor import extract_docx, clean_text
from chunker import chunk_law, LawChunk
from embedder import Embedder
from vector_store import VectorStore


# ── Cấu hình đường dẫn ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent  # backend/

RAW_FILES = {
    "LuatAnNinhMang2025": BASE_DIR / "data" / "raw" / "luatanm2025.docx",
    "LuatCNTT2006":       BASE_DIR / "data" / "raw" / "luatcntt2006.docx",
    "LuatVienThong2023":  BASE_DIR / "data" / "raw" / "luatvienthong2023.docx",
}

CHUNKS_CACHE_DIR = BASE_DIR / "data" / "chunks"   # lưu chunks.json để debug

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


def run_ingestion(recreate_collection: bool = False):
    """
    Chạy toàn bộ pipeline Vector RAG cho 3 luật.
    """
    CHUNKS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Khởi tạo Qdrant
    store = VectorStore(host=QDRANT_HOST, port=QDRANT_PORT)
    store.init_collection(recreate=recreate_collection)

    # 2. Khởi tạo Embedder
    embedder = Embedder(device="gpu")

    all_chunks: list[LawChunk] = []

    # 3. Extract → Clean → Chunk từng luật
    for law_name, file_path in RAW_FILES.items():
        if not file_path.exists():
            print(f"[WARN] Không tìm thấy file: {file_path}, bỏ qua.")
            continue

        print(f"\n{'='*50}")
        print(f"Processing: {law_name}")
        print(f"File: {file_path}")

        raw_text = extract_docx(str(file_path))
        clean = clean_text(raw_text)
        chunks = chunk_law(clean, law_name)

        print(f"  → {len(chunks)} chunks "
              f"(dieu: {sum(1 for c in chunks if c.chunk_type=='dieu')}, "
              f"khoan: {sum(1 for c in chunks if c.chunk_type=='khoan')})")

        # Lưu chunks ra JSON để debug/kiểm tra
        cache_path = CHUNKS_CACHE_DIR / f"{law_name}_chunks.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "chunk_id":       c.chunk_id,
                        "neo4j_id":       c.neo4j_id,
                        "chunk_type":     c.chunk_type,
                        "law_name":       c.law_name,
                        "chuong_so":      c.chuong_so,
                        "chuong_ten":     c.chuong_ten,
                        "dieu_so":        c.dieu_so,
                        "dieu_ten":       c.dieu_ten,
                        "khoan_so":       c.khoan_so,
                        "amendment_type": c.amendment_type,
                        "affected_laws":  c.affected_laws,
                        "content":        c.content[:300] + "...",
                    }
                    for c in chunks
                ],
                f, ensure_ascii=False, indent=2
            )
        print(f"  → Cache: {cache_path}")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("\n[ERROR] Không có chunk nào! Kiểm tra đường dẫn file.")
        return

    print(f"\nTổng: {len(all_chunks)} chunks từ {len(RAW_FILES)} luật")

    # 4. Embed theo batch
    print("\nBắt đầu embedding...")
    texts_for_embed = [c.content_for_embed for c in all_chunks]
    dense_vectors = embedder.encode(texts_for_embed, batch_size=16, show_progress=True)

    # 5. Upsert vào Qdrant
    print("\nUpsert vào Qdrant...")
    store.upsert_chunks(all_chunks, dense_vectors)

    # 6. Kiểm tra
    info = store.get_collection_info()
    print(f"\n✅ Hoàn tất Vector RAG ingestion!")
    print(f"   Collection: law_chunks")
    print(f"   Vectors count: {info['vectors_count']}")
    print(f"   Points count:  {info['points_count']}")


if __name__ == "__main__":
    run_ingestion(recreate_collection=True)