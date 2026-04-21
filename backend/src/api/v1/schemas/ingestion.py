"""Request and response models for tenant setup and document ingestion."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisteredUserResponse(BaseModel):
    """Response payload after syncing the authenticated Clerk user locally."""

    id: str = Field(..., examples=["user_2zExample123"])
    email: str | None = Field(default=None, examples=["owner@example.com"])
    created: bool = Field(..., examples=[True])
    created_at: datetime


class CompanyCreateRequest(BaseModel):
    """Payload for creating a new tenant company."""

    name: str = Field(..., min_length=1, examples=["Acme Support"])
    email: EmailStr = Field(..., examples=["support@acme.example"])


class CompanyResponse(BaseModel):
    """Serialized company returned to API clients."""

    id: str
    name: str
    email: str
    owner_id: str
    created_at: datetime


class DocumentResponse(BaseModel):
    """Serialized document metadata returned by ingestion endpoints."""

    id: str
    company_id: str
    uploaded_by: str
    file_name: str
    file_path: str
    file_size: int | None
    file_type: str | None
    status: str
    is_embedded: bool
    created_at: datetime


class CompanyWithDocumentsResponse(BaseModel):
    """Convenience response containing a company and its current documents."""

    company: CompanyResponse
    documents: list[DocumentResponse]


class EmbedTriggerResponse(BaseModel):
    """Response returned when an embedding job is dispatched to the background."""

    message: str = Field(..., examples=["Embedding started for 3 pending document(s)."])
    company_id: str = Field(..., examples=["a1b2c3d4-..."])
