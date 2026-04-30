# Architecture explained (prose only)

This document describes how Customer Support SaaS is structured and how data moves through it. It intentionally contains no diagrams. For visual architecture views, see the Mermaid sources in the same folder: `component-overview.mmd`, `document-ingestion-flow.mmd`, `rag-chat-flow.mmd`, `security-and-tenancy.mmd`, and `planned-omnichannel.mmd`.

## Product intent

The system is a multi-tenant AI support platform. Each customer organization (called a company in the codebase) has its own documents, embeddings, and chat context. Retrieval and answers must use only that tenant’s knowledge. Cross-tenant access is excluded by design at the API and database layers.

## Major components

The browser runs a Next.js application that handles sign-in, navigation, document management, chat, and dashboard views. Authentication is delegated to Clerk. The frontend does not talk to the database directly. For operations that need secrets or privileged access, Next.js server routes act as a backend-for-frontend layer and attach the user’s Clerk bearer token when calling the FastAPI service.

The FastAPI service exposes versioned REST endpoints for companies and documents, agent chat, and read-only monitoring data. It validates every protected request with Clerk’s session verification, then performs work against PostgreSQL and optional object storage. For generative features it calls OpenRouter for both embedding and chat completions, using models configured in application settings.

PostgreSQL holds users, companies, documents, chunk metadata, vector embeddings in pgvector-enabled tables, guardrail audit events, and usage accounting. Files for uploaded PDFs live in Supabase Storage when configured, or on local disk under a configured upload root otherwise.

## Document ingestion path

When an operator uploads a PDF for a selected company, the flow is transactional at the metadata and storage boundary first, then asynchronous for heavy work. Two ingestion shapes exist. If Supabase object storage is configured, the API can mint signed upload URLs so the browser uploads bytes directly to the bucket, then calls a confirm endpoint that verifies each object with a storage HEAD request before inserting document rows in one transaction. If Supabase is not configured, the same router accepts a legacy multipart POST where the FastAPI process receives the file body, writes to the local upload root, inserts metadata, and commits. In both cases, after a successful commit, a background task is scheduled so the HTTP response is not blocked by extraction and embedding.

The embedding pipeline opens its own database session, finds documents for that company that are not yet embedded, reads each file back from storage, extracts plain text, splits it into chunks, requests embeddings from the provider, and writes rows into the chunk table including the company identifier on every row. When embedding completes for a document, the document’s embedded flag is updated. The pipeline is written to skip work when the database is not PostgreSQL, which supports lightweight test environments without pgvector.

## RAG chat path

Chat requests specify which company the question belongs to. The backend resolves the signed-in Clerk identity to a local user record, verifies that the requested company is owned by that user, and runs input guardrails such as token limits before any model work begins.

Retrieval is deterministic in the first phase: the user message is embedded, and a SQL query returns the most similar chunks ordered by cosine distance, filtered strictly by company identifier. A similarity threshold decides whether the question is in scope relative to the knowledge base. If nothing passes the threshold, the service can return a refusal that names the company without invoking the full answer model.

When context is available, a second phase runs an agent configured with instructions that treat the retrieved excerpts as the only source of truth. An optional tool allows the model to request additional retrieval if the first excerpts are insufficient. The run is wrapped in a trace for observability hooks. The HTTP response includes whether the answer was grounded in retrieved material, and usage metadata is collected for cost monitoring.

## Security and tenancy

Trust starts at the edge with Clerk-issued tokens. The FastAPI dependency layer rejects unauthenticated traffic. Business logic maps the external user identifier to an internal user primary key and enforces ownership on company-scoped routes so one tenant cannot pass another tenant’s identifier and read data.

At persistence time, chunk search always includes an explicit company identifier predicate, so even if higher-level code regressed, the narrowest data access path still scopes vectors to one tenant. Background embedding jobs are invoked with a single company identifier per scheduling decision, which keeps batch processing aligned with tenant boundaries.

## Operations and monitoring

A simple health endpoint exists on the backend for load balancers and uptime checks. Guardrail events can be listed through an authenticated monitoring route for dashboard review. Centralized metrics and alerting are not described as fully implemented in the repository; logging is used in service modules.

## Planned omnichannel layer

The product direction includes automatic handling of inbound email and WhatsApp messages using the same retrieval and answer pipeline. In the current repository state, that channel layer is conceptual: webhooks and provider integrations are the natural next step once routing, idempotency, and outbound sending are defined per channel. The prose here matches that roadmap without duplicating diagram content from `planned-omnichannel.mmd`.

## How this folder relates to other docs

The root of `backend/docs` still hosts `system-architecture.md`, which includes an inline diagram for quick reading in Markdown viewers. The `architecture/` subfolder holds standalone Mermaid sources that are easier to diff, reuse in presentations, or import into diagram tools. This file is the companion narrative for those sources.
