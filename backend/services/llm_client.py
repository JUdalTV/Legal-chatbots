"""
llm_client.py
OpenAI-compatible LLM client used by service-level RAG pipelines.
Supports both blocking `.chat()` and streaming `.chat_stream()` modes.
"""

from __future__ import annotations

import json
from typing import Any, Iterator, Tuple

import requests

try:
    from backend.services.llm_config import (
        DEFAULT_LLM_API_KEY,
        DEFAULT_LLM_DISABLE_THINKING,
        DEFAULT_LLM_ENDPOINT,
        get_llm_model,
    )
except ImportError:
    from services.llm_config import (
        DEFAULT_LLM_API_KEY,
        DEFAULT_LLM_DISABLE_THINKING,
        DEFAULT_LLM_ENDPOINT,
        get_llm_model,
    )


# Event tuple yielded by chat_stream: (kind, text) where kind ∈ {"thinking","answer"}
StreamEvent = Tuple[str, str]


class LLMClient:
    """Small OpenAI-compatible chat/completions client."""

    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 180,
        disable_thinking: bool | None = None,
    ):
        self.endpoint = endpoint or DEFAULT_LLM_ENDPOINT
        self.model = get_llm_model(model)
        self.api_key = api_key if api_key is not None else DEFAULT_LLM_API_KEY
        self.timeout = timeout
        self.disable_thinking = (
            DEFAULT_LLM_DISABLE_THINKING
            if disable_thinking is None
            else disable_thinking
        )

    def _build_payload(
        self,
        messages: list[dict],
        *,
        temperature: float,
        max_tokens: int,
        enable_thinking: bool | None,
        thinking_budget: int | None,
        extra_payload: dict[str, Any] | None,
        stream: bool,
    ) -> dict[str, Any]:
        if enable_thinking is None:
            enable_thinking = not self.disable_thinking
        chat_template_kwargs: dict[str, Any] = {"enable_thinking": enable_thinking}
        # `thinking_budget` is honored by Qwen3 / R1-style chat templates that
        # auto-inject </think> when reasoning hits the cap, leaving the rest
        # of `max_tokens` for the visible answer.
        if enable_thinking and thinking_budget is not None:
            chat_template_kwargs["thinking_budget"] = thinking_budget
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "chat_template_kwargs": chat_template_kwargs,
        }
        if extra_payload:
            payload.update(extra_payload)
        return payload

    def _headers(self, *, stream: bool) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if stream:
            headers["Accept"] = "text/event-stream"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        enable_thinking: bool | None = None,
        thinking_budget: int | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> str:
        payload = self._build_payload(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget,
            extra_payload=extra_payload,
            stream=False,
        )
        # /chat/completions endpoints don't always accept stream=False in payload —
        # but it's standard OpenAI, fine to leave.
        resp = requests.post(
            self.endpoint,
            headers=self._headers(stream=False),
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return _extract_text(resp.json())

    def chat_stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        enable_thinking: bool | None = None,
        thinking_budget: int | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> Iterator[StreamEvent]:
        """
        Yield (kind, delta_text) tuples as tokens arrive.

        Handles BOTH conventions used by OpenAI-compatible servers:
          1. Separate `reasoning_content` / `reasoning` delta field (vLLM Qwen3 etc.)
          2. Inline `<think>...</think>` tags embedded in `content` — including the
             common Qwen/R1 case where the chat template injects the opening
             `<think>` so the model's content STARTS already inside a think
             block and only emits `</think>` partway through.
        """
        resolved_thinking = (
            (not self.disable_thinking) if enable_thinking is None else enable_thinking
        )
        payload = self._build_payload(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=resolved_thinking,
            thinking_budget=thinking_budget,
            extra_payload=extra_payload,
            stream=True,
        )
        # If thinking is enabled, assume content starts INSIDE <think>.
        splitter = _ThinkSplitter(in_think=resolved_thinking)
        with requests.post(
            self.endpoint,
            headers=self._headers(stream=True),
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                line = raw.lstrip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data in ("[DONE]", "DONE"):
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or choices[0].get("message") or {}

                # 1. Reasoning sent separately (vLLM Qwen3 thinking mode)
                reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                if isinstance(reasoning, str) and reasoning:
                    yield ("thinking", reasoning)

                # 2. Content — may contain inline <think>...</think>
                content = delta.get("content")
                if isinstance(content, str) and content:
                    for ev in splitter.feed(content):
                        yield ev
        # flush residual buffer (no closing tag arrived → treat as answer)
        for ev in splitter.flush():
            yield ev


class _ThinkSplitter:
    """
    Stateful parser that splits a streamed content string into
    ("thinking", ...) and ("answer", ...) deltas based on <think>...</think>
    tags. Safe against tags split across chunks.

    `in_think=True` indicates the stream starts already inside a think block
    (common with Qwen3 / DeepSeek-R1 chat templates that pre-emit `<think>`).
    A stray literal "<think>" while already in think state is silently
    swallowed so it doesn't appear as visible text.
    """

    OPEN = "<think>"
    CLOSE = "</think>"

    def __init__(self, in_think: bool = False) -> None:
        self.buf = ""
        self.in_think = in_think

    def feed(self, text: str) -> list[StreamEvent]:
        out: list[StreamEvent] = []
        self.buf += text
        # When in think mode, keep enough trailing chars to detect either
        # </think> (close) or a stray <think> (already-open) split across chunks.
        keep_in_think = max(len(self.CLOSE), len(self.OPEN)) - 1
        keep_in_answer = len(self.OPEN) - 1

        while self.buf:
            if not self.in_think:
                idx = self.buf.find(self.OPEN)
                if idx == -1:
                    safe = max(0, len(self.buf) - keep_in_answer)
                    if safe > 0:
                        out.append(("answer", self.buf[:safe]))
                        self.buf = self.buf[safe:]
                    break
                if idx > 0:
                    out.append(("answer", self.buf[:idx]))
                self.buf = self.buf[idx + len(self.OPEN):]
                self.in_think = True
            else:
                # If a stray <think> arrives before any </think>, swallow it.
                o_idx = self.buf.find(self.OPEN)
                c_idx = self.buf.find(self.CLOSE)
                if o_idx != -1 and (c_idx == -1 or o_idx < c_idx):
                    if o_idx > 0:
                        out.append(("thinking", self.buf[:o_idx]))
                    self.buf = self.buf[o_idx + len(self.OPEN):]
                    continue
                if c_idx == -1:
                    safe = max(0, len(self.buf) - keep_in_think)
                    if safe > 0:
                        out.append(("thinking", self.buf[:safe]))
                        self.buf = self.buf[safe:]
                    break
                if c_idx > 0:
                    out.append(("thinking", self.buf[:c_idx]))
                self.buf = self.buf[c_idx + len(self.CLOSE):]
                self.in_think = False
        return out

    def flush(self) -> list[StreamEvent]:
        if not self.buf:
            return []
        kind = "thinking" if self.in_think else "answer"
        ev: list[StreamEvent] = [(kind, self.buf)]
        self.buf = ""
        return ev


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
