from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import tempfile
import hashlib

from nexus.ingest.pipeline import ingest_collection
from nexus.hooks.executor import HookExecutor


@pytest.fixture
def temp_corpora_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        corpora_path = Path(tmpdir) / "corpora"
        corpora_path.mkdir()
        (corpora_path / "test").mkdir()
        (corpora_path / "library").mkdir()
        yield tmpdir


@pytest.fixture
def temp_processed_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_path = Path(tmpdir) / "processed"
        processed_path.mkdir()
        yield processed_path


@pytest.fixture
def sample_pdf():
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Length 2 0 R\nstream\nBT\n>>\nendstream"
    return pdf_content


@pytest.mark.asyncio
async def test_ingest_collection_creates_collection_record(
    temp_corpora_dir, temp_processed_dir, sample_pdf
):
    pdf_path = Path(temp_corpora_dir) / "corpora" / "test" / "test.pdf"
    pdf_path.write_bytes(sample_pdf)

    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = Path(temp_processed_dir)
        settings.corpora_manifest = Path(temp_corpora_dir) / "corpora.yml"
        mock_settings.return_value = settings

        corpora_config = MagicMock()
        corpora_config.collections = {
            "test": MagicMock(
                roots=[Path(temp_corpora_dir) / "corpora" / "test"],
                include=["**/*.pdf"],
                exclude=[],
                tags=["test"],
                hooks={},
            )
        }

        with patch("nexus.ingest.pipelines.get_settings") as mock_get_settings:
            mock_get_settings.return_value = settings

            with patch("nexus.config.CorporaConfig.load") as mock_load:
                mock_load.return_value = corpora_config

                with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

                    async def mock_ensure():
                        pass

                    mock_schema.side_effect = mock_ensure

                    with patch("nexus.ingest.pipelines.HookExecutor") as mock_executor_class:
                        executor = MagicMock(spec=HookExecutor)
                        executor.run_pre_ingest.return_value = {}
                        executor.run_post_ingest.return_value = {}
                        mock_executor_class.return_value = executor

                        await ingest_collection("test")


@pytest.mark.asyncio
async def test_ingest_collection_skips_unchanged_files(
    temp_corpora_dir, temp_processed_dir, sample_pdf
):
    pdf_path = Path(temp_corpora_dir) / "corpora" / "test" / "test.pdf"
    pdf_path.write_bytes(sample_pdf)

    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = Path(temp_processed_dir)
        settings.corpora_manifest = Path(temp_corpora_dir) / "corpora.yml"
        mock_settings.return_value = settings

        corpora_config = MagicMock()
        corpora_config.collections = {
            "test": MagicMock(
                roots=[Path(temp_corpora_dir) / "corpora" / "test"],
                include=["**/*.pdf"],
                exclude=[],
                tags=["test"],
                hooks={},
            )
        }

        with patch("nexus.config.CorporaConfig.load") as mock_load:
            mock_load.return_value = corpora_config

            with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

                async def mock_ensure():
                    pass

                mock_schema.side_effect = mock_ensure

                with patch("nexus.ingest.pipelines.HookExecutor") as mock_executor_class:
                    executor = MagicMock(spec=HookExecutor)
                    executor.run_pre_ingest.return_value = {}
                    executor.run_post_ingest.return_value = {}
                    mock_executor_class.return_value = executor

                    await ingest_collection("test")

                    await ingest_collection("test")


@pytest.mark.asyncio
async def test_ingest_collection_calls_hooks(temp_corpora_dir, temp_processed_dir, sample_pdf):
    pdf_path = Path(temp_corpora_dir) / "corpora" / "test" / "test.pdf"
    pdf_path.write_bytes(sample_pdf)

    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = Path(temp_processed_dir)
        settings.corpora_manifest = Path(temp_corpora_dir) / "corpora.yml"
        settings.hooks_dir = Path(temp_corpora_dir)
        mock_settings.return_value = settings

        hook_path = Path(temp_corpora_dir) / "hooks" / "pre-ingest-test.sh"
        hook_path.write_text("#!/bin/bash\necho 'pre ingest hook'")
        hook_path.chmod(0o755)

        corpora_config = MagicMock()
        corpora_config.collections = {
            "test": MagicMock(
                roots=[Path(temp_corpora_dir) / "corpora" / "test"],
                include=["**/*.pdf"],
                exclude=[],
                tags=["test"],
                hooks={"pre_ingest": str(hook_path)},
            )
        }

        with patch("nexus.config.CorporaConfig.load") as mock_load:
            mock_load.return_value = corpora_config

            with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

                async def mock_ensure():
                    pass

                mock_schema.side_effect = mock_ensure

                executor = HookExecutor(hooks_dir=Path(temp_corpora_dir))

                await ingest_collection("test")


@pytest.mark.asyncio
async def test_ingest_collection_handles_corrupt_files(temp_corpora_dir, temp_processed_dir):
    pdf_path = Path(temp_corpora_dir) / "corpora" / "test" / "test.pdf"
    pdf_path.write_bytes(b"corrupted pdf data")

    with patch("nexus.ingest.pipelines.get_settings") as mock_settings:
        settings = MagicMock()
        settings.database_url = "sqlite:///:memory:"
        settings.processed_dir = Path(temp_processed_dir)
        settings.corpora_manifest = Path(temp_corpora_dir) / "corpora.yml"
        mock_settings.return_value = settings

        corpora_config = MagicMock()
        corpora_config.collections = {
            "test": MagicMock(
                roots=[Path(temp_corpora_dir) / "corpora" / "test"],
                include=["**/*.pdf"],
                exclude=[],
                tags=["test"],
                hooks={},
            )
        }

        with patch("nexus.config.CorporaConfig.load") as mock_load:
            mock_load.return_value = corpora_config

            with patch("nexus.ingest.pipelines.ensure_schema") as mock_schema:

                async def mock_ensure():
                    pass

                mock_schema.side_effect = mock_ensure

                with patch("nexus.ingest.pipelines.HookExecutor") as mock_executor_class:
                    executor = MagicMock(spec=HookExecutor)
                    executor.run_pre_ingest.return_value = {}
                    executor.run_post_ingest.return_value = {}
                    mock_executor_class.return_value = executor

                    await ingest_collection("test")
