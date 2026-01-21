import pytest
from httpx import AsyncClient

from nexus.api import main


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
