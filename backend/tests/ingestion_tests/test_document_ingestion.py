"""API tests for tenant document ingestion (file + metadata, pre-embeddings)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_document_ingestion_persists_pending_metadata(tmp_path, monkeypatch):
    """Upload creates a pending document row, stores bytes on disk, and lists them back."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("CLERK_SECRET_KEY", "test-clerk-secret")
    db_file = tmp_path / "ingestion.db"
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_ROOT", str(upload_root))

    from clerk_backend_api.security.types import AuthStatus, RequestState
    from src.core.clerk_auth import require_clerk_session
    from src.core.dependencies import (
        get_database_engine,
        get_database_session_factory,
        get_settings,
    )

    get_settings.cache_clear()
    get_database_engine.cache_clear()
    get_database_session_factory.cache_clear()

    from src.main import app

    async def stub_require_clerk_session():
        """Return a signed-in Clerk state without calling the Clerk SDK."""
        return RequestState(
            status=AuthStatus.SIGNED_IN,
            token="test-session",
            payload={"sub": "user_ingest_test", "email": "owner@example.com"},
        )

    app.dependency_overrides[require_clerk_session] = stub_require_clerk_session
    try:
        with TestClient(app) as client:
            company_response = client.post("/api/v1/companies", json={"name": "Ingestion Test Co"})
            assert company_response.status_code == 201
            company_id = company_response.json()["id"]

            doc_response = client.post(
                f"/api/v1/companies/{company_id}/documents",
                files={"file": ("handbook.txt", b"chapter one", "text/plain")},
            )
            assert doc_response.status_code == 201
            body = doc_response.json()
            assert body["status"] == "pending"
            assert body["is_embedded"] is False
            assert body["file_name"] == "handbook.txt"
            assert body["company_id"] == company_id
            assert body["uploaded_by"] == "user_ingest_test"

            stored_path = Path(body["file_path"])
            assert stored_path.is_file()
            assert stored_path.read_bytes() == b"chapter one"

            list_response = client.get(f"/api/v1/companies/{company_id}/documents")
            assert list_response.status_code == 200
            listed = list_response.json()
            assert len(listed["documents"]) == 1
            assert listed["documents"][0]["id"] == body["id"]
    finally:
        app.dependency_overrides.clear()
