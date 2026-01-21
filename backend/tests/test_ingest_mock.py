import pytest
from httpx import AsyncClient

from nexus.api import main
from nexus.ingest import pipeline


class DummyEmbedder:
    async def embed_documents(self, texts):
        return [[0.1] * 1024 for _ in texts]

    async def embed_query(self, text: str):
        return [0.1] * 1024


@pytest.mark.asyncio
async def test_ingest_unknown_collection():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post("/ingest/unknown", headers={"x-api-key": "test-key"})
        assert resp.status_code in (400, 404)
