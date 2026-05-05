"""
sparse_encoder.py — BM25 encoder cho hybrid search trong Qdrant.

  fit(corpus)         → tính IDF + avgdl
  encode_doc(text)    → (indices, values) BM25 weights cho 1 document
  encode_query(text)  → (indices, values) chỉ IDF cho query (theo công thức BM25 chuẩn)
  save/load(path)     → JSON state để pipeline.search dùng lại

Tokenization dùng `underthesea` để bắt từ ghép tiếng Việt
("viễn thông", "doanh nghiệp", …) như 1 token.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from underthesea import word_tokenize as _ut_word_tokenize


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lower + strip punctuation + underthesea tokens (giữ '_' cho từ ghép)."""
    text = _PUNCT_RE.sub(" ", text.lower())
    return _ut_word_tokenize(text, format="text").split()


class BM25Encoder:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.vocab: dict[str, int] = {}
        self.idf:   dict[str, float] = {}
        self.avgdl: float = 0.0
        self.fitted = False

    # ────────────────────────────────────────────────────────────────
    def fit(self, corpus: Iterable[str]) -> "BM25Encoder":
        df: Counter[str] = Counter()
        total_dl = 0
        N = 0
        for doc in corpus:
            toks = tokenize(doc)
            df.update(set(toks))
            total_dl += len(toks)
            N += 1
        if N == 0:
            return self
        self.avgdl = total_dl / N
        for term, freq in df.items():
            self.vocab[term] = len(self.vocab)
            self.idf[term] = math.log(1 + (N - freq + 0.5) / (freq + 0.5))
        self.fitted = True
        return self

    # ────────────────────────────────────────────────────────────────
    def encode_doc(self, text: str) -> tuple[list[int], list[float]]:
        toks = tokenize(text)
        tf = Counter(toks)
        dl = len(toks) or 1
        ids: list[int] = []
        vals: list[float] = []
        for term, freq in tf.items():
            tid = self.vocab.get(term)
            idf = self.idf.get(term)
            if tid is None or idf is None:
                continue
            num   = freq * (self.k1 + 1)
            denom = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
            ids.append(tid)
            vals.append(idf * num / denom)
        return ids, vals

    def encode_query(self, text: str) -> tuple[list[int], list[float]]:
        """Query side: 1 lần xuất hiện = idf (BM25 query weight chuẩn)."""
        ids: list[int] = []
        vals: list[float] = []
        for term in set(tokenize(text)):
            tid = self.vocab.get(term)
            idf = self.idf.get(term)
            if tid is None or idf is None:
                continue
            ids.append(tid)
            vals.append(idf)
        return ids, vals

    # ────────────────────────────────────────────────────────────────
    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "k1":    self.k1,
            "b":     self.b,
            "avgdl": self.avgdl,
            "vocab": self.vocab,
            "idf":   self.idf,
        }, ensure_ascii=False), encoding="utf-8")

    def load(self, path: str | Path) -> "BM25Encoder":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.k1    = data["k1"]
        self.b     = data["b"]
        self.avgdl = data["avgdl"]
        self.vocab = data["vocab"]
        self.idf   = data["idf"]
        self.fitted = True
        return self


# Đường dẫn mặc định lưu state BM25 (gitignore khuyến nghị)
DEFAULT_BM25_PATH = Path(__file__).resolve().parent / "_state" / "bm25.json"
