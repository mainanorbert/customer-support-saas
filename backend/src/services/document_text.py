"""Extract plain text from uploaded files stored under ``upload_root``."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


class UnsupportedDocumentFormatError(ValueError):
    """Raised when a file type is not supported for text extraction."""


def resolve_stored_document_path(*, upload_root: str, file_path: str) -> Path:
    """Map a DB ``file_path`` (``storage/{company_id}/…``) to an absolute ``Path``."""
    prefix = "storage/"
    if not file_path.startswith(prefix):
        msg = f"Unexpected file_path format (expected '{prefix}' prefix): {file_path!r}"
        raise ValueError(msg)
    relative_under_root = file_path[len(prefix) :].lstrip("/")
    return Path(upload_root).expanduser().resolve() / relative_under_root


def extract_document_text(
    *,
    upload_root: str,
    file_path: str,
    file_name: str,
    file_type: str | None,
) -> str:
    """Read a stored PDF upload from disk and return UTF-8 text suitable for chunking.

    Only PDF files are supported. Any other format raises ``UnsupportedDocumentFormatError``.
    """
    path = resolve_stored_document_path(upload_root=upload_root, file_path=file_path)
    if not path.is_file():
        msg = f"Upload file missing on disk: {path}"
        raise FileNotFoundError(msg)

    suffix = path.suffix.lower()
    mime = (file_type or "").lower()

    if suffix == ".pdf" or "pdf" in mime:
        return _extract_pdf_text(path)

    raise UnsupportedDocumentFormatError(
        f"Only PDF documents are supported for embedding: suffix={suffix!r} mime={mime!r} file={file_name!r}"
    )


def _extract_pdf_text(path: Path) -> str:
    """Return joined text from all pages of a PDF file."""
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            parts.append(extracted)
    return "\n\n".join(parts).strip()
