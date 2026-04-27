# System architecture

This document describes the high-level system architecture for Customer Support SaaS.

## Components

- Frontend: Next.js app that handles authentication, document management, and chat UI.
- Backend: FastAPI API that handles ingestion, embeddings, retrieval, guardrails, and persistence.
- Database: Aiven PostgreSQL with pgvector for structured data and embedding storage.
- File storage: Supabase Storage when configured, otherwise local disk.
- AI providers: OpenRouter for chat (GPT-4.1 Mini) and embeddings (Text Embedding 3 Small).

## Data flow

1. A user signs in via Clerk in the frontend.
2. The frontend calls the backend to create companies and upload PDFs.
3. The backend stores metadata in Postgres and files in Supabase Storage or local disk.
4. A FastAPI background task extracts text, chunks it, and writes embeddings to Postgres.
5. Chat requests retrieve top-k chunks for the tenant and call OpenRouter for a response.
6. Token and cost usage are recorded per user in the database.

## Architecture diagram

```mermaid
flowchart LR
  subgraph Frontend
    Web[Next.js app]
  end

  subgraph Backend
    API[FastAPI API]
    Tasks[Background tasks\n(embeddings)]
  end

  subgraph Data
    DB[(Aiven Postgres\npgvector)]
    Storage[Supabase Storage\nor local disk]
  end

  subgraph AI
    OpenRouter[OpenRouter API\nGPT-4.1 Mini]
    Embeddings[Text Embedding 3 Small]
  end

  Web -->|Auth + UI| API
  API -->|Reads/Writes| DB
  API -->|Uploads| Storage
  API -->|RAG chat| OpenRouter
  API -->|Embed docs| Embeddings
  API --> Tasks
  Tasks --> DB
```

## Tenancy and isolation

- Company data is scoped to the authenticated user and tenant.
- Retrieval queries filter by company id to avoid cross-tenant leakage.
- Background tasks operate on a single company id per run.

## Reliability and observability

- Health check: `GET /health` on the backend.
- Logging uses Python `logging` in service layers; there is no centralized logger config yet.
- Traces, metrics, and alerts are not configured.
- LLM usage (token counts and cost) is persisted in the database per user.
