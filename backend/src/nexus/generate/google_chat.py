from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

from google import genai
from google.genai import types

from nexus.config import get_settings
from nexus.generate import prompts


class GoogleAIChatProvider:
    def __init__(self):
        settings = get_settings()
        if not settings.google_ai_api_key:
            raise ValueError("Google AI API key not configured")

        self.client = genai.Client(api_key=settings.google_ai_api_key)
        self.model = "gemini-1.5-flash"  # You can make this configurable

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
        config = {}
        if temperature is not None:
            config["temperature"] = temperature
        if top_p is not None:
            config["top_p"] = top_p
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
        else:
            config["max_output_tokens"] = 4096

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config),
        )
        return response.text

    async def stream_chat(
        self,
        query: str,
        chunks: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        prompt = prompts.build_prompt(query, chunks)
        config = {}
        if temperature is not None:
            config["temperature"] = temperature
        if top_p is not None:
            config["top_p"] = top_p
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
        else:
            config["max_output_tokens"] = 4096

        response = await self.client.aio.models.generate_content(
            model=model or self.model,
            contents=prompt,
            config=types.GenerateContentConfig(**config),
        )

        yield response.text


async def chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> str:
    provider = GoogleAIChatProvider()
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
    provider = GoogleAIChatProvider()
    async for token in provider.stream_chat(
        query, chunks, model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens
    ):
        yield token
