"""Anthropic-backed target (optional; requires `anthropic` and an API key)."""
from __future__ import annotations

import os
from typing import List

from ..types import Message
from .base import Target


class AnthropicTarget(Target):
    name = "anthropic"

    def __init__(self, model: str = "claude-opus-4-8", api_key: str | None = None,
                 max_tokens: int = 512):
        import anthropic

        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, messages: List[Message]) -> str:
        system = "\n".join(m.content for m in messages if m.role == "system")
        turns = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system or None,
            messages=turns,
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
