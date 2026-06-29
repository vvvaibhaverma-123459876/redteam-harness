"""Attack-success judges."""
from .base import Judge
from .heuristic import HeuristicJudge

__all__ = ["Judge", "HeuristicJudge"]


def __getattr__(name: str):
    if name == "LLMJudge":
        from .llm_judge import LLMJudge

        return LLMJudge
    raise AttributeError(name)
