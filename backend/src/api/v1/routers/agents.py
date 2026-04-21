"""HTTP routes for the RAG-grounded customer support agent."""

from typing import Annotated

from clerk_backend_api.security.types import RequestState
from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from src.api.v1.schemas.agent import AgentChatRequest, AgentChatResponse
from src.core.clerk_auth import get_authenticated_user_identity, require_clerk_session
from src.core.config import Settings
from src.core.dependencies import get_db_session, get_openrouter_client, get_settings
from src.services.ingestion import get_owned_company, upsert_user
from src.services.openrouter_agent import generate_rag_reply
from src.services.rag_retrieval import retrieve_and_check_relevance

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/chat", response_model=AgentChatResponse)
async def post_agent_chat(
    body: AgentChatRequest,
    session_state: Annotated[RequestState, Depends(require_clerk_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[AsyncOpenAI, Depends(get_openrouter_client)],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> AgentChatResponse:
    """Generate a RAG-grounded support reply for a given company.

    Embeds the user's question, retrieves the nearest document chunks for the
    company, and checks that the best similarity meets the configured threshold.
    If the question is unrelated to the knowledge base the user is politely
    informed rather than receiving a hallucinated or off-topic answer.
    """
    identity = get_authenticated_user_identity(session_state)
    user, _created = upsert_user(db_session, user_id=identity.user_id, email=identity.email)
    company = get_owned_company(db_session, company_id=body.company_id, owner_id=user.id)
    db_session.commit()

    is_relevant, context = await retrieve_and_check_relevance(
        client,
        db_session,
        company_id=company.id,
        query=body.message,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        top_k=settings.rag_top_k,
        similarity_threshold=settings.rag_similarity_threshold,
    )

    if not is_relevant:
        return AgentChatResponse(reply=context, grounded=False)

    reply = await generate_rag_reply(
        client=client,
        model=settings.openrouter_model,
        user_message=body.message,
        context=context,
    )
    return AgentChatResponse(reply=reply, grounded=True)