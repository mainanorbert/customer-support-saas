"""Application settings loaded from environment variables."""

from pydantic import AliasChoices, Field, field_validator
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
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        description="OpenRouter / OpenAI-compatible embedding model slug",
    )
    embedding_dimensions: int = Field(
        default=1536,
        ge=32,
        le=8192,
        description="Vector size for document_chunks.embedding; must match the embedding model output",
    )
    embedding_max_chars_per_chunk: int = Field(
        default=2000,
        ge=256,
        le=32000,
        description="Maximum characters per text chunk before embedding",
    )
    embedding_chunk_overlap_chars: int = Field(
        default=200,
        ge=0,
        le=4096,
        description="Character overlap between consecutive chunks",
    )
    embedding_api_batch_size: int = Field(
        default=64,
        ge=1,
        le=256,
        description="Maximum number of texts sent per embeddings API request",
    )
    rag_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of nearest chunks to retrieve per query",
    )
    rag_similarity_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description=(
            "Cosine similarity floor (0–1). Queries whose best chunk similarity falls below "
            "this value are considered out-of-scope and receive a polite refusal. "
            "For OpenAI text-embedding-3-* models, relevant matches usually score 0.35–0.6; "
            "tune via RAG_SIMILARITY_THRESHOLD in .env."
        ),
    )
    clerk_secret_key: str = Field(..., description="Clerk secret key for verifying session JWTs")
    clerk_authorized_parties: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated frontend origins allowed in Clerk session tokens (azp)",
    )
    database_url: str = Field(
        validation_alias=AliasChoices("EIVEN_SERVICE_URL", "DATABASE_URL"),
        description="Aiven PostgreSQL Service URI (postgres:// or postgresql+psycopg2://)",
    )
    upload_root: str = Field(
        default="./storage",
        description="Root directory where uploaded files are stored locally",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalize postgres:// shorthand to the SQLAlchemy psycopg2 dialect prefix."""
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v
