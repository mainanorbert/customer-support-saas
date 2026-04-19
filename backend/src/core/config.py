"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API process."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenAI-compatible base URL for OpenRouter",
    )
    openrouter_model: str = Field(
        default="openai/gpt-4.1-mini",
        description="OpenRouter model slug for chat completions",
    )
    clerk_secret_key: str = Field(..., description="Clerk secret key for verifying session JWTs")
    clerk_authorized_parties: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated frontend origins allowed in Clerk session tokens (azp)",
    )