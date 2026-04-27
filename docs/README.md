# Project docs

This folder contains product and architecture documentation for Customer Support SaaS.

## Contents

- [Build journey](build-journey/README.md)
- [System architecture](system-architecture.md)
- [Mermaid source diagram](architecture-overview.mmd)

## Architecture overview

```mermaid
flowchart LR
  subgraph Frontend
    Web[Next.js app]
  end

  subgraph Backend
    API[FastAPI API]
    Tasks[Background tasks<br/>(embeddings)]
  end

  subgraph Data
    DB[(Aiven Postgres<br/>pgvector)]
    Storage[Supabase Storage<br/>or local disk]
  end

  subgraph AI
    OpenRouter[OpenRouter API<br/>GPT-4.1 Mini]
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

Notes:

- The diagram source lives in [architecture-overview.mmd](architecture-overview.mmd).
- The backend runs embeddings in FastAPI background tasks after uploads complete.
