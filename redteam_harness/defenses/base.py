"""Defense interface.

A defense can act at two points:
  * ``transform_input``  — sanitize/rewrite the conversation before the model sees it.
  * ``filter_output``    — inspect the model's reply and optionally block it.
Defenses are composed by ``DefensePipeline``; the harness measures attack success
with and without them to quantify mitigation.
"""
from __future__ import annotations

import abc
from typing import List, Tuple

from ..types import Message


class Defense(abc.ABC):
    name: str = "defense"

    def transform_input(self, messages: List[Message]) -> List[Message]:
        return messages

    def filter_output(self, response: str) -> Tuple[str, bool]:
        """Return (possibly-rewritten response, blocked?)."""
        return response, False
