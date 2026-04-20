"""Routes for syncing authenticated Clerk users into local persistence."""

from typing import Annotated

from clerk_backend_api.security.types import RequestState
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.v1.schemas.ingestion import RegisteredUserResponse
from src.core.clerk_auth import get_authenticated_user_identity, require_clerk_session
from src.core.dependencies import get_db_session
from src.services.ingestion import upsert_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=RegisteredUserResponse, status_code=status.HTTP_201_CREATED)
async def post_user_register(
    session_state: Annotated[RequestState, Depends(require_clerk_session)],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> RegisteredUserResponse:
    """Create the local user row for the signed-in Clerk user if it does not exist yet."""
    identity = get_authenticated_user_identity(session_state)
    user, created = upsert_user(db_session, user_id=identity.user_id, email=identity.email)
    db_session.commit()
    db_session.refresh(user)
    return RegisteredUserResponse(
        id=user.id,
        email=user.email,
        created=created,
        created_at=user.created_at,
    )
