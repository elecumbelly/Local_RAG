from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

from anthropic import AsyncAnthropic

from nexus.config import get_settings
from nexus.generate import prompts


class AnthropicChatProvider:
    def __init__(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-haiku-20240307"  # You can make this configurable

    async def chat(
        self,
        query: str,
        chunks: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        model = model or self.model
        prompt = prompts.build_prompt(query, chunks)
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = 4096
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        message = await self.client.messages.create(**kwargs)
        return message.content[0].text

    async def stream_chat(
        self,
        query: str,
        chunks: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        model = model or self.model
        prompt = prompts.build_prompt(query, chunks)
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = 4096
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        stream = await self.client.messages.create(**kwargs)

        async for chunk in stream:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text


async def chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> str:
    provider = AnthropicChatProvider()
    return await provider.chat(
        query, chunks, model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens
    )


async def stream_chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    provider = AnthropicChatProvider()
    async for token in provider.stream_chat(
        query, chunks, model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens
    ):
        yield token
