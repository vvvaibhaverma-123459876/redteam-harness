"""Input sanitizer: neutralize injection markers in untrusted turns.

Strips/escapes the control phrases and structural tokens that injection and
indirect-injection attacks rely on, and flattens obvious obfuscation (spacing,
fake delimiters). This is a *defense under test* — the harness shows how much it
helps, and the obfuscation mutators exist precisely to probe its blind spots.
"""
from __future__ import annotations

import re
from typing import List

from ..types import Message
from .base import Defense

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"ignore your system prompt",
    r"system override",
    r"developer mode",
    r"you are dan",
    r"</?system>",
    r"new instructions:",
]


class InputSanitizer(Defense):
    name = "input_sanitizer"

    def __init__(self):
        self._regexes = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def _clean(self, text: str) -> str:
        collapsed = re.sub(r"(?<=\w)\s(?=\w\b)", "", text)  # undo "i g n o r e" spacing
        cleaned = collapsed
        for rx in self._regexes:
            cleaned = rx.sub("[removed-injection-attempt]", cleaned)
        return cleaned

    def transform_input(self, messages: List[Message]) -> List[Message]:
        out: List[Message] = []
        for m in messages:
            if m.role == "system":
                out.append(m)  # trust the system prompt; sanitize only user/tool content
            else:
                out.append(Message(m.role, self._clean(m.content)))
        return out
