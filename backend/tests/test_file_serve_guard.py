import pathlib

import pytest
from httpx import AsyncClient

from nexus.api import main
from nexus.config import Settings, get_settings


@pytest.fixture(autouse=True)
def override_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_API_KEY", "test-key")
    # Point corpora to a temp dir
    corp_path = tmp_path / "corpora"
    corp_path.mkdir(parents=True, exist_ok=True)
    (corp_path / "library").mkdir(parents=True, exist_ok=True)
    def _settings():
        return Settings(corpora_manifest=pathlib.Path("corpora.yml"))
    main.app.dependency_overrides[get_settings] = _settings
    yield
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_file_serve_outside_allowed_roots():
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get("/documents/999/file?processed=true", headers={"x-api-key": "test-key"})
        # Depending on DB state may be 404, but path traversal should not be allowed.
        # Simulate traversal attempt.
        resp = await client.get("/documents/../../etc/passwd/file", headers={"x-api-key": "test-key"})
        assert resp.status_code in (400, 404)
