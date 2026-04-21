"""Services for local user sync, tenant setup, and document file ingestion."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.models import Company, Document, User, generate_uuid

DOCUMENT_STATUS_PENDING = "pending"
DOCUMENT_STATUS_PROCESSING = "processing"
DOCUMENT_STATUS_COMPLETED = "completed"
DOCUMENT_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class StoredDocumentFile:
    """Metadata captured after persisting an uploaded file to local storage."""

    file_name: str
    file_path: str
    file_size: int
    file_type: str | None


def upsert_user(session: Session, *, user_id: str, email: str | None) -> tuple[User, bool]:
    """Create or refresh the local user record that mirrors Clerk identity."""
    user = session.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=email)
        session.add(user)
        session.flush()
        return user, True

    if email and user.email != email:
        user.email = email
        session.flush()

    return user, False


def get_or_create_company(
    session: Session,
    *,
    owner_id: str,
    name: str,
    email: str,
) -> tuple[Company, bool]:
    """Return the company matching the given email, creating it if it does not exist.

    Returns a (company, created) tuple where created is True when a new row was inserted.
    If the email already belongs to another owner the existing company is returned as-is.
    """
    normalized_email = email.strip().lower()
    existing = session.query(Company).filter(Company.email == normalized_email).one_or_none()
    if existing is not None:
        return existing, False

    normalized_name = name.strip()
    if not normalized_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name cannot be empty.")

    company = Company(name=normalized_name, email=normalized_email, owner_id=owner_id)
    session.add(company)
    session.flush()
    return company, True


def list_companies_for_owner(session: Session, *, owner_id: str) -> list[Company]:
    """Return companies owned by the provided user id."""
    return (
        session.query(Company)
        .filter(Company.owner_id == owner_id)
        .order_by(Company.created_at.desc())
        .all()
    )


def get_owned_company(session: Session, *, company_id: str, owner_id: str) -> Company:
    """Return the requested company only if it belongs to the authenticated owner."""
    company = (
        session.query(Company)
        .filter(Company.id == company_id, Company.owner_id == owner_id)
        .one_or_none()
    )
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company


def list_documents(session: Session, *, company_id: str) -> list[Document]:
    """Return ingested documents for a company sorted from newest to oldest."""
    return (
        session.query(Document)
        .filter(Document.company_id == company_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def count_pending_documents(session: Session, *, company_id: str) -> int:
    """Return the number of documents awaiting embedding for the given company.

    Counts rows where ``is_embedded`` is false and ``status`` is not failed,
    matching the same predicate used by the embedding pipeline job.
    """
    return (
        session.query(Document)
        .filter(
            Document.company_id == company_id,
            Document.is_embedded.is_(False),
            Document.status != DOCUMENT_STATUS_FAILED,
        )
        .count()
    )


def ensure_document_name_is_available(session: Session, *, company_id: str, file_name: str) -> None:
    """Reject uploads that would violate the per-company file name uniqueness constraint."""
    existing = (
        session.query(Document)
        .filter(Document.company_id == company_id, Document.file_name == file_name)
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A document named '{file_name}' already exists for this company.",
        )


def sanitize_file_name(file_name: str) -> str:
    """Remove unsafe path components from an uploaded file name."""
    cleaned_name = Path(file_name).name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a name.")
    if cleaned_name in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file name is invalid.")
    return cleaned_name


def assert_pdf_upload(upload_file: UploadFile) -> None:
    """Raise HTTP 415 when the uploaded file is not a PDF.

    Checks both the filename extension and the declared MIME type so that
    non-PDF files are rejected before any bytes are written to disk.
    """
    name = upload_file.filename or ""
    mime = (upload_file.content_type or "").lower().strip()
    suffix = Path(name).suffix.lower()

    if suffix != ".pdf" or mime not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Received: name={name!r} type={mime!r}.",
        )


async def store_uploaded_document_file(
    *,
    upload_root: str,
    company_id: str,
    document_id: str,
    upload_file: UploadFile,
) -> StoredDocumentFile:
    """Persist an uploaded file under the company storage folder and return its metadata.

    Files are written to ``{upload_root}/{company_id}/{document_id}_{file_name}`` so
    each file is uniquely addressed on disk even when names are reused across document
    lifecycle (delete + re-upload).  The stored path recorded in the database uses the
    same ``storage/{company_id}/{stored_name}`` relative format defined in the schema.
    """
    original_name = upload_file.filename or ""
    safe_name = sanitize_file_name(original_name)
    target_directory = Path(upload_root).expanduser().resolve() / company_id
    target_directory.mkdir(parents=True, exist_ok=True)

    stored_name = f"{document_id}_{safe_name}"
    destination_path = target_directory / stored_name

    file_size = 0
    with destination_path.open("wb") as output_stream:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            file_size += len(chunk)
            output_stream.write(chunk)

    await upload_file.close()

    if file_size == 0:
        destination_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    relative_path = f"storage/{company_id}/{stored_name}"
    return StoredDocumentFile(
        file_name=safe_name,
        file_path=relative_path,
        file_size=file_size,
        file_type=upload_file.content_type,
    )


def create_document_record(
    session: Session,
    *,
    document_id: str,
    company_id: str,
    uploaded_by: str,
    stored_file: StoredDocumentFile,
) -> Document:
    """Insert a document metadata record for a file already saved to disk."""
    document = Document(
        id=document_id,
        company_id=company_id,
        uploaded_by=uploaded_by,
        file_name=stored_file.file_name,
        file_path=stored_file.file_path,
        file_content="",
        file_size=stored_file.file_size,
        file_type=stored_file.file_type,
        status=DOCUMENT_STATUS_PENDING,
        is_embedded=False,
    )
    session.add(document)
    session.flush()
    return document
