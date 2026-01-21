from __future__ import annotations

import httpx

from nexus.config import get_settings
from nexus.domain.interfaces import Embedder


class OllamaEmbedder(Embedder):
    def __init__(self, client: httpx.AsyncClient | None = None):
        self.settings = get_settings()
        self.client = client or httpx.AsyncClient(
            base_url=self.settings.ollama_url, timeout=self.settings.timeout_seconds
        )

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents. Ollama /api/embed accepts 'input' as string or list."""
        resp = await self.client.post(
            "/api/embed",
            json={"model": self.settings.embed_model, "input": texts},
        )
        if resp.status_code == 400:
            # Context length exceeded - truncate and retry
            error_data = resp.json()
            if "context length" in error_data.get("error", ""):
                # Truncate to ~400 chars (conservative estimate)
                truncated = [t[:400] for t in texts]
                resp = await self.client.post(
                    "/api/embed",
                    json={"model": self.settings.embed_model, "input": truncated},
                )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"]

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        resp = await self.client.post(
            "/api/embed",
            json={"model": self.settings.embed_model, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        # Single input returns embeddings as list with one item
        embeddings = data["embeddings"]
        return embeddings[0] if isinstance(embeddings, list) else embeddings
