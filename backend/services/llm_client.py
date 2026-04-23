"""
graph_rag/services/llm_client.py
Client gọi LLM (Gemini / OpenAI / Anthropic) để sinh câu trả lời.
"""

from __future__ import annotations
import os


class LLMClient:
    """
    Wrapper LLM. Mặc định dùng Google Gemini.
    Đổi provider bằng env LLM_PROVIDER=openai|anthropic|gemini
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini")
        self.model    = os.getenv("LLM_MODEL",    "gemini-2.0-flash")
        self.api_key  = os.getenv("LLM_API_KEY",  "")

    def chat(self, messages: list[dict], max_tokens: int = 2048) -> str:
        """
        messages: [{"role": "system"|"user"|"assistant", "content": str}]
        Trả về content string.
        """
        if self.provider == "gemini":
            return self._gemini(messages, max_tokens)
        elif self.provider == "openai":
            return self._openai(messages, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic(messages, max_tokens)
        else:
            raise ValueError(f"LLM provider không hỗ trợ: {self.provider}")

    # ── Gemini ────────────────────────────────────────────────────
    def _gemini(self, messages: list[dict], max_tokens: int) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        # Chuyển messages sang Gemini format
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        history = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})

        chat = model.start_chat(history=history[:-1])
        response = chat.send_message(
            history[-1]["parts"][0],
            generation_config={"max_output_tokens": max_tokens}
        )
        return response.text

    # ── OpenAI ────────────────────────────────────────────────────
    def _openai(self, messages: list[dict], max_tokens: int) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai")

        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    # ── Anthropic ─────────────────────────────────────────────────
    def _anthropic(self, messages: list[dict], max_tokens: int) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        resp = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=user_msgs,
        )
        return resp.content[0].text