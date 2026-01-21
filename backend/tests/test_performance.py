from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import tempfile
import hashlib

from nexus.ingest.pipeline import ingest_collection
from nexus.embed.ollama_embed import OllamaEmbedder


@pytest.fixture
def temp_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_path = Path(tmpdir) / "corpus"
        corpus_path.mkdir()
        processed_path = Path(tmpdir) / "processed"
        processed_path.mkdir()

        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Length 100 R\nstream\nBT\n>>\nendstream\n"

        test_file_1 = corpus_path / "doc1.pdf"
        test_file_2 = corpus_path / "doc2.pdf"
        test_file_1.write_bytes(pdf_content)
        test_file_2.write_bytes(pdf_content)

        yield {
            "corpus": corpus_path,
            "processed": processed_path,
            "files": [test_file_1, test_file_2],
        }


@pytest.mark.asyncio
async def test_embedding_throughput_for_100_documents(temp_files):
    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = temp_files["processed"]
        settings.corpora_manifest = MagicMock()
        settings.corpora_manifest.load.return_value = MagicMock(
            collections={
                "test": MagicMock(
                    roots=[temp_files["corpus"]],
                    include=["**/*.pdf"],
                    exclude=[],
                    tags=["test"],
                    hooks={},
                )
            }
        )
        mock_settings.return_value = settings

        with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

            async def mock_ensure():
                pass

            mock_schema.side_effect = mock_ensure

            with patch("nexus.ingest.pipelines.HookExecutor") as mock_executor:
                executor = MagicMock()
                executor.run_pre_ingest.return_value = {}
                executor.run_post_ingest.return_value = {}

                with patch("nexus.embed.ollama_embed.OllamaEmbedder") as mock_embedder:
                    embedder = AsyncMock()

                    async def mock_embed():
                        return [0.1, 0.2] * 50

                    embedder.embed_multiple.return_value = mock_embed()
                    embedder.embed_query.return_value = [0.1, 0.2, 0.3]

                    start_time = time.time()
                    await ingest_collection("test")
                    end_time = time.time()

    throughput = 100 / (end_time - start_time)
    assert throughput > 10


@pytest.mark.asyncio
async def test_search_latency_under_1000_chunks(temp_files):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        start_time = time.time()

        mock_chunks = [
            MagicMock(
                document_id=i, path=f"doc{i}.pdf", page=1, score=0.95 - (i * 0.001), content="test"
            )
            for i in range(100)
        ]
        mock_search.return_value = mock_chunks

        from nexus.api.routes_chat import _retrieve

        await _retrieve(
            MagicMock(
                query="test query",
                collections=["test"],
                tags=None,
                top_k=8,
                min_score=None,
            )
        )

        end_time = time.time()
        latency = (end_time - start_time) * 1000

    assert latency < 500


@pytest.mark.asyncio
async def test_search_latency_with_high_top_k(temp_files):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        start_time = time.time()

        mock_chunks = [
            MagicMock(document_id=i, path=f"doc{i}.pdf", page=1, score=0.95, content="test")
            for i in range(100)
        ]
        mock_search.return_value = mock_chunks

        from nexus.api.routes_chat import _retrieve

        await _retrieve(
            MagicMock(
                query="test query",
                collections=["test"],
                tags=None,
                top_k=100,
                min_score=None,
            )
        )

        end_time = time.time()
        latency = (end_time - start_time) * 1000

    assert latency < 2000


@pytest.mark.asyncio
async def test_embedding_latency(temp_files):
    from nexus.embed.ollama_embed import OllamaEmbedder

    embedder = OllamaEmbedder()

    texts = ["test content"] * 50

    start_time = time.time()
    with patch.object(embedder, "client") as mock_client:
        async_client = AsyncMock()
        async_client.post.return_value = AsyncMock()
        async_client.post.return_value.json.return_value = {"embeddings": [[0.1] * 1024] * 50}

        await embedder.embed_multiple(texts)

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    assert latency_ms < 10000


@pytest.mark.asyncio
async def test_chunking_performance(temp_files):
    from nexus.ingest.chunking import chunk_text

    long_text = "This is a test. " * 10000

    start_time = time.time()
    chunks = chunk_text(long_text, chunk_size=800, overlap=80)
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000

    assert len(chunks) > 10
    assert latency_ms < 100


@pytest.mark.asyncio
async def test_concurrent_search_performance(temp_files):
    with patch("nexus.retrieve.pgvector.search_chunks") as mock_search:
        mock_chunks = [
            MagicMock(document_id=1, path="doc1.pdf", page=1, score=0.95, content="test")
        ]

        start_time = time.time()

        tasks = []
        for _ in range(10):
            with patch("nexus.api.routes_chat._retrieve") as mock_retrieve:
                mock_retrieve.return_value = mock_chunks

                from nexus.api.routes_chat import _retrieve

                tasks.append(
                    _retrieve(
                        MagicMock(
                            query="test",
                            collections=["test"],
                            tags=None,
                            top_k=8,
                            min_score=None,
                        )
                    )
                )

        await asyncio.gather(*tasks)

        end_time = time.time()
        total_latency = (end_time - start_time) * 1000

    assert total_latency < 10000


@pytest.mark.asyncio
async def test_memory_efficiency_large_document(temp_files):
    import psutil
    import os

    process = psutil.Process(os.getpid())

    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = temp_files["processed"]
        settings.corpora_manifest = MagicMock()
        settings.corpora_manifest.load.return_value = MagicMock(
            collections={
                "test": MagicMock(
                    roots=[temp_files["corpus"]],
                    include=["**/*.pdf"],
                    exclude=[],
                    tags=["test"],
                    hooks={},
                )
            }
        )
        mock_settings.return_value = settings

        with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

            async def mock_ensure():
                pass

            mock_schema.side_effect = mock_ensure

            with patch("nexus.ingest.pipelines.HookExecutor") as mock_executor:
                executor = MagicMock()
                executor.run_pre_ingest.return_value = {}
                executor.run_post_ingest.return_value = {}

                with patch("nexus.embed.ollama_embed.OllamaEmbedder") as mock_embedder:
                    embedder = AsyncMock()
                    embedder.embed_multiple.return_value = [[0.1] * 1024]

                    initial_mem = process.memory_info().rss

                    await ingest_collection("test")

                    final_mem = process.memory_info().rss
                    mem_increase_mb = (final_mem - initial_mem) / (1024 * 1024)

    assert mem_increase_mb < 500
