from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from fastapi.testclient import TestClient

from nexus.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_ollama_response():
    return {
        "models": [
            {
                "name": "llama3.1:8b-instruct",
                "size": 4900000000,
                "modified_at": "2024-01-15T00:00:00Z",
            },
            {"name": "phi3:mini", "size": 2200000000, "modified_at": "2024-01-15T00:00:00Z"},
            {
                "name": "qwen2.5:7b-instruct",
                "size": 4700000000,
                "modified_at": "2024-01-15T00:00:00Z",
            },
        ]
    }


def test_list_ollama_models_success(client, mock_ollama_response):
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        response = client.get("/models/ollama")

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 3
    assert data["models"][0]["name"] == "llama3.1:8b-instruct"
    assert data["models"][1]["name"] == "phi3:mini"


def test_list_ollama_models_sorts_alphabetically(client, mock_ollama_response):
    unsorted_models = [
        {"name": "qwen2.5:7b-instruct"},
        {"name": "llama3.1:8b-instruct"},
        {"name": "phi3:mini"},
    ]
    mock_ollama_response["models"] = unsorted_models

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        response = client.get("/models/ollama")

    assert response.status_code == 200
    data = response.json()
    model_names = [m["name"] for m in data["models"]]
    assert model_names == ["llama3.1:8b-instruct", "phi3:mini", "qwen2.5:7b-instruct"]


def test_list_ollama_models_empty(client):
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        response = client.get("/models/ollama")

    assert response.status_code == 200
    data = response.json()
    assert data["models"] == []


def test_list_ollama_models_ollama_error(client):
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Ollama not available")
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        response = client.get("/models/ollama")

    assert response.status_code != 200
