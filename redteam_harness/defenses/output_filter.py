"""Output filter: block replies that leak the protected secret."""
from __future__ import annotations

from typing import Tuple

from ..targets.mock import SECRET
from .base import Defense

BLOCK_MESSAGE = "[response blocked by safety filter]"


class OutputFilter(Defense):
    name = "output_filter"

    def __init__(self, secret: str = SECRET):
        self.secret = secret.lower()

    def filter_output(self, response: str) -> Tuple[str, bool]:
        if self.secret in response.lower():
            return BLOCK_MESSAGE, True
        return response, False
