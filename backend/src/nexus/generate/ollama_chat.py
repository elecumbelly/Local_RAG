from __future__ import annotations

import asyncio
from typing import AsyncIterator, List

import httpx

from nexus.config import get_settings
from nexus.generate import prompts


async def chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> str:
    settings = get_settings()
    model = model or settings.chat_model
    prompt = prompts.build_prompt(query, chunks)
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if top_p is not None:
        options["top_p"] = top_p
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    async with httpx.AsyncClient(
        base_url=settings.ollama_url, timeout=settings.timeout_seconds
    ) as client:
        resp = await client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "options": options,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


async def stream_chat(
    query: str,
    chunks: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    settings = get_settings()
    model = model or settings.chat_model
    prompt = prompts.build_prompt(query, chunks)
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if top_p is not None:
        options["top_p"] = top_p
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    async with httpx.AsyncClient(
        base_url=settings.ollama_url, timeout=settings.timeout_seconds
    ) as client:
        async with client.stream(
            "POST",
            "/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "options": options,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    import json

                    payload = json.loads(line)
                    message = payload.get("message", {}).get("content")
                    if message:
                        yield message
                except Exception:
                    yield line
