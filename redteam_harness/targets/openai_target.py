"""OpenAI-backed target (optional; requires `openai` and an API key)."""
from __future__ import annotations

import os
from typing import List

from ..types import Message
from .base import Target


class OpenAITarget(Target):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None,
                 max_tokens: int = 512):
        import openai

        self.model = model
        self.max_tokens = max_tokens
        self._client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def generate(self, messages: List[Message]) -> str:
        turns = [{"role": m.role, "content": m.content} for m in messages]
        resp = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=turns,
        )
        return resp.choices[0].message.content or ""
