"""
llm_client.py
OpenAI-compatible LLM client used by service-level RAG pipelines.
"""

from __future__ import annotations

import os
from typing import Any

import requests


class LLMClient:
    """Small OpenAI-compatible chat/completions client."""

    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 180,
        disable_thinking: bool = True,
    ):
        self.endpoint = endpoint or os.getenv(
            "LLM_ENDPOINT", "http://100.119.186.48:8000/v1/chat/completions"
        )
        self.model = model or os.getenv("LLM_MODEL", "Qwen/Qwen3.5-9B")
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "")
        self.timeout = timeout
        self.disable_thinking = disable_thinking

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        extra_payload: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.disable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        if extra_payload:
            payload.update(extra_payload)

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_text(data)


def _extract_text(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    choice = choices[0]
    message = choice.get("message") if isinstance(choice, dict) else None
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning
        reasoning_content = message.get("reasoning_content")
        if isinstance(reasoning_content, str) and reasoning_content.strip():
            return reasoning_content
    text = choice.get("text") if isinstance(choice, dict) else None
    return text if isinstance(text, str) else ""

