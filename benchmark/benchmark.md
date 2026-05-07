# Benchmark Report — Hybrid RAG Legal Chatbot

## Tổng quan hệ thống

- **Model LLM**: Qwen/Qwen3.5-9B (vLLM, OpenAI-compatible)
- **Embedding**: AITeamVN/Vietnamese_Embedding (fp16)
- **Reranker**: AITeamVN/Vietnamese_Reranker (fp16)
- **Vector DB**: Qdrant (INT8 quantization + fp32 rescore)
- **Graph DB**: Neo4j 5 Community (APOC)
- **NER**: Fine-tuned NlpHUST/electra-vi
- **Architecture**: Hybrid RAG (Vector + Graph song song → LLM synthesis)

---

## Kết quả tổng hợp

### Điểm trung bình 3 luật (90 câu hỏi)

| Metric | Score | Đánh giá |
|--------|:-----:|----------|
| **Composite** | **0.717** | Tốt |
| **Citations Accuracy** | **0.957** | Xuất sắc |
| **Faithfulness** | **0.812** | Tốt |
| **ROUGE-L F1** | **0.591** | Khá |
| **Semantic Similarity** | **0.824** | Tốt |
| **Exact Match** | **0.033** | Thấp (bình thường — model paraphrase) |

### Theo từng luật

| Metric | Luật ANM 2025 | Luật Viễn thông 2023 | Luật CNTT (VBHN) |
|--------|:---:|:---:|:---:|
| **Composite** | **0.755** | 0.715 | 0.682 |
| **Citations** | **1.000** | 0.922 | 0.950 |
| **Faithfulness** | **0.862** | 0.814 | 0.760 |
| **ROUGE-L** | **0.644** | 0.588 | 0.541 |
| **Semantic Sim** | **0.853** | 0.828 | 0.791 |

### Theo độ khó (trung bình 3 luật)

| Difficulty | Composite | ROUGE-L | Citations | Faithfulness |
|:----------:|:---------:|:-------:|:---------:|:------------:|
| Easy | 0.687 | 0.593 | 0.933 | 0.692 |
| Medium | 0.737 | 0.620 | 0.983 | 0.842 |
| **Hard** | **0.727** | **0.560** | **0.972** | **0.902** |

> Hard có faithfulness cao nhất (0.90) — model xử lý tốt câu hỏi phức tạp nhờ graph context bổ trợ.

---

## Chi tiết từng luật

### 1. Luật An ninh mạng 2025 (116/2025/QH15)

**30 câu | Composite = 0.755**

| Difficulty | Count | Composite | ROUGE-L | Citations | Faithfulness |
|:----------:|:-----:|:---------:|:-------:|:---------:|:------------:|
| Easy | 10 | 0.718 | 0.618 | 1.000 | 0.742 |
| Medium | 10 | 0.761 | 0.665 | 1.000 | 0.867 |
| Hard | 10 | 0.784 | 0.650 | 1.000 | 0.978 |

**Điểm mạnh:**
- Citations = 100% toàn bộ 30 câu — retrieval pipeline hoàn hảo
- Hard faithfulness = 0.978 — gần như không hallucinate
- 8 câu đạt composite > 0.8

**Điểm yếu:**
- easy_03 (0.39): Hỏi "bao nhiêu cấp" → model vẫn liệt kê chi tiết dù đã fix prompt
- easy_10 (0.60): Model trả lời đúng nhưng thêm thông tin Điều 45 (chuyển tiếp)

---

### 2. Luật Viễn thông 2023 (24/2023/QH15)

**30 câu | Composite = 0.715**

| Difficulty | Count | Composite | ROUGE-L | Citations | Faithfulness |
|:----------:|:-----:|:---------:|:-------:|:---------:|:------------:|
| Easy | 10 | 0.727 | 0.690 | 0.900 | 0.680 |
| Medium | 10 | 0.716 | 0.575 | 0.950 | 0.841 |
| Hard | 10 | 0.703 | 0.498 | 0.917 | 0.922 |

**Điểm mạnh:**
- Easy ROUGE-L cao nhất (0.69) — model trả lời ngắn gọn sát ground truth
- 5 câu đạt composite > 0.8 (Q003, Q007, Q009, Q010, Q019)
- Q017/Q018 đã fix (trước đó 0 điểm)

**Điểm yếu:**
- Q006 (0.27): Chunk Điều 2 (đối tượng áp dụng) không tìm được — lỗi retrieval
- Q029 (0.50): Câu hỏi phân tích phức tạp, model thiếu thông tin

---

### 3. Luật CNTT — Văn bản hợp nhất (65/VBHN-VPQH)

**30 câu | Composite = 0.682**

| Difficulty | Count | Composite | ROUGE-L | Citations | Faithfulness |
|:----------:|:-----:|:---------:|:-------:|:---------:|:------------:|
| Easy | 10 | 0.617 | 0.472 | 0.900 | 0.653 |
| Medium | 10 | 0.733 | 0.621 | 1.000 | 0.820 |
| Hard | 10 | 0.695 | 0.531 | 0.950 | 0.807 |

**Điểm mạnh:**
- Medium citations = 100% — retrieval tốt cho câu hỏi trung bình
- 4 câu đạt composite > 0.75 (Q005, Q012, Q013, Q022)
- Cải thiện lớn so với lần đầu (0.46 → 0.68)

**Điểm yếu:**
- Q006 (0.25): Giống Luật VT — chunk Điều áp dụng không tìm được
- Easy faithfulness thấp (0.65): Ground truth ngắn, model vẫn verbose hơn cần thiết
- Q001 ROUGE thấp (0.20): Hỏi hiệu lực nhưng model trả lời dài

---

## Tiến trình cải thiện

### Trước và sau optimization

| Giai đoạn | Composite | Citations | Faithfulness | ROUGE-L |
|-----------|:---------:|:---------:|:------------:|:-------:|
| Baseline (lần 1) | 0.600 | 0.675 | 0.652 | 0.521 |
| Fix retrieval + re-ingest | 0.635 | 0.957 | 0.724 | 0.386 |
| Fix prompt (ngắn gọn) | **0.717** | **0.957** | **0.812** | **0.591** |

### Các thay đổi đã thực hiện

1. **Fix chunking văn bản hợp nhất** → Citations CNTT: 0.28 → 0.95
2. **Re-ingest Luật VT** → Q017/Q018 từ 0 → 0.72/0.77
3. **Prompt tuning** (trả lời ngắn gọn, đúng trọng tâm) → ROUGE +53%, Faithfulness +12%

---

## Phân tích lỗi

### Lỗi phổ biến

| Loại lỗi | Tần suất | Ảnh hưởng | Ví dụ |
|-----------|:--------:|:---------:|-------|
| Retrieval miss (chunk không tìm thấy) | 3/90 | Citations = 0 | Q006 VT, Q006 CNTT |
| Over-generation (thêm thông tin không hỏi) | ~15/90 | Faithfulness giảm | easy_03 ANM, Q001 CNTT |
| Paraphrase khác ground truth | ~20/90 | ROUGE thấp | Không phải lỗi thực sự |

### Câu hỏi có điểm thấp nhất (< 0.5)

| ID | Luật | Composite | Nguyên nhân |
|----|------|:---------:|-------------|
| easy_03 ANM | ANM | 0.389 | Hỏi "bao nhiêu cấp" → model liệt kê chi tiết cả 5 cấp |
| Q006 VT | VT | 0.270 | Chunk Điều 2 không tìm được |
| Q006 CNTT | CNTT | 0.248 | Chunk Điều áp dụng không tìm được |
| Q029 VT | VT | 0.496 | Câu phân tích phức tạp, thiếu context |

---

## Giải thích metrics

| Metric | Cách tính | Ý nghĩa |
|--------|-----------|---------|
| **Citations** | Parse "Điều X, Khoản Y" từ model_answer → so với reference | Model có trích dẫn đúng điều khoản không |
| **Faithfulness** | Mỗi câu trong answer, tính token overlap với ground_truth (≥40% = supported) | Tỷ lệ câu trả lời được hỗ trợ bởi nguồn |
| **ROUGE-L** | LCS F1 giữa ground_truth và model_answer | Overlap từ vựng (bị penalty khi answer dài) |
| **Semantic Sim** | Cosine similarity embedding (Vietnamese_Embedding) | Tương đồng ngữ nghĩa |
| **Exact Match** | Ground truth có nằm trọn trong model answer không | Trích dẫn nguyên văn |
| **Composite** | Weighted: Citations(0.25) + Faithfulness(0.25) + ROUGE(0.25) + EM(0.10) + Sim(0.15) | Điểm tổng hợp |

---

## Khuyến nghị tiếp theo

### Ưu tiên cao
1. **Fix retrieval Q006** (cả VT và CNTT): Kiểm tra chunking Điều 2 (đối tượng áp dụng) — có thể chunk quá ngắn hoặc bị merge sai
2. **Giảm verbose cho easy**: Thêm logic detect intent=lookup → append "Trả lời trong 1-2 câu" vào prompt

### Ưu tiên trung bình
3. **Pass 2 cross-chunk relations**: Thêm LLM extraction quan hệ giữa các Điều liên quan → cải thiện graph context cho câu hard
4. **Cải thiện faithfulness scoring**: Threshold 40% token overlap có thể quá nghiêm cho câu ngắn

### Ưu tiên thấp
5. **LLM-as-Judge**: Thêm metric chấm bằng LLM (0-10) để đánh giá chất lượng tổng thể chính xác hơn
6. **A/B test prompt variants**: So sánh nhiều phiên bản prompt để tìm optimal

---

## Cách chạy benchmark

```bash
# 1. Chạy model trả lời 30 câu
python benchmark_run.py benchmark_luatAnNinhMang.json --law-id LuatAnNinhMang2025
python benchmark_run.py benchmark_luatVienThong.json --law-id LuatVienThong2023
python benchmark_run.py benchmark_luatCNTT --law-id LuatCNTT2025

# 2. Chấm điểm (không cần LLM)
python benchmark_score.py benchmark_luatAnNinhMang.json --no-llm
python benchmark_score.py benchmark_luatVienThong.json --no-llm
python benchmark_score.py benchmark_luatCNTT --no-llm

# 3. Chấm có semantic similarity (cần GPU)
python benchmark_score.py benchmark_luatAnNinhMang.json --no-llm

# 4. Chấm full (có LLM judge)
python benchmark_score.py benchmark_luatAnNinhMang.json
```

---

*Báo cáo tạo ngày: $(date) | Hệ thống: Hybrid RAG v2 | 90 câu hỏi | 3 luật*
