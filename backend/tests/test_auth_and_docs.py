import asyncio

import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from nexus.api import main
from nexus.config import Settings, get_settings


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    # Force a test API key
    monkeypatch.setenv("NEXUS_API_KEY", "test-key")
    # Allow localhost origin for CORS
    monkeypatch.setenv("NEXUS_ALLOW_ORIGINS", '["http://localhost:3000"]')
    # Override settings factory
    def _get_settings():
        return Settings()
    main.app.dependency_overrides[get_settings] = _get_settings
    yield
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_requires_api_key():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get("/documents")
        assert resp.status_code == 401
        resp = await client.get("/documents", headers={"x-api-key": "test-key"})
        # Schema not initialized in test; expect 500/404 rather than 401
        assert resp.status_code != 401


@pytest.mark.asyncio
async def test_cors_headers_on_options():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.options(
            "/chat",
            headers={
                "origin": "http://localhost:3000",
                "access-control-request-method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
