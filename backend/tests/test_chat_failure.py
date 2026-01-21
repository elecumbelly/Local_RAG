import pytest
from httpx import AsyncClient

from nexus.api import main


@pytest.mark.asyncio
async def test_chat_returns_error_on_bad_request():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/chat",
            headers={"x-api-key": "test-key"},
            json={"query": "", "collections": [], "top_k": 1},
        )
        assert resp.status_code in (400, 422)
