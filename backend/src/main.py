"""FastAPI application entrypoint."""

from fastapi import FastAPI

from src.api.v1.routers import agents

app = FastAPI(title="Customer Support SaaS", version="0.1.0")
app.include_router(agents.router, prefix="/api/v1")


@app.get("/health")
async def get_health() -> dict[str, str]:
    """Liveness probe for orchestrators and local checks."""
    return {"status": "ok"}