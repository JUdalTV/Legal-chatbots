"""
embedder.py
Dense embedding qua AITeamVN/Vietnamese_Embedding (fp16 trên GPU).

API:
    emb = Embedder(device="gpu")           # auto cuda → fp16
    vecs = emb.encode(["text1", ...])      # list[list[float]]
    n    = emb.count_tokens("text")        # int — dùng cho chunker
    d    = emb.dim                         # vector dimension
"""
from __future__ import annotations

from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer


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

    # ── Lazy load ──────────────────────────────────────────────────
    def _load(self) -> SentenceTransformer:
        if self._model is None:
            kwargs = {}
            if self.use_half:
                kwargs["torch_dtype"] = torch.float16
            self._model = SentenceTransformer(
                self.MODEL_NAME,
                device=self.device,
                trust_remote_code=True,
                model_kwargs=kwargs,
            )
            if self.use_half:
                self._model.half()
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
        return int(self._load().get_sentence_embedding_dimension())
