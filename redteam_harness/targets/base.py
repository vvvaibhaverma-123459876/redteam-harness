"""Target model interface — the system under test."""
from __future__ import annotations

import abc
from typing import List

from ..types import Message


class Target(abc.ABC):
    """A chat model we are red-teaming."""

    name: str = "target"

    @abc.abstractmethod
    def generate(self, messages: List[Message]) -> str:
        """Return the model's reply to a conversation."""
        ...
