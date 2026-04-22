"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.api.v1.routers import agents, companies, users
from src.core.config import Settings
from src.core.database import Base
from src.core.dependencies import get_database_engine, get_settings
from src.core.pgvector_setup import database_url_is_postgresql, ensure_pgvector_extension
import src.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure local storage directory exists and database tables are created."""
    settings: Settings = get_settings()
    Path(settings.upload_root).expanduser().resolve().mkdir(parents=True, exist_ok=True)
    engine = get_database_engine(settings.database_url)
    if database_url_is_postgresql(settings.database_url):
        ensure_pgvector_extension(engine)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Customer Support SaaS", version="0.1.0", lifespan=lifespan)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")


@app.get("/health")
async def get_health() -> dict[str, str]:
    """Liveness probe for orchestrators and local checks."""
    return {"status": "ok"}


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/", StaticFiles(directory="static", html=True), name="static")