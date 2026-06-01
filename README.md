# Legal-chatbots — Hybrid RAG cho Pháp luật Việt Nam

Hệ thống Q&A trên 3 bộ luật:

- **Luật An ninh mạng 2025** (116/2025/QH15)
- **Luật Viễn thông 2023** (24/2023/QH15)
- **Luật Công nghệ thông tin** (Văn bản hợp nhất 65/VBHN-VPQH)

Hai nhánh retrieval chạy **song song** rồi đưa vào 1 lần gọi LLM tổng hợp:

```
                ┌──── Vector RAG  (Qdrant, hybrid dense+sparse, rerank) ────┐
   query ──►  fan-out                                                       └─► LLM synthesis ─► answer
                └──── Graph RAG   (Neo4j, ontology 5 lớp + NER + LLM edges) ─┘
```

Composite benchmark (xem [benchmark/](benchmark/))

---

## Mục lục

1. [Kiến trúc tổng quan](#kiến-trúc-tổng-quan)
2. [Cài đặt & chạy hạ tầng](#cài-đặt--chạy-hạ-tầng)
3. [Vector RAG](#vector-rag)
4. [Graph RAG](#graph-rag)
5. [LLM Reasoning & Hybrid Synthesis](#llm-reasoning--hybrid-synthesis)
6. [API HTTP](#api-http)
7. [Cây thư mục](#cây-thư-mục)

---

## Kiến trúc tổng quan

| Lớp | Tech | Mục đích |
|---|---|---|
| Vector DB | Qdrant (INT8 scalar quantization + fp32 rescore) | Dense + sparse hybrid search |
| Graph DB | Neo4j 5 Community + APOC | Knowledge graph theo ontology pháp lý |
| Embedding | `truro7/vn-law-embedding` (dim=768, fp16 GPU) | Domain-specific cho luật VN |
| Reranker | `AITeamVN/Vietnamese_Reranker` (fp16 GPU) | CrossEncoder rerank candidate |
| Sparse | BM25 (underthesea word_tokenize) | Token match — bổ sung cho dense |
| LLM | OpenAI-compatible endpoint (mặc định Qwen3.5-9B qua vLLM) | Query refine + final synthesis |
| Fusion | RRF (k=60) → rerank → MMR (λ=0.5) | Trộn dense+sparse, đa dạng kết quả |

Document được chunk theo cấu trúc pháp lý: `LAW → CHAPTER → ARTICLE → CLAUSE → POINT`. Vector RAG sinh 3 loại chunk: `article_summary`, `clause`, `point_group`; cả 3 dùng chung `chunk_id` map sang `neo4j_id` để 2 nhánh nối được với nhau.

---

## Cài đặt & chạy hạ tầng

```bash
# 1. Dependencies
python -m venv .venv && .venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r api/requirements.txt

# 2. Hạ tầng (Qdrant + Neo4j)
docker compose up -d qdrant neo4j

# 3. Cấu hình
cp backend/.env.example backend/.env   # hoặc tạo tay theo block dưới
```

`backend/.env` cần có:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678

QDRANT_HOST=localhost
QDRANT_PORT=6333

LLM_ENDPOINT=http://<host>:8005/v1/chat/completions
LLM_MODEL=Qwen/Qwen3.5-9B
LLM_API_KEY=
LLM_DISABLE_THINKING=1
```

> **Windows + Docker Desktop:** Bind mount `./qdrant_storage:/qdrant/storage` không cho phép Qdrant rename folder khi `delete_collection`. Khi cần wipe sạch, làm thủ công:
> ```bash
> docker stop qdrant_doan
> rm -rf qdrant_storage/collections/law_chunks
> docker start qdrant_doan
> ```

---

## Vector RAG

Module: [backend/vector_rag/](backend/vector_rag/)

### Pipeline ingest

```
.docx | .pdf
  → extract_text + clean_text                       (extractor.py)
  → parse_to_articles → chunk_legal_document         (chunker_v2.py)
  → Embedder.encode dense (GPU, fp16)                (embedder.py)
  → VectorStore.upsert_chunks (dense, sparse rỗng)   (vector_store.py)
  → scroll TOÀN BỘ collection → BM25.fit             (sparse_encoder.py)
  → encode_doc sparse cho all → update_vectors       (chỉ ghi đè sparse)
```

**Tại sao refit BM25 trên full corpus mỗi lần ingest?**  BM25 cần avgdl + IDF tính trên toàn collection để chuẩn. Nếu chỉ fit trên chunks của file đang ingest, BM25 chỉ biết vocab của file cuối → sparse search 2 luật trước đó bị mù chữ. Pipeline mới scroll tất cả `(id, content)` đã upsert, fit BM25 trên full, encode sparse cho mọi point, rồi dùng `update_vectors` để ghi đè **chỉ sparse vector** (dense + payload giữ nguyên — tránh tốn GPU re-embed).

### Pipeline search

```
query
  → classify_intent (regex heuristic) → top_k
  → nếu intent=lookup + có law_id ⇒ direct article fetch (skip search)
  → encode query: dense (GPU) ∥ sparse (CPU BM25)
  → search_dense (INT8 + fp32 rescore, oversampling=2x) ∥ search_sparse
  → RRF fuse (k=60)
  → CrossEncoder Vietnamese_Reranker → score [0,1]
  → threshold filter (min_rerank_score)
  → MMR (λ=0.5) HOẶC dedup_by_article
  → list[dict] + format_context_for_llm
```

### Intent → top_k

Phân loại bằng regex tại [intent.py](backend/vector_rag/intent.py). 13 intent, chia 2 nhóm:

- **Factual** (trích nguyên văn, scaffold chặt): `lookup` (k=4), `definition` (k=4), `cross_law` (k=6), `compare` (k=6), `penalty` (k=6), `authority` (k=6), `procedure` (k=8), `obligation` (k=7), `liability` (k=7)
- **Reasoning** (suy luận, scaffold IRAC): `applicability` (k=7), `gap_analysis` (k=8), `conclusion` (k=6), `thematic` (k=7)

`REASONING_INTENTS` (4 cuối) bật thinking mode mặc định khi `thinking_mode="auto"`.

### CLI

```bash
# Ingest từng file
python -m backend.vector_rag.main ingest "law_dataset/Luật-116-2025-QH15.docx" --law-id LuatAnNinhMang2025
python -m backend.vector_rag.main ingest "law_dataset/Luật-24-2023-QH15.docx"  --law-id LuatVienThong2023
python -m backend.vector_rag.main ingest "law_dataset/Văn-bản-hợp-nhất-65-VBHN-VPQH.docx" --law-id LuatCNTT2025

# Search & stats
python -m backend.vector_rag.main search "trách nhiệm doanh nghiệp viễn thông"
python -m backend.vector_rag.main search "Điều 15 nói gì?" --law-id LuatAnNinhMang2025 --show-context
python -m backend.vector_rag.main intent "có được phép chia sẻ dữ liệu không?"
python -m backend.vector_rag.main stats
python -m backend.vector_rag.main chat --law-id LuatAnNinhMang2025 --show-sources
```

### Files chính

| File | Vai trò |
|---|---|
| `chunker.py` / `chunker_v2.py` | Parse cấu trúc Chương/Điều/Khoản/Điểm, sinh 3 loại chunk |
| `extractor.py` | `.docx` / `.pdf` → plain text (xử lý header/footer, soft-hyphen) |
| `embedder.py` | SentenceTransformer wrapper, singleton cache theo (device, fp16) |
| `sparse_encoder.py` | BM25 + underthesea tokenizer (giữ từ ghép VN như "viễn_thông") |
| `vector_store.py` | Qdrant client wrapper (init/upsert/scroll/search dense+sparse/update_vectors) |
| `fusion.py` | RRF + MMR + dedup_by_article |
| `reranker.py` | CrossEncoder rerank, sigmoid score, format context cho LLM |
| `intent.py` | Regex phân loại 13 intent → top_k mặc định |
| `pipeline.py` | E2E search: intent → dense+sparse → RRF → rerank → MMR |
| `ingestion.py` | E2E ingest 1 file (dense + refit BM25 full corpus + sparse update) |
| `prompt_builder.py` | Render prompt RAG (system + user + context) |
| `main.py` | CLI driver |

---

## Graph RAG

Module: [backend/graph_rag/](backend/graph_rag/)

### Ontology (5 lớp, theo [legal_ontology.docx](legal_ontology.docx))

| Lớp | Loại | Ví dụ |
|---|---|---|
| **L1 Structural** | 100% NODE | `LAW`, `CHAPTER`, `ARTICLE`, `CLAUSE`, `POINT`, `APPENDIX` |
| **L2 Normative** | SPLIT (node + edge.modality) | Node: `LEGAL_ACTOR`, `LEGAL_ACTION`, `RIGHT`, `SANCTION` · Edge: `OBLIGATION`, `PROHIBITION`, `PERMISSION` |
| **L3 Logic** | 0% NODE (edge property) | `condition`, `exception`, `scope`, `time`, `status` |
| **L4 Governance** | SPLIT | Node: `LICENSE`, `CERTIFICATE` · Edge: `COMPLIANCE`, `AUDIT`, `ENFORCEMENT` |
| **L5 System/Data** | 100% NODE | `SYSTEM`, `DATA`, `PLATFORM`, `NETWORK` |
| **Domain ext.** | 100% NODE | Cyber (`THREAT`, `VULNERABILITY`...), Telecom (`SUBSCRIBER`, `BANDWIDTH`...), IT (`SOFTWARE`, `STANDARD`...) |

Định nghĩa đầy đủ ở [backend/graph_rag/ontology.py](backend/graph_rag/ontology.py).

### Pipeline ingest

Per chunk:

1. **NER** (fine-tuned electra-vi) → entities với `sentence_idx`
2. **Filter ontology**:
    - `is_node(label)` → upsert entity node + edge `MENTIONS` từ ARTICLE
    - `edge_attr_role(label)` → giữ để gắn vào edge properties (modality/condition/...)
3. **Rule-based** [`tham_chieu.py`](backend/graph_rag/tham_chieu.py): regex bắt "Điều X", "Khoản Y", "Luật ABC số ..." → edge `REFERS_TO ↔ ARTICLE`
4. **LLM relation extraction** ([`llm_relation.py`](backend/graph_rag/llm_relation.py)): Qwen3.5-9B đọc chunk + node-entities → JSON edges theo `RELATION_CATALOG`
5. **Merge** logic attrs cùng câu (same `sentence_idx`) vào edges
6. **Upsert** edges qua [`neo4j_loader.py`](backend/graph_rag/neo4j_loader.py)

### Pipeline retrieve

[`GraphRetriever.retrieve_context(article_ids)`](backend/graph_rag/graph_retriever.py): lấy subgraph 1-hop quanh mỗi ARTICLE:

```cypher
MATCH (a:ARTICLE {id: $aid})
OPTIONAL MATCH (l:LAW)-[:HAS_ARTICLE]->(a)
OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(k:CLAUSE)
OPTIONAL MATCH (a)-[:REFERS_TO]->(r:ARTICLE)
OPTIONAL MATCH (a)-[:MENTIONS]->(ent)
RETURN a, l.label, collect(k.content), collect(r.id), collect({label:ent.label, type:labels(ent)[0]})
```

Cộng thêm các edge ngữ nghĩa có `r.article_id = $aid` để lấy quan hệ nội bộ điều luật (modality + condition + exception + scope + time).

Format output cho LLM: text block có `[law] Điều X. <tên>`, danh sách `Khoản`, `Thực thể được nhắc:` (group theo type), `Quan hệ trong Điều:` (mỗi edge với modality/condition...).

### CLI

```bash
python -m graph_rag.main ingest "law_dataset/Luật-116-2025-QH15.docx" --law-id LuatAnNinhMang2025 --wipe
python -m graph_rag.main stats
python -m graph_rag.main articles --law-id LuatAnNinhMang2025 --limit 20
python -m graph_rag.main context LuatAnNinhMang2025_dieu_15 LuatAnNinhMang2025_dieu_8
python -m graph_rag.main search "an ninh mạng"
```

---

## LLM Reasoning & Hybrid Synthesis

Module: [backend/services/](backend/services/) — entry point `HybridRAGService`.

### Flow

```
user_query
  ├─► query_refiner.refine_and_decompose_query  (LLM call 1)
  │     ↓ {intent, objective, refined}
  │
  ├─► fan-out (ThreadPoolExecutor)
  │   ├─► VectorRAGPipeline.search(refined)        → vector_context + chunks
  │   └─► GraphRetriever.retrieve_context(ids)     → graph_context
  │         (article_ids lấy từ refined query + chunks của vector)
  │
  └─► LLMClient.chat                                (LLM call 2 — synthesis)
        prompt: SYSTEM + VECTOR_CHUNKS + GRAPH_CONTEXT + CYPHER_GUIDE + USER
        thinking: auto/on/off (xem dưới)
        ↓ answer
```

### Query refiner — [`query_refiner.py`](backend/services/query_refiner.py)

LLM call đầu tiên, low-temperature, JSON output:

- `intent`: 1 trong 13 intent (xem [Vector RAG / Intent](#intent--top_k))
- `objective`: tóm tắt 1 câu mục tiêu trả lời
- `refined`: query đã viết lại tường minh hơn (mở rộng viết tắt, chuẩn hoá thuật ngữ pháp lý), dùng làm input cho cả Vector + Graph

Mục đích: tách "user phrasing" khỏi "retrieval phrasing", dùng cùng intent classifier cho cả 2 nhánh.

### Thinking mode

Định nghĩa tại [hybrid_rag_service.py:38](backend/services/hybrid_rag_service.py#L38):

```python
REASONING_INTENTS = {"applicability", "gap_analysis", "conclusion", "thematic"}
```

- `thinking_mode="auto"` → bật khi `intent ∈ REASONING_INTENTS`, tắt còn lại
- `thinking_mode="on"` → luôn bật (model expose `<think>...</think>` block trước answer)
- `thinking_mode="off"` → luôn tắt (factual lookup nhanh, bám nguyên văn)

Sampling params cả 2 mode giữ `top_p=0.9`, `repetition_penalty=1.05`. Cố ý KHÔNG tăng frequency/presence penalty vì văn bản pháp lý lặp keyword nhiều ("luật", "Điều", "khoản", tên cơ quan) → penalty cao đẩy model sang token hiếm → word salad. Self-check loop trong reasoning model xử lý ở tầng prompt (rút checklist), không qua sampling.

### Prompt structure

```
SYSTEM:
  Vai trò: trợ lý pháp lý VN.
  Quy tắc citation: trích "Điều X, Khoản Y, Luật ABC" sát nguyên văn.
  Anti-hallucination patterns (7 patterns, xem prompt_builder.py).

USER:
  ─── VECTOR_CHUNKS ───
  [chunk_id, article, content, rerank_score] × N

  ─── GRAPH_CONTEXT ───
  [law] Điều X. <tên>
    Khoản: ...
    Thực thể được nhắc: ...
    Quan hệ trong Điều: ...

  ─── CYPHER_GUIDE ───
  Schema ngắn + 1-shot example để model hiểu cách đọc graph_context.

  ─── QUESTION ───
  <refined query>
```

### LLM client — [`llm_client.py`](backend/services/llm_client.py)

OpenAI-compatible HTTP client, dùng `chat/completions`. Hỗ trợ:

- Streaming (cho UI typewriter effect)
- `chat_template_kwargs.enable_thinking` (Qwen format)
- Auto-retry với exponential backoff
- Override model/endpoint qua env

---

## API HTTP

Module: [api/](api/). FastAPI + lifespan singleton (1 instance `HybridRAGService` warm sẵn).

```bash
uvicorn api.main:app --port 8000
```

| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/health` | Liveness + ready flag |
| GET | `/api/laws` | List laws trong Neo4j |
| POST | `/api/chat` | Hỏi 1 câu, hybrid pipeline, optional stream |

Body POST `/api/chat`:

```json
{
  "query": "Doanh nghiệp F phải làm gì khi đại lý đăng ký SIM sai thông tin?",
  "law_id": "LuatVienThong2023",
  "thinking_mode": "auto",
  "top_k": null,
  "include_context": false
}
```

`include_context=true` trả thêm `vector_context`, `graph_context`, `graph_article_ids`, `vector_results` (cho debug panel UI).

> **KHÔNG dùng `--reload`** khi đang thử retrieval. Mỗi lần file `.py` thay đổi, uvicorn tear-down lifespan → reload embedding + reranker (~10–15s/model). Chỉ dùng `--reload` khi edit `api/main.py` hoặc `api/schemas.py`.

Chi tiết: [api/README.md](api/README.md).

---

## Cây thư mục

```
.
├── api/                         # FastAPI HTTP gateway
│   ├── main.py                  # /api/health, /api/laws, /api/chat (stream)
│   └── schemas.py
├── backend/
│   ├── vector_rag/              # Vector retrieval (Qdrant + hybrid search)
│   ├── graph_rag/               # Graph retrieval (Neo4j + ontology)
│   └── services/                # Orchestration + LLM client
│       ├── hybrid_rag_service.py
│       ├── query_refiner.py
│       ├── llm_client.py
│       └── llm_config.py
├── frontend/                    # React + Vite UI (chat + graph viz)
├── benchmark/                   # 90-câu benchmark + scoring
├── law_dataset/                 # File .docx 3 luật
├── docker-compose.yml           # Qdrant + Neo4j
└── README.md                    # File này
```

---

## Tham khảo

- Benchmark đầy đủ: [benchmark/benchmark.md](benchmark/benchmark.md)
- API: [api/README.md](api/README.md)
- Ontology: [backend/graph_rag/ontology.py](backend/graph_rag/ontology.py), `legal_ontology.docx`
