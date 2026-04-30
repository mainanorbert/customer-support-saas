# Customer Support SaaS Strategic Pitch

## 1. Technology Stack

The project is built as a modern AI customer-support platform with a clear separation between user experience, API orchestration, storage, retrieval, and model execution.

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS, shadcn-style UI components, Clerk.
- **Backend:** FastAPI, Python 3.12, SQLAlchemy, Alembic, Pydantic settings.
- **AI layer:** OpenAI SDK-compatible clients through OpenRouter, OpenAI Agents SDK, tracing around the RAG answer flow, GPT-4.1 Mini for chat, Text Embedding 3 Small for embeddings.
- **Database:** Aiven PostgreSQL with pgvector for tenant data, document metadata, vector embeddings, guardrail events, and usage tracking.
- **File storage:** Supabase Storage for uploaded document files, with local filesystem fallback for development.
- **Authentication:** Clerk for signup, sign-in, session management, and backend JWT verification.
- **Deployment:** Containerized FastAPI backend with Docker, suitable for Render deployment. Render was selected because it can build from GitHub, run the container, expose health checks, and automate deployment from repository changes.
- **Observability and safety:** Usage tracking, cost tracking, guardrail event logging, input token limits, and response PII checks.

## 2. The Problem This Project Solves

Support teams repeatedly answer the same questions across channels, while company-specific policies, documents, and customer instructions often live in scattered PDF files or internal references. This creates slow response times, inconsistent answers, and a high risk of agents giving information that does not match the company's actual policies.

This project solves that problem by giving each company a private AI support assistant grounded in its own documents. A user can create a company workspace, upload knowledge-base PDFs, automatically embed them, and ask questions that are answered using only that company's stored context.

The strategic value is not just faster chat. The core value is a reusable support intelligence layer that can later power WhatsApp, email, and other customer channels while keeping every tenant isolated.

## 3. Current MVP: What Has Been Built

The current MVP delivers the foundation of an AI support SaaS platform.

Authenticated users can:

- Sign in through Clerk.
- Register their identity in the backend.
- Create company workspaces.
- Upload PDF documents under each company.
- Store document files in Supabase Storage or local storage.
- View uploaded documents per company with status and embedding state.
- Trigger background embeddings for uploaded documents.
- Chat with a tenant-scoped support assistant.
- Receive answers grounded in the selected company's embedded documents.
- View usage and cost tracking.
- View guardrail events for blocked or monitored interactions.

The MVP proves the central product hypothesis: company documents can become a private, searchable support knowledge base, and an AI assistant can answer questions from that knowledge base without mixing data between tenants.

## 4. Full Product Direction: WhatsApp and Email Webhooks

The full version extends the MVP from an internal chat interface into an omnichannel support automation system.

In the full product, incoming customer messages from WhatsApp and email would arrive through webhooks. The backend would identify the company/channel, retrieve the right tenant knowledge base, generate a grounded draft or response, apply guardrails, log usage, and send the reply through the same channel.

The intended full flow is:

1. A customer sends a WhatsApp message or email.
2. The channel provider calls a backend webhook.
3. The backend maps the sender/channel to the correct company tenant.
4. The message is checked for limits and safety rules.
5. The RAG engine retrieves relevant chunks from that company's documents only.
6. The AI agent generates a response from the retrieved context.
7. The response is checked for monitored PII such as email addresses and phone numbers.
8. Usage, cost, and guardrail events are stored.
9. The reply is delivered through WhatsApp or email, or queued for human review depending on policy.

The repository already reflects this direction in the product rules and placeholder router files, but the current implemented MVP does not yet mount active WhatsApp or email webhook endpoints. That is the next product layer built on top of the current RAG, tenant isolation, storage, and monitoring foundation.

## 5. Key Design Decisions and Why They Matter

### Next.js for the Frontend

Next.js was chosen because it supports a fast, modern SaaS user experience with protected pages, server-side route handlers, and strong TypeScript ergonomics.

The frontend uses API route handlers as a secure proxy between the browser and FastAPI. This keeps browser calls same-origin, forwards Clerk session tokens server-side, and avoids exposing backend details directly in the UI.

### FastAPI for the Backend

FastAPI was chosen for its speed, strong typing, Pydantic validation, OpenAPI support, and clean dependency injection.

It fits this project well because the backend has multiple responsibilities: authentication verification, file ingestion, background jobs, retrieval, AI orchestration, cost tracking, and monitoring endpoints.

### Clerk for Authentication

Clerk was adopted to avoid rebuilding authentication from scratch. It handles user signup, sessions, and frontend identity state. The backend verifies Clerk JWTs before allowing access to company data.

This is important because the product is multi-tenant. Every company, document, vector search, and chat request must be tied to a verified user identity.

### Aiven PostgreSQL With pgvector

Aiven PostgreSQL was selected as an external managed database because the project needs durable data outside the application container.

PostgreSQL stores:

- Users mirrored from Clerk.
- Company tenants.
- Document metadata.
- Extracted document text.
- Vector chunks through pgvector.
- Guardrail audit events.
- Usage and cost totals.

pgvector keeps semantic search close to relational tenant data. This simplifies isolation because retrieval can filter by `company_id` before returning matching chunks.

### Supabase Storage for Files

Supabase Storage is used for uploaded document binaries so the backend container does not need to permanently hold user files. This matters in hosted environments where container disks can be ephemeral.

The direct-upload design also lets the browser upload files to Supabase using signed URLs. That prevents the backend from becoming a bottleneck for large PDF transfer and is especially useful on free or low-resource deployment tiers.

### Docker and Render Deployment

The backend is containerized with Docker. This makes the API portable across local development, Docker Compose, and hosted services.

Render is a practical deployment option because it can connect to GitHub, build the container, run the service, and redeploy automatically when changes are pushed. For an MVP, this reduces deployment overhead and lets the project focus on product validation instead of infrastructure management.

## 6. RAG Techniques Used and Why

The project uses Retrieval-Augmented Generation so answers are grounded in company documents instead of relying only on the model's general knowledge.

The RAG pipeline includes:

- **PDF text extraction:** Uploaded PDFs are converted into plain text.
- **Chunking with overlap:** Long documents are split into smaller overlapping text windows. This improves retrieval quality because related context is less likely to be split too aggressively.
- **Embeddings:** Each chunk is embedded with Text Embedding 3 Small.
- **Vector storage:** Embeddings are stored in PostgreSQL using pgvector.
- **Tenant-scoped retrieval:** Queries search only chunks belonging to the selected `company_id`.
- **Top-k similarity search:** The system retrieves the most relevant chunks for the user question.
- **Similarity thresholding:** If no chunk is relevant enough, the assistant gives a company-aware refusal instead of guessing.
- **Grounded answer generation:** Retrieved excerpts are injected into the agent instructions as the only source of truth.
- **Follow-up retrieval tool:** The OpenAI Agents SDK agent has a `search_knowledge_base` tool for additional context if needed.
- **Tracing:** The answer-agent run is wrapped in a named trace, which supports later debugging and observability.

This design was chosen to reduce hallucination, enforce tenant isolation, and make answers explainable as knowledge-base responses rather than general AI guesses.

## 7. Monitoring, Guardrails, and PII Checks

The project includes guardrails for two important risks: uncontrolled cost and unsafe output.

Input messages are checked for token length before any embedding or model call. The default input limit is 500 tokens. This keeps requests focused, prevents accidental oversized prompts, and protects the system from avoidable model spend.

Assistant responses are scanned for monitored personal information such as email addresses and phone numbers. When detected, the system records a guardrail event with the prompt, response, matched rules, company, user, and token count.

The goal is not only to block bad behavior. The goal is operational visibility. Support automation needs review trails so operators can understand where the assistant may expose sensitive data or produce risky replies.

## 8. Usage and Cost Tracking

The backend tracks model usage per user in the database.

It records:

- Total requests.
- Prompt tokens.
- Completion tokens.
- Total tokens.
- Estimated or fetched model cost.
- User email when available.

Embedding usage and chat generation usage are both accumulated. This matters because an AI SaaS product must understand cost per user and cost per workflow before it can price, scale, or protect margins.

The frontend dashboard displays cumulative usage and spend so the project has an early operational view of AI cost behavior.

## 9. Background Embeddings

Document embedding runs as a FastAPI background task after upload, and it can also be manually triggered for pending documents.

This was an important design choice because embedding can be slow and should not block the upload response. Users can upload files, receive a fast response, and see document status update as processing completes.

The document status model includes pending, processing, completed, and failed states. This makes ingestion visible and debuggable.

## 10. Displaying Documents Under Each Company

Documents are displayed under each company because the company is the tenant boundary.

This is important for three reasons:

1. **Trust:** Users can see exactly which files power a company's answers.
2. **Isolation:** The UI reinforces that each company has its own knowledge base.
3. **Operations:** Status badges show whether documents are pending, processing, embedded, or failed.

This makes the product easier to operate and easier to explain to customers: the assistant answers from the documents attached to the selected company.

## 11. Why This Project Is Important

This project matters because it turns company knowledge into a support automation layer that can scale across channels.

For businesses, it offers:

- Faster response times.
- More consistent customer answers.
- Lower support workload.
- Safer AI responses grounded in company-approved documents.
- Clear separation between tenants.
- Usage visibility for managing AI cost.

For the product roadmap, the MVP establishes the hard parts first: authentication, tenant boundaries, document ingestion, embeddings, vector retrieval, grounded generation, safety checks, and deployment structure.

Once those foundations exist, WhatsApp and email webhooks become channel integrations rather than a complete rebuild.

## 12. Current Limitations

The MVP is intentionally focused and has known limitations.

- **WhatsApp and email webhooks are not yet implemented:** Placeholder files exist, but active webhook routers are not mounted yet.
- **PDF-only ingestion:** The backend currently validates and extracts PDFs only.
- **Scanned PDFs may not work well:** The system uses text extraction, not OCR.
- **Input token limit:** User prompts are limited by default to 500 tokens.
- **Single-turn chat:** The current chat endpoint answers one message at a time and does not yet persist conversation history.
- **No full external metrics stack:** Health checks, logs, usage tracking, and guardrail events exist, but external metrics, alerting, and dashboards are not fully configured.
- **Limited admin access control:** Monitoring endpoints require authentication, but a deeper role-based admin model would be needed for production.
- **Background tasks are in-process:** FastAPI background tasks are suitable for MVP, but a production-scale system may need a queue such as Celery, RQ, or a managed job runner.
- **Frontend tests are limited:** The repo has backend tests, while frontend validation is currently linting and type checking.

## 13. Strategic Summary

This project is an AI-powered, multi-tenant customer support SaaS. The MVP already proves the core support-agent workflow: authenticated users create companies, upload documents, embed knowledge, and chat with an assistant that answers from company-specific context.

The major design decisions support a serious SaaS direction:

- Clerk secures identity.
- Aiven PostgreSQL and pgvector keep tenant data and embeddings durable and queryable.
- Supabase Storage keeps file uploads outside ephemeral containers.
- FastAPI coordinates ingestion, retrieval, AI calls, and monitoring.
- Next.js provides the product interface and secure backend proxying.
- OpenAI-compatible SDKs and Agents SDK traces support model execution and debugging.
- Usage tracking and guardrails make the platform operationally accountable.
- Docker and Render make deployment repeatable and MVP-friendly.

The full vision is to connect WhatsApp and email webhooks to this same RAG engine, turning the current knowledge-base chat into an automated omnichannel support assistant.
