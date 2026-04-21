"""RAG retrieval: embed a query, search ``document_chunks``, enforce a relevance threshold."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

OUT_OF_SCOPE_REPLY = (
    "I'm sorry, but your question does not appear to be related to the information "
    "available in this company's knowledge base. Please rephrase your question or "
    "contact support directly for further assistance."
)


async def embed_query(
    client: AsyncOpenAI,
    query: str,
    *,
    model: str,
    dimensions: int,
) -> list[float]:
    """Return the embedding vector for a single query string."""
    response = await client.embeddings.create(model=model, input=[query])
    vector = list(response.data[0].embedding)
    if len(vector) != dimensions:
        msg = (
            f"Query embedding dimension mismatch: got {len(vector)}, expected {dimensions}. "
            "Check embedding_model / embedding_dimensions in settings."
        )
        raise ValueError(msg)
    return vector


def retrieve_relevant_chunks(
    session: Session,
    *,
    company_id: str,
    query_vector: list[float],
    top_k: int,
) -> list[dict]:
    """Return the ``top_k`` chunks closest to ``query_vector`` for the given company.

    Each returned dict contains ``content``, ``distance`` (cosine), and ``metadata``.
    Distance is in [0, 2]: 0 = identical, 1 = orthogonal, 2 = opposite.
    """
    vec_literal = "[" + ",".join(str(float(x)) for x in query_vector) + "]"
    sql = text(
        """
        SELECT
            content,
            metadata,
            1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM document_chunks
        WHERE company_id = :company_id
        ORDER BY similarity DESC
        LIMIT :top_k
        """
    )
    rows: list[dict] = []
    result = session.execute(sql, {"qvec": vec_literal, "company_id": company_id, "top_k": top_k})
    for row in result.mappings():
        rows.append(dict(row))
    return rows


def build_context_from_chunks(chunks: list[dict]) -> str:
    """Concatenate retrieved chunk texts into a single context block for the LLM prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata") or {}
        source = meta.get("file_name", "document")
        parts.append(f"[Source {i}: {source}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


async def retrieve_and_check_relevance(
    client: AsyncOpenAI,
    session: Session,
    *,
    company_id: str,
    query: str,
    model: str,
    dimensions: int,
    top_k: int,
    similarity_threshold: float,
) -> tuple[bool, str]:
    """Embed ``query``, retrieve nearest chunks, apply threshold, and return context.

    Returns ``(is_relevant, context_or_refusal)``:
    - If the best chunk similarity >= ``similarity_threshold``: ``(True, context_text)``
    - Otherwise: ``(False, OUT_OF_SCOPE_REPLY)``
    """
    query_vector = await embed_query(client, query, model=model, dimensions=dimensions)
    chunks = retrieve_relevant_chunks(session, company_id=company_id, query_vector=query_vector, top_k=top_k)

    if not chunks:
        logger.info("No chunks found for company_id=%s; returning out-of-scope reply.", company_id)
        return False, OUT_OF_SCOPE_REPLY

    best_similarity = float(chunks[0].get("similarity", 0.0))
    logger.info(
        "RAG: company_id=%s query=%r best_similarity=%.4f threshold=%.4f",
        company_id,
        query[:80],
        best_similarity,
        similarity_threshold,
    )

    if best_similarity < similarity_threshold:
        return False, OUT_OF_SCOPE_REPLY

    context = build_context_from_chunks(chunks)
    return True, context
