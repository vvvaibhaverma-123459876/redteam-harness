"""Target models under test."""
from .base import Target
from .mock import MockTarget

__all__ = ["Target", "MockTarget"]


def __getattr__(name: str):  # lazy imports so SDKs stay optional
    if name == "AnthropicTarget":
        from .anthropic_target import AnthropicTarget

        return AnthropicTarget
    if name == "OpenAITarget":
        from .openai_target import OpenAITarget

        return OpenAITarget
    raise AttributeError(name)


def build_target(provider: str, model: str | None = None):
    """Factory used by the CLI."""
    if provider == "mock":
        return MockTarget()
    if provider == "anthropic":
        from .anthropic_target import AnthropicTarget

        return AnthropicTarget(model=model or "claude-opus-4-8")
    if provider == "openai":
        from .openai_target import OpenAITarget

        return OpenAITarget(model=model or "gpt-4o-mini")
    raise ValueError(f"unknown provider: {provider}")
