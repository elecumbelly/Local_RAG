from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

from openai import AsyncOpenAI

from nexus.config import get_settings
from nexus.generate import prompts


class OpenAIChatProvider:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

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
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

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
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


async def chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> str:
    provider = OpenAIChatProvider()
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
    provider = OpenAIChatProvider()
    async for token in provider.stream_chat(
        query, chunks, model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens
    ):
        yield token
