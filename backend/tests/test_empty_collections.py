"""Regression tests for empty collections handling.

These tests ensure that empty collections lists are properly handled
to prevent SQL injection and invalid query errors.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nexus.api.main import app
from nexus.config import Settings, get_settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Set up test API key for all tests in this module."""
    monkeypatch.setenv("NEXUS_API_KEY", "test-key")
    monkeypatch.setenv("NEXUS_ALLOW_ORIGINS", '["http://localhost:3000"]')

    def _get_settings():
        return Settings()

    app.dependency_overrides[get_settings] = _get_settings
    yield
    app.dependency_overrides.clear()


class TestEmptyCollectionsHandling:
    """Test that empty collections lists are handled gracefully."""

    def test_chat_request_rejects_empty_collections(self, client):
        """Regression: Empty collections list should return 422, not 500 or SQL error."""
        response = client.post(
            "/chat",
            json={"query": "test", "collections": []},
            headers={"x-api-key": "test-key"},
        )
        # Should get validation error (422), not SQL error or 500
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_chat_stream_rejects_empty_collections(self, client):
        """Regression: Empty collections in streaming chat should return 422."""
        response = client.post(
            "/chat/stream",
            json={"query": "test", "collections": []},
            headers={"x-api-key": "test-key"},
        )
        assert response.status_code == 422

    def test_search_chunks_returns_empty_for_empty_collections(self):
        """Unit test: search_chunks should return empty list for empty collections."""
        from nexus.retrieve.pgvector import search_chunks

        # This should not raise an exception
        result = search_chunks(
            query_embedding=[0.1] * 1024,
            collections=[],
            tags=None,
            top_k=8,
        )
        assert result == []

    def test_chat_request_with_valid_collections_succeeds_validation(self, client):
        """Ensure normal collections list still passes validation."""
        response = client.post(
            "/chat",
            json={"query": "test", "collections": ["library"]},
            headers={"x-api-key": "test-key"},
        )
        # Should fail for other reasons (DB not initialized), but not validation
        assert response.status_code != 422
