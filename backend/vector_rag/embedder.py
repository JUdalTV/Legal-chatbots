"""
embedder.py
Dense embedding qua AITeamVN/Vietnamese_Embedding (fp16 trên GPU).

API:
    emb = Embedder(device="gpu")           # auto cuda → fp16
    vecs = emb.encode(["text1", ...])      # list[list[float]]
    n    = emb.count_tokens("text")        # int — dùng cho chunker
    d    = emb.dim                         # vector dimension

Module-level singleton: nhiều VectorRAGPipeline có cùng (device, use_half)
sẽ dùng chung 1 SentenceTransformer trong RAM → không reload weights.
"""
from __future__ import annotations

import threading
from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer


# (device, use_half) → SentenceTransformer cache toàn process.
_MODEL_CACHE: dict[tuple[str, bool], SentenceTransformer] = {}
_MODEL_LOCK = threading.Lock()


class Embedder:
    """Wrapper SentenceTransformer + fp16 + tokenizer-based token counter."""

    MODEL_NAME = "AITeamVN/Vietnamese_Embedding"

    def __init__(self, device: str = "gpu", use_half: bool = True):
        self.device = self._resolve_device(device)
        self.use_half = use_half and self.device.startswith("cuda")
        self._model: Optional[SentenceTransformer] = None

    # ── Device ──────────────────────────────────────────────────────
    @staticmethod
    def _resolve_device(device: str) -> str:
        d = (device or "").strip().lower()
        if d in {"gpu", "cuda", "cuda:0"}:
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA không khả dụng. Truyền device='cpu' nếu chạy không GPU."
                )
            return "cuda"
        return d or "cpu"

    # ── Lazy load (process-wide singleton) ─────────────────────────
    def _load(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        key = (self.device, self.use_half)
        with _MODEL_LOCK:
            cached = _MODEL_CACHE.get(key)
            if cached is not None:
                print(f"[Embedder] reuse cached {self.MODEL_NAME} on {self.device}")
                self._model = cached
                return self._model
            print(f"[Embedder] LOADING {self.MODEL_NAME} on {self.device} (fp16={self.use_half})…")
            kwargs: dict = {}
            if self.use_half:
                kwargs["dtype"] = torch.float16  # `torch_dtype` deprecated
            model = SentenceTransformer(
                self.MODEL_NAME,
                device=self.device,
                trust_remote_code=True,
                model_kwargs=kwargs,
            )
            _MODEL_CACHE[key] = model
            self._model = model
            print(f"[Embedder] LOADED  {self.MODEL_NAME}")
        return self._model

    # ── Encode ─────────────────────────────────────────────────────
    def encode(
        self,
        texts: List[str],
        batch_size: int = 24,
        show_progress: bool = True,
    ) -> List[List[float]]:
        if not texts:
            return []
        m = self._load()
        vecs = m.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        return [v.tolist() for v in vecs]

    # ── Token counter (dùng tokenizer của embedder) ────────────────
    def count_tokens(self, text: str) -> int:
        m = self._load()
        # SentenceTransformer.tokenize trả dict tensors → lấy input_ids[0]
        ids = m.tokenize([text])["input_ids"][0]
        return int(len(ids))

    @property
    def dim(self) -> int:
        m = self._load()
        getter = (
            getattr(m, "get_embedding_dimension", None)
            or getattr(m, "get_sentence_embedding_dimension", None)
        )
        if getter is None:
            raise RuntimeError("SentenceTransformer missing embedding-dim getter")
        return int(getter())
