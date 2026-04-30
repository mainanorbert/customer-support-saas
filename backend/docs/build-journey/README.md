# Build journey (V1 execution)

This page captures the current V1 build steps and execution flow for the project.

## Local setup

### Backend

```bash
cd backend
uv sync --extra dev
./scripts/migrate.sh
./scripts/dev.sh
```

The backend runs at `http://127.0.0.1:8000` and exposes `GET /health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:3000`.

## Docker run (backend)

```bash
docker compose up --build
```

Ensure backend environment variables are available before running Docker.

## Execution flow

1. Authenticate via Clerk in the frontend.
2. Create a company workspace.
3. Upload PDF documents for that company.
4. The backend stores files and triggers FastAPI background tasks to embed content.
5. Chat queries retrieve tenant-specific chunks and call OpenRouter for responses.

## Notes

- Database: Aiven PostgreSQL with pgvector.
- File storage: Supabase Storage when configured; otherwise local disk.
- Models: Text Embedding 3 Small for embeddings, GPT-4.1 Mini for chat.
