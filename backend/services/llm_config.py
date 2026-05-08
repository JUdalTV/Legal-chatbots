"""
Shared LLM configuration.

All runtime LLM model selection should come from backend/.env via LLM_MODEL,
or from an explicit CLI/function override.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass


DEFAULT_LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
DEFAULT_LLM_API_KEY = os.getenv("LLM_API_KEY", "")
DEFAULT_LLM_DISABLE_THINKING = os.getenv(
    "LLM_DISABLE_THINKING", "1"
).lower() not in {"0", "false", "no"}


def get_llm_model(model: str | None = None) -> str:
    value = (model or os.getenv("LLM_MODEL") or DEFAULT_LLM_MODEL).strip()
    if not value:
        raise RuntimeError(
            "LLM_MODEL is not configured. Set LLM_MODEL in backend/.env "
            "or pass --llm-model."
        )
    return value
