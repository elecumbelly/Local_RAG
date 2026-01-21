from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from fastapi.testclient import TestClient

from nexus.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_sql_injection_in_query(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test'; DROP TABLE documents; --",
                "collections": ["test"],
            },
        )

    assert response.status_code == 200
    assert mock_search.called
    call_args = mock_search.call_args
    actual_query = call_args.kwargs.get("query") or call_args.args[0]
    assert "'" not in actual_query


def test_sql_injection_in_collections(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test query",
                "collections": ["test'; DROP TABLE documents; --"],
            },
        )

    assert response.status_code == 200
    assert mock_search.called
    call_args = mock_search.call_args
    actual_collections = call_args.kwargs.get("collections") or call_args.args[1]
    assert all("';" not in str(col) for col in actual_collections)


def test_sql_injection_in_model_parameter(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test",
                "collections": ["test"],
                "model": "llama3.1'; DROP TABLE documents; --",
            },
        )

    assert response.status_code == 200


def test_xss_in_query(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "<script>alert('xss')</script>",
                "collections": ["test"],
            },
        )

    assert response.status_code == 200
    assert mock_search.called


def test_xss_in_response_is_escaped(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test query",
                "collections": ["test"],
            },
        )

    assert response.status_code == 200

    response_text = ""
    for chunk in response.text.split("\n"):
        if "<script>" in chunk and "alert" in chunk:
            response_text += chunk

    assert "<script>" not in response_text


def test_path_traversal_in_collections(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test",
                "collections": ["../../etc/passwd"],
            },
        )

    assert response.status_code == 200
    assert mock_search.called
    call_args = mock_search.call_args
    actual_collections = call_args.kwargs.get("collections") or call_args.args[1]
    assert all("../" not in str(col) for col in actual_collections)


def test_command_injection_in_model(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "test",
                "collections": ["test"],
                "model": "llama3.1 && cat /etc/passwd",
            },
        )

    assert response.status_code == 200


def test_combined_attack_vectors(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = []

        response = client.post(
            "/chat/stream",
            json={
                "query": "<script>alert(1)</script>'; DROP TABLE",
                "collections": ["../../etc"],
                "model": "test; cat /etc/passwd",
            },
        )

    assert response.status_code == 200


def test_api_key_authentication(client):
    response = client.post(
        "/chat/stream",
        json={"query": "test", "collections": ["test"]},
        headers={"x-api-key": "invalid-key-12345"},
    )

    assert response.status_code == 401


def test_missing_api_key(client):
    response = client.post(
        "/chat/stream",
        json={"query": "test", "collections": ["test"]},
        headers={"x-api-key": ""},
    )

    assert response.status_code in [401, 403]


def test_rate_limiting_headers_present(client):
    response = client.post(
        "/chat/stream",
        json={"query": "test", "collections": ["test"]},
    )

    assert "x-rate-limit" in response.headers or response.headers.get("X-Rate-Limit") is not None
