"""OpenRouter chat completions with RAG context injection."""

from openai import AsyncOpenAI, OpenAI

_RAG_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant.\n"
    "Answer the user's question using ONLY the knowledge-base excerpts provided below.\n"
    "Be clear and concise. If the excerpts do not fully answer the question, say so honestly "
    "but do not invent information.\n\n"
    "Knowledge-base excerpts:\n"
    "{context}"
)


def create_openrouter_async_client(*, api_key: str, base_url: str) -> AsyncOpenAI:
    """Create an AsyncOpenAI client that targets OpenRouter's API."""
    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def create_openrouter_sync_client(*, api_key: str, base_url: str) -> OpenAI:
    """Create a synchronous OpenAI client that targets OpenRouter's API."""
    return OpenAI(base_url=base_url, api_key=api_key)


async def generate_rag_reply(
    *,
    client: AsyncOpenAI,
    model: str,
    user_message: str,
    context: str,
) -> str:
    """Generate a support reply grounded in the provided RAG context.

    ``context`` is the concatenated chunk text returned by the retrieval step.
    The LLM is instructed to answer only from that context.
    """
    system_content = _RAG_SYSTEM_PROMPT.format(context=context)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    choice = response.choices[0].message.content
    if choice is None:
        return ""
    return choice.strip()