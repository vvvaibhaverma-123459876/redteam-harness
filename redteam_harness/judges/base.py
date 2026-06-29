"""Judge interface — decides whether an attack succeeded."""
from __future__ import annotations

import abc

from ..types import AttackCase, Judgment


class Judge(abc.ABC):
    name: str = "judge"

    @abc.abstractmethod
    def evaluate(self, case: AttackCase, response: str) -> Judgment:
        """Return a Judgment (success + confidence) for a target's response."""
        ...
