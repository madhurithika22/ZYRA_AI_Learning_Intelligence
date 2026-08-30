import os

from app.providers.llm.base import LLMProvider
from app.providers.llm.gemini_key_router import GeminiKeyRouter
from app.providers.llm.mock_provider import MockLLMProvider


def get_llm_provider(provider_type: str | None = None) -> LLMProvider:
    """Factory function returning the configured LLM provider instance."""
    env_provider = os.getenv("LLM_PRIMARY_PROVIDER") or os.getenv("LLM_PROVIDER") or "gemini"
    selected = (provider_type or env_provider).lower()

    if selected in ("gemini", "google"):
        return GeminiKeyRouter()

    if selected == "mock":
        return MockLLMProvider()

    raise ValueError(f"Unsupported LLM provider '{selected}'. Supported providers: 'gemini', 'mock'.")
