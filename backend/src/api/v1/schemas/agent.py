"""Request and response models for the simple agent endpoint."""

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Inbound chat payload for a single-turn agent reply."""

    message: str = Field(..., min_length=1, examples=["My order arrived damaged. What should I do?"])


class AgentChatResponse(BaseModel):
    """Assistant text returned from OpenRouter (no RAG)."""

    reply: str = Field(..., examples=["I'm sorry to hear that. Please send your order number and a photo..."])