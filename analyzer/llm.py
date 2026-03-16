from __future__ import annotations
import logging
import anthropic
import config

logger = logging.getLogger(__name__)
_client = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def call_llm(prompt: str, model: str | None = None, system: str = "", max_tokens: int = 4096) -> str:
    client = get_client()
    model = model or config.LLM_MODEL_DAILY
    messages = [{"role": "user", "content": prompt}]
    kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
    if system:
        kwargs["system"] = system
    response = await client.messages.create(**kwargs)
    return response.content[0].text
