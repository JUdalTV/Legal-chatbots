# Legal-chatbots API

HTTP gateway cho `HybridRAGService` (Vector RAG + Graph RAG + LLM synthesis).

## Cài đặt

```bash
pip install -r api/requirements.txt
# (đã có sẵn backend/requirements.txt cài trước đó)
```

## Chạy

Đảm bảo Qdrant + Neo4j + LLM endpoint đã sẵn sàng (xem `backend/.env`).

```bash
uvicorn api.main:app --reload --port 8000
```

Service khởi tạo `HybridRAGService` 1 lần ở startup (load reranker / embeddings / Neo4j),
nên lần đầu sẽ chậm. Sau đó mỗi request `/api/chat` chỉ trả ngay kết quả.

## Endpoints

| Method | Path           | Mô tả                                         |
|--------|----------------|-----------------------------------------------|
| GET    | `/api/health`  | Liveness + ready flag                         |
| GET    | `/api/laws`    | Danh sách luật trong Neo4j (id + label)       |
| POST   | `/api/chat`    | Hỏi 1 câu, trả lời + refined + (optional) context |

### POST /api/chat — body

```json
{
  "query": "Doanh nghiệp F phải làm gì khi đại lý đăng ký SIM sai thông tin?",
  "law_id": "LuatVienThong2023",
  "thinking_mode": "auto",
  "top_k": null,
  "include_context": false
}
```

- `thinking_mode`: `"auto"` (theo intent), `"on"` (luôn bật), `"off"` (luôn tắt).
- `law_id`: nếu null → search toàn bộ luật.
- `include_context`: true → trả thêm `vector_context`, `graph_context`,
  `graph_article_ids`, `vector_results` (cho UI hiển thị panel debug).

### Biến môi trường tuỳ chọn

| Var                  | Default                                | Ghi chú                       |
|----------------------|----------------------------------------|-------------------------------|
| `QDRANT_HOST`        | localhost                              |                               |
| `QDRANT_PORT`        | 6333                                   |                               |
| `NEO4J_URI`          | bolt://localhost:7687                  |                               |
| `NEO4J_USER`         | neo4j                                  |                               |
| `NEO4J_PASSWORD`     | 12345678                               |                               |
| `RAG_DEVICE`         | gpu                                    | `cpu` nếu không có CUDA        |
| `API_CORS_ORIGINS`   | `http://localhost:5173,http://127.0.0.1:5173` | comma-separated         |
