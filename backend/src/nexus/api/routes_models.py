from __future__ import annotations

import httpx

from fastapi import APIRouter, Depends

from nexus.api import deps
from nexus.config import get_settings

router = APIRouter(
    prefix="/models",
    tags=["models"],
    dependencies=[Depends(deps.require_api_key)],
)


@router.get("/ollama")
async def list_ollama_models():
    """List available models from local Ollama instance."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
        data = response.json()

        models = [
            {
                "name": model["name"],
                "size": model.get("size", 0),
                "modified_at": model.get("modified_at"),
            }
            for model in data.get("models", [])
        ]

        models.sort(key=lambda m: m["name"])

        return {"models": models}
