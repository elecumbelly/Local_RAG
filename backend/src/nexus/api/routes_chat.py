from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi.util import get_remote_address

from nexus.api import deps
from nexus.config import get_settings
from nexus.embed.ollama_embed import OllamaEmbedder
from nexus.generate import ollama_chat, validate
from nexus.generate import openai_chat, anthropic_chat, google_chat
from nexus.retrieve import pgvector

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(deps.require_api_key)],
)


class ChatRequest(BaseModel):
    query: str
    collections: List[str] = ["library", "dev", "test"]
    tags: Optional[List[str]] = None
    top_k: int = 8
    min_score: Optional[float] = None
    provider: str = "ollama"
    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

    @model_validator(mode="after")
    def validate_non_empty_collections(self) -> "ChatRequest":
        if not self.collections:
            raise ValueError("collections must not be empty")
        return self

    @property
    def effective_max_tokens(self) -> int:
        settings = get_settings()
        if self.max_tokens is None:
            return settings.max_response_tokens
        return min(self.max_tokens, settings.max_response_tokens)


async def _retrieve(req: ChatRequest):
    embedder = OllamaEmbedder()
    q_embed = await embedder.embed_query(req.query)
    chunks = await pgvector.search_chunks(
        query_embedding=q_embed,
        collections=req.collections,
        tags=req.tags,
        top_k=req.top_k,
        min_score=req.min_score,
    )
    return chunks


async def _get_chat_provider(provider_name: str):
    """Get the appropriate chat provider based on the provider name."""
    providers = {
        "ollama": ollama_chat,
        "openai": openai_chat,
        "anthropic": anthropic_chat,
        "google": google_chat,
    }

    if provider_name not in providers:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_name}")

    return providers[provider_name]


@router.post("")
async def chat(request: Request, req: ChatRequest):
    await request.state.limiter.check_async(
        get_remote_address(request),
        "chat",
        cost=1,
    )
    chunks = await _retrieve(req)
    chunk_payload = [
        {
            "document_id": c.document_id,
            "path": c.path,
            "page": c.page,
            "score": c.score,
            "content": c.content,
        }
        for c in chunks
    ]

    provider = await _get_chat_provider(req.provider)
    answer = await provider.chat(
        req.query,
        chunk_payload,
        model=req.model,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.effective_max_tokens,
    )
    answer = validate.ensure_citations(answer, has_evidence=bool(chunks))
    return {"answer": answer, "chunks": chunk_payload}


@router.post("/stream")
async def chat_stream(request: Request, req: ChatRequest):
    await request.state.limiter.check_async(
        get_remote_address(request),
        "chat",
        cost=1,
    )
    chunks = await _retrieve(req)
    chunk_payload = [
        {
            "document_id": c.document_id,
            "path": c.path,
            "page": c.page,
            "score": c.score,
            "content": c.content,
        }
        for c in chunks
    ]

    provider = await _get_chat_provider(req.provider)

    async def event_generator():
        yield f"data: {json.dumps({'chunks': chunk_payload})}\n\n"
        try:
            async for token in provider.stream_chat(
                req.query,
                chunk_payload,
                model=req.model,
                temperature=req.temperature,
                top_p=req.top_p,
                max_tokens=req.effective_max_tokens,
            ):
                yield f"data: {token}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: ERROR {exc}\n\n"
        yield "data: [DONE]\n\n"

    headers = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
