"""FastAPI dependency providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI

from src.core.config import Settings
from src.services.openrouter_agent import create_openrouter_async_client


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings (env-backed, cached)."""
    return Settings()


def get_openrouter_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for OpenRouter."""
    return create_openrouter_async_client(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )