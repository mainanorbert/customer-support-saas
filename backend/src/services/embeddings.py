"""OpenRouter-compatible synchronous embedding calls."""

from __future__ import annotations

from openai import OpenAI


def embed_texts_sync(
    client: OpenAI,
    texts: list[str],
    *,
    model: str,
    expected_dimensions: int,
    batch_size: int,
) -> list[list[float]]:
    """Return one embedding vector per input string, preserving order.

    Calls the OpenAI-compatible ``/v1/embeddings`` endpoint in batches of at most
    ``batch_size`` strings. Each vector length must match ``expected_dimensions``.
    """
    if not texts:
        return []

    all_vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = client.embeddings.create(model=model, input=batch)
        rows = sorted(response.data, key=lambda row: row.index)
        for row in rows:
            vector = list(row.embedding)
            if len(vector) != expected_dimensions:
                msg = (
                    f"Embedding dimension mismatch: model returned {len(vector)} floats, "
                    f"expected {expected_dimensions}. Check embedding_model / embedding_dimensions."
                )
                raise ValueError(msg)
            all_vectors.append(vector)

    return all_vectors
