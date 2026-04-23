"""
embedder.py
T?o dense vector embedding t? text d?ng mainguyen9/vietlegal-harrier-0.6b.

L? do ch?n model:
  - T?i ?u cho ng? li?u ph?p l? ti?ng Vi?t
  - H? tr? semantic embedding cho truy h?i lu?t
  - Chu?n h?a vector (normalize=True) ?? d?ng COSINE similarity
"""

from __future__ import annotations
from sentence_transformers import SentenceTransformer
from typing import List
import torch


class Embedder:
    """
    Wrapper quanh SentenceTransformer vietlegal-harrier-0.6b.
    Lazy-load model khi l?n ??u g?i encode().
    """

    MODEL_NAME = "mainguyen9/vietlegal-harrier-0.6b"

    def __init__(self, device: str = "gpu", use_half: bool = True):
        self.device = self._resolve_device(device)
        self.use_half = use_half and self.device.startswith("cuda")
        self._model = None

    @staticmethod
    def _resolve_device(device: str) -> str:
        normalized = (device or "").strip().lower()

        if normalized in {"gpu", "cuda", "cuda:0"}:

            if not torch.cuda.is_available():
                raise RuntimeError(
                    "Kh?ng t?m th?y CUDA GPU. H?y ki?m tra driver/CUDA ho?c truy?n device='cpu'."
                )
            return "cuda"

        return normalized or "cpu"

    def _load(self):
        if self._model is None:
            model_kwargs = {}
            if self.use_half:
                model_kwargs["torch_dtype"] = torch.float16

            self._model = SentenceTransformer(
                self.MODEL_NAME,
                device=self.device,
                trust_remote_code=True,
                model_kwargs=model_kwargs,
            )

            if self.use_half:
                self._model.half()

    def encode(
        self,
        texts: List[str],
        batch_size: int = 16,
        show_progress: bool = True,
    ) -> List[List[float]]:
        """
        Tr? v? list vector float ?? normalize ?? search cosine.
        """
        if not texts:
            return []

        self._load()
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        return [v.tolist() for v in vectors]

    @property
    def dim(self) -> int:
        self._load()
        return int(self._model.get_sentence_embedding_dimension())
