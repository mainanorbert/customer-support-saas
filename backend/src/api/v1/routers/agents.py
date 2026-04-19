"""HTTP routes for invoking the support agent (LLM-only)."""

from typing import Annotated

from clerk_backend_api.security.types import RequestState
from fastapi import APIRouter, Depends
from openai import AsyncOpenAI

from src.api.v1.schemas.agent import AgentChatRequest, AgentChatResponse
from src.core.clerk_auth import require_clerk_session
from src.core.config import Settings
from src.core.dependencies import get_openrouter_client, get_settings
from src.services.openrouter_agent import generate_simple_agent_reply

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/chat", response_model=AgentChatResponse)
async def post_agent_chat(
    body: AgentChatRequest,
    _session: Annotated[RequestState, Depends(require_clerk_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[AsyncOpenAI, Depends(get_openrouter_client)],
) -> AgentChatResponse:
    """Generate a one-shot support reply using OpenRouter (no retrieval)."""
    reply = await generate_simple_agent_reply(
        client=client,
        model=settings.openrouter_model,
        user_message=body.message,
    )
    return AgentChatResponse(reply=reply)