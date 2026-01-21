from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from fastapi.testclient import TestClient

from nexus.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_chunks():
    return [MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")]


@pytest.mark.asyncio
async def test_ollama_chat_with_default_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Ollama response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={"query": "test", "collections": ["test"], "provider": "ollama"},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ollama_chat_with_custom_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Ollama response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test",
                    "collections": ["test"],
                    "provider": "ollama",
                    "temperature": 0.5,
                    "top_p": 0.8,
                    "max_tokens": 1024,
                },
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openai_chat_with_default_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.openai_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "OpenAI response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={"query": "test", "collections": ["test"], "provider": "openai"},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openai_chat_with_custom_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.openai_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "OpenAI response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test",
                    "collections": ["test"],
                    "provider": "openai",
                    "temperature": 0.4,
                    "top_p": 0.85,
                    "max_tokens": 2048,
                },
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_anthropic_chat_with_default_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.anthropic_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Claude response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={"query": "test", "collections": ["test"], "provider": "anthropic"},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_anthropic_chat_with_custom_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.anthropic_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Claude response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test",
                    "collections": ["test"],
                    "provider": "anthropic",
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "max_tokens": 1024,
                },
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_google_chat_with_default_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.google_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Gemini response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={"query": "test", "collections": ["test"], "provider": "google"},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_google_chat_with_custom_parameters(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.google_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Gemini response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test",
                    "collections": ["test"],
                    "provider": "google",
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "max_tokens": 1024,
                },
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unsupported_provider_returns_400(client, mock_chunks):
    response = client.post(
        "/chat/stream",
        json={"query": "test", "collections": ["test"], "provider": "unsupported"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_with_custom_model_parameter(client, mock_chunks):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, path="test.pdf", page=1, score=0.95, content="test")
        ]

        with patch("nexus.generate.ollama_chat.stream_chat") as mock_chat:

            async def mock_gen():
                yield "Ollama response"

            mock_chat.return_value = mock_gen()

            response = client.post(
                "/chat/stream",
                json={
                    "query": "test",
                    "collections": ["test"],
                    "provider": "ollama",
                    "model": "phi3:mini",
                },
            )

    assert response.status_code == 200
