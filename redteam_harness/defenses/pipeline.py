"""Compose multiple defenses into one input->output pipeline."""
from __future__ import annotations

from typing import List, Tuple

from ..types import Message
from .base import Defense


class DefensePipeline(Defense):
    name = "pipeline"

    def __init__(self, defenses: List[Defense]):
        self.defenses = defenses
        self.name = "+".join(d.name for d in defenses) or "none"

    def transform_input(self, messages: List[Message]) -> List[Message]:
        for d in self.defenses:
            messages = d.transform_input(messages)
        return messages

    def filter_output(self, response: str) -> Tuple[str, bool]:
        blocked_any = False
        for d in self.defenses:
            response, blocked = d.filter_output(response)
            blocked_any = blocked_any or blocked
        return response, blocked_any


def default_pipeline() -> DefensePipeline:
    """The recommended defense-in-depth stack used by the demo/CLI."""
    from .hardener import SystemPromptHardener
    from .output_filter import OutputFilter
    from .sanitizer import InputSanitizer

    return DefensePipeline([InputSanitizer(), SystemPromptHardener(), OutputFilter()])
