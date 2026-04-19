"""Minimal OpenRouter chat completions (no RAG, no tools)."""

from openai import AsyncOpenAI

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant. "
    "Reply clearly and briefly unless the user asks for detail."
)


def create_openrouter_async_client(*, api_key: str, base_url: str) -> AsyncOpenAI:
    """Create an AsyncOpenAI client that targets OpenRouter's API."""
    return AsyncOpenAI(base_url=base_url, api_key=api_key)


async def generate_simple_agent_reply(
    *,
    client: AsyncOpenAI,
    model: str,
    user_message: str,
    system_prompt: str | None = None,
) -> str:
    """Run a single chat completion and return assistant text."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,
    )
    choice = response.choices[0].message.content
    if choice is None:
        return ""
    return choice.strip()