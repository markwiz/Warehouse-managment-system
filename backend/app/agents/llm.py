"""Chat model factory. All agents should obtain their model from here."""

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from app.core.config import get_settings


@lru_cache
def get_chat_model() -> ChatAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
        max_tokens=16000,
    )
