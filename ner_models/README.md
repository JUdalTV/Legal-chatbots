---
language:
- vi
license: mit
tags:
- token-classification
- ner
- vietnamese
- legal
- electra
- transformers
base_model: NlpHUST/ner-vietnamese-electra-base
datasets:
- NTA1802/NER-Completing-With-Legal-Dataset
metrics:
- seqeval
pipeline_tag: token-classification
---

# NER — Vietnamese Legal Domain (Electra-base)

Mô hình **Named Entity Recognition (NER)** cho văn bản pháp lý tiếng Việt, fine-tune từ [`NlpHUST/ner-vietnamese-electra-base`](https://huggingface.co/NlpHUST/ner-vietnamese-electra-base) trên bộ dữ liệu pháp lý tự xây dựng với **BIO tagging scheme**, **63 loại thực thể** và **125 nhãn** (1 `O` + các tag B-/I-; riêng `ARTICLE` và `LOCATION` chỉ xuất hiện dạng `B-`).

Phạm vi: **3 luật** — Luật Viễn thông, Luật An ninh mạng, Luật Công nghệ thông tin (cùng các văn bản hướng dẫn liên quan).

## Các loại thực thể nhận dạng

125 nhãn BIO (1 `O` + 62 loại × 2 prefix B/I) thuộc 7 nhóm: văn bản pháp lý, chủ thể, khái niệm pháp lý, an ninh mạng, hạ tầng & kỹ thuật, tiêu chuẩn & quy định, và các thực thể khác (địa điểm, thời gian, mức độ...).

## Kỹ thuật fine-tune

- **Subword label alignment** — chỉ gán nhãn cho first subtoken, các subtoken còn lại dùng `-100`
- **Mixed precision (bf16)** + **TF32** — tối ưu tốc độ trên GPU Ampere/Hopper
- **Layer-wise Learning Rate Decay (LLRD)** với decay factor `0.9` — backbone LR `3e-5`, classifier head LR `1e-4`
- **Linear warmup + decay** (`warmup_ratio=0.1`), **weight decay** `0.01`, **gradient clipping** `1.0`
- **Label smoothing** `0.1`
- **Early stopping** theo `eval_f1` (seqeval entity-level), patience `5`
- **Dynamic padding** với `DataCollatorForTokenClassification`
- **Reproducible seed** `42`

## Dữ liệu huấn luyện

| Split | Số câu |
|---|---|
| Train | 6 403 |
| Validation | 1 279 |
| Test | 1 288 |

Dataset: JSONL format, mỗi dòng gồm `tokens` (list) và `labels` (list BIO labels) — ngoài ra có thêm `id` và `sentence`. Lưu ý `tokens` đã được **word-tokenize** sẵn (token dạng `Bộ_Công_an`, `an_ninh_mạng`).

## Kết quả đánh giá

Train 30 epoch (early stopping theo `eval_f1`), GPU NVIDIA RTX PRO 6000 Blackwell, ~262 s — `train_loss ≈ 1.09` (đã gồm label smoothing 0.1). Metric **seqeval entity-level**:

| Split | Precision | Recall | F1 |
|---|---|---|---|
| Validation | 0.9965 | 0.9970 | **0.9968** |
| Test | 0.9960 | 0.9976 | **0.9968** |

Trên tập **test** (7 804 thực thể), theo `classification_report`:

| | Precision | Recall | F1 |
|---|---|---|---|
| micro avg | 0.9960 | 0.9976 | 0.9968 |
| macro avg | 0.9896 | 0.9963 | 0.9926 |
| weighted avg | 0.9961 | 0.9976 | 0.9968 |

Phần lớn entity type đạt F1 = 1.0. Các type có support lớn: `OBLIGATION` (1079, F1 1.00), `LEGAL_ACTOR` (1025, F1 0.996), `LEGAL_ACTION` (940, F1 0.997), `LAW` (690, F1 1.00), `TIME` (556, F1 0.998), `SANCTION` (485, F1 0.998), `SYSTEM` (327, F1 0.989). Các type F1 thấp nhất đều thuộc nhóm support rất nhỏ: `AUTHORIZATION` (0.857, support 3), `AUDIT` (0.933, 7), `LICENSE` (0.947, 19), `LEGAL_CONCEPT` (0.952, 31), `PERMISSION` (0.964, 28).

> ⚠️ F1 ≈ 0.997 phản ánh dữ liệu được sinh khá theo khuôn mẫu (template) — số liệu trên domain văn bản pháp lý thực tế, đa dạng hơn, sẽ thấp hơn đáng kể.

## Cách sử dụng

> ⚠️ **Quan trọng:** model được train trên dữ liệu đã **word-tokenize** (token dạng
> `Bộ_Công_an`, `an_ninh_mạng`, ...). Khi inference **bắt buộc** phải word-tokenize trước
> rồi truyền với `is_split_into_words=True` — nếu truyền raw text thẳng vào tokenizer/`pipeline`,
> entity sẽ lệch hoàn toàn.

```python
import torch
from pyvi import ViTokenizer
from transformers import AutoTokenizer, AutoModelForTokenClassification

MODEL_DIR = "NTA1802/NER-Completing-With-Legal-Dataset"
tok = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
mdl = AutoModelForTokenClassification.from_pretrained(MODEL_DIR).eval()
id2label = mdl.config.id2label

@torch.no_grad()
def extract_entities(text: str):
    words = ViTokenizer.tokenize(text).split()
    enc = tok(words, is_split_into_words=True, return_tensors="pt", truncation=True)
    pred_ids = mdl(**enc).logits[0].argmax(-1).tolist()
    word_ids = enc.word_ids(0)

    word_label = [None] * len(words)
    seen = set()
    for j, wid in enumerate(word_ids):
        if wid is None or wid in seen:
            continue
        seen.add(wid)
        word_label[wid] = id2label[pred_ids[j]]

    entities, cur = [], None
    for w, lab in zip(words, word_label):
        if lab in (None, "O"):
            if cur: entities.append(cur); cur = None
            continue
        prefix, _, etype = lab.partition("-")
        if prefix == "B" or cur is None or cur["type"] != etype:
            if cur: entities.append(cur)
            cur = {"type": etype, "text": w.replace("_", " ")}
        else:
            cur["text"] += " " + w.replace("_", " ")
    if cur: entities.append(cur)
    return entities

print(extract_entities("Khoản 1 Điều 46 Luật An ninh mạng quy định về bảo vệ dữ liệu cá nhân."))
```

## Thông tin mô hình

- **Base model:** `NlpHUST/ner-vietnamese-electra-base` (ELECTRA-base, 12 layers, hidden 768)
- **Số nhãn:** 125 (BIO scheme — 63 entity types)
- **Max sequence length:** 512
- **Framework:** PyTorch + HuggingFace Transformers ≥ 4.41
- **Ngôn ngữ:** Tiếng Việt (văn bản pháp lý — viễn thông, an ninh mạng, công nghệ thông tin)
