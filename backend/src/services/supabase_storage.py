"""Helpers for storing and retrieving document bytes in Supabase Storage."""

from __future__ import annotations

from urllib.parse import quote

import httpx

from src.core.config import Settings


class ExternalStorageError(RuntimeError):
    """Raised when the external object storage service cannot complete a request."""


def uses_supabase_storage(settings: Settings) -> bool:
    """Return True when the current settings fully configure Supabase Storage."""
    return bool(settings.supabase_url and settings.supabase_service_key)


def normalize_storage_file_path(file_path: str) -> str:
    """Validate and normalize a DB ``file_path`` into a storage object key."""
    prefix = "storage/"
    if not file_path.startswith(prefix):
        msg = f"Unexpected file_path format (expected '{prefix}' prefix): {file_path!r}"
        raise ValueError(msg)
    return file_path.lstrip("/")


def build_storage_object_url(*, settings: Settings, file_path: str) -> str:
    """Return the REST endpoint URL for a Supabase Storage object."""
    if not settings.supabase_url or not settings.supabase_service_key:
        raise ExternalStorageError("Supabase storage is not configured.")
    normalized_path = normalize_storage_file_path(file_path)
    encoded_path = quote(normalized_path, safe="/")
    return f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{encoded_path}"


def build_storage_headers(*, settings: Settings, content_type: str | None = None) -> dict[str, str]:
    """Build the server-side authorization headers for Supabase Storage requests."""
    if not settings.supabase_service_key:
        raise ExternalStorageError("Supabase service key is not configured.")
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


async def upload_file_bytes_to_supabase(
    *,
    settings: Settings,
    file_path: str,
    file_bytes: bytes,
    content_type: str | None,
) -> None:
    """Upload the provided file bytes into the configured Supabase bucket."""
    url = build_storage_object_url(settings=settings, file_path=file_path)
    headers = build_storage_headers(settings=settings, content_type=content_type or "application/octet-stream")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, content=file_bytes)
    if response.status_code not in {200, 201}:
        raise ExternalStorageError(
            f"Supabase upload failed with status {response.status_code}: {response.text[:300]}"
        )


def download_file_bytes_from_supabase(*, settings: Settings, file_path: str) -> bytes:
    """Download the full object contents for a previously stored document."""
    url = build_storage_object_url(settings=settings, file_path=file_path)
    headers = build_storage_headers(settings=settings)
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
    if response.status_code == 404:
        raise FileNotFoundError(f"Supabase object not found for file_path={file_path!r}")
    if response.status_code != 200:
        raise ExternalStorageError(
            f"Supabase download failed with status {response.status_code}: {response.text[:300]}"
        )
    return response.content


async def delete_file_from_supabase(*, settings: Settings, file_path: str) -> None:
    """Delete a stored object from Supabase, ignoring objects that are already missing."""
    url = build_storage_object_url(settings=settings, file_path=file_path)
    headers = build_storage_headers(settings=settings)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(url, headers=headers)
    if response.status_code in {200, 202, 204, 404}:
        return
    raise ExternalStorageError(f"Supabase delete failed with status {response.status_code}: {response.text[:300]}")
