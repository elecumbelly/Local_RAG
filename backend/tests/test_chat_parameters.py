from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
import httpx

from fastapi.testclient import TestClient

from nexus.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_chunks():
    return [
        {
            "document_id": 1,
            "path": "/corpora/test/doc.pdf",
            "page": 1,
            "score": 0.95,
            "content": "Test content from document",
        }
    ]


@pytest.mark.asyncio
async def test_chat_with_temperature_parameter(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                    "temperature": 0.5,
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_with_top_p_parameter(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                    "top_p": 0.8,
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_with_max_tokens_parameter(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                    "max_tokens": 2048,
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_with_all_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                    "temperature": 0.3,
                    "top_p": 0.7,
                    "max_tokens": 1024,
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_with_openai_provider_passes_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.openai_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                    "provider": "openai",
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "max_tokens": 2048,
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_default_parameters_omitted(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test query",
                    "collections": ["test"],
                },
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_invalid_temperature(client):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        response = client.post(
            "/chat/stream",
            json={
                "query": "test",
                "collections": ["test"],
                "temperature": 3.0,
            },
        )

        assert response.status_code == 422
