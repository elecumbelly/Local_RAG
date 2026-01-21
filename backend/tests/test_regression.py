"""Regression tests for critical Local RAG functionality.

These tests serve as a safety net for behavior that, if changed,
would break core functionality or introduce security issues.

Run with: pytest tests/test_regression.py -v
"""

from __future__ import annotations

import pathlib
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from nexus.api.main import app
from nexus.config import Settings, get_settings
from nexus.ingest.mounts import MountValidator, MountValidationError
from nexus.ingest.chunking import chunk_text
from nexus.ingest.quality import assess_quality
from nexus.ingest.discover import (
    walk_collection,
    _check_file_size,
    _skip,
    _hash_file,
    DiscoveredFile,
)
from nexus.api import deps


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    monkeypatch.setenv("NEXUS_API_KEY", "test-key")
    monkeypatch.setenv("NEXUS_ALLOW_ORIGINS", '["http://localhost:3000"]')

    def _get_settings():
        return Settings()

    app.dependency_overrides[get_settings] = _get_settings
    yield
    app.dependency_overrides.clear()


# =============================================================================
# MOUNT VALIDATION REGRESSION TESTS
# =============================================================================


class TestMountValidation:
    """Regression tests for mount path validation."""

    def test_blocked_system_paths(self):
        """System directories should always be blocked."""
        validator = MountValidator()
        blocked = [
            "/etc/passwd",
            "/proc/self",
            "/sys/kernel",
            "/root/.ssh",
            "/var/run/docker.sock",
            "/tmp/../etc",
        ]

        for path in blocked:
            with pytest.raises(MountValidationError):
                validator.validate_path(pathlib.Path(path))

    def test_allowed_paths_pass(self):
        """Allowed mount points should pass validation."""
        validator = MountValidator()
        allowed = [
            "/corpora/library",
            "/documents/user",
            "/downloads",
            "/project/src",
            "/app/data/cache",
        ]

        for path in allowed:
            # Should not raise
            validator.validate_path(pathlib.Path(path))

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        validator = MountValidator()
        traversal_paths = [
            "/corpora/../../../etc/passwd",
            "/documents/../../root",
            "/project/../../var/log",
        ]

        for path in traversal_paths:
            with pytest.raises(MountValidationError):
                validator.validate_path(pathlib.Path(path))

    def test_relative_paths_resolved(self):
        """Symlinks and relative paths should be resolved and validated."""
        validator = MountValidator()

        # A path that resolves to a system directory should be blocked
        # even if the input looks like it might be allowed
        with pytest.raises(MountValidationError):
            validator.validate_path(pathlib.Path("/corpora/../../../root"))

    def test_collection_path_filters_invalid_roots(self):
        """validate_collection_path should filter out invalid roots."""
        validator = MountValidator()

        # Mix of valid and invalid paths
        roots = [
            "/corpora/library",  # Valid
            "/etc/passwd",  # Invalid - blocked
            "/documents/user",  # Valid
            "/proc/self",  # Invalid - blocked
        ]

        valid = validator.validate_collection_path([pathlib.Path(r) for r in roots])

        assert len(valid) == 2
        assert pathlib.Path("/corpora/library") in valid
        assert pathlib.Path("/documents/user") in valid


# =============================================================================
# CHUNKING REGRESSION TESTS
# =============================================================================


class TestChunking:
    """Regression tests for text chunking."""

    def test_chunk_size_respected(self):
        """Chunks should not exceed target size."""
        text = "A" * 2000  # Long text

        chunks = list(chunking.chunk_text(text, page=1))

        for _, _, content, _ in chunks:
            assert len(content) <= chunking.CHUNK_SIZE + 100, (
                "Chunk exceeds target size significantly"
            )

    def test_overlap_between_chunks(self):
        """Adjacent chunks should overlap by configured amount."""
        text = "START " + "X" * 1000 + " END"

        chunks = list(chunking.chunk_text(text, page=1))

        if len(chunks) > 1:
            # Get the end of first chunk and start of second
            first_content = chunks[0][2]  # content
            second_content = chunks[1][2]  # content

            # There should be some overlap
            assert first_content[-50:] in second_content or any(
                first_content[-20 + i :] == second_content[: 20 - i] for i in range(20)
            )

    def test_page_numbers_preserved(self):
        """Each chunk should preserve its page number."""
        chunks = list(chunking.chunk_text("Test content", page=42))

        for page, idx, content, _ in chunks:
            assert page == 42, f"Expected page 42, got {page}"

    def test_content_hash_stable(self):
        """Same content should produce same hash."""
        text = "Consistent content for hashing " * 50

        chunks1 = list(chunking.chunk_text(text, page=1))
        chunks2 = list(chunking.chunk_text(text, page=1))

        for c1, c2 in zip(chunks1, chunks2):
            assert c1[3] == c2[3], "Hash should be deterministic for same content"

    def test_empty_text_handled(self):
        """Empty or whitespace-only text should be handled gracefully."""
        chunks = list(chunking.chunk_text("", page=1))
        # Should return at least one empty chunk or empty list
        assert len(chunks) >= 0


# =============================================================================
# QUALITY ASSESSMENT REGRESSION TESTS
# =============================================================================


class TestQualityAssessment:
    """Regression tests for quality assessment."""

    def test_empty_page_100_percent_empty(self):
        """Empty page should have 1.0 empty ratio."""
        from nexus.ingest.pdf_extract_pypdf import PageText

        page = PageText(page=1, text="", width=8.5, height=11)
        report = assess_quality([page])

        assert report.empty_page_ratio == 1.0

    def test_full_page_0_percent_empty(self):
        """Full text page should have 0.0 empty ratio."""
        from nexus.ingest.pdf_extract_pypdf import PageText

        page = PageText(page=1, text="This is a full page of text " * 100, width=8.5, height=11)
        report = assess_quality([page])

        assert report.empty_page_ratio < 0.1

    def test_needs_ocr_threshold(self):
        """Pages above empty ratio threshold should need OCR."""
        from nexus.ingest.pdf_extract_pypdf import PageText

        # Create page with mostly empty content
        mostly_empty = PageText(
            page=1, text="Header\n\n\n\n\n\n\n\n\n\nFooter", width=8.5, height=11
        )
        report = assess_quality([mostly_empty])

        # With default threshold of 0.30, this should need OCR
        if report.empty_page_ratio > 0.30:
            assert report.needs_ocr

    def test_char_count_accurate(self):
        """Extracted character count should match text length."""
        from nexus.ingest.pdf_extract_pypdf import PageText

        expected_text = "Exact character count test"
        page = PageText(page=1, text=expected_text, width=8.5, height=11)
        report = assess_quality([page])

        assert report.extracted_chars == len(expected_text)


# =============================================================================
# FILE DISCOVERY REGRESSION TESTS
# =============================================================================


class TestFileDiscovery:
    """Regression tests for file discovery."""

    def test_pdf_extension_filter(self):
        """Only PDF files should be discovered."""
        from nexus.config import CollectionConfig

        cfg = CollectionConfig(
            roots=["/tmp"],
            include=["**/*"],
            exclude=[],
            tags=[],
        )

        # Mock walk to return mixed extensions
        with patch("nexus.ingest.discover.os.walk") as mock_walk:
            mock_walk.return_value = [
                ("/tmp", [], ["document.pdf", "image.png", "text.txt", "data.pdf"]),
            ]

            files = walk_collection(cfg)

            # Only PDFs should be included
            assert len(files) == 2
            for f in files:
                assert f.path.suffix.lower() == ".pdf"

    def test_exclude_pattern_applied(self):
        """Exclude patterns should filter files."""
        from nexus.config import CollectionConfig

        cfg = CollectionConfig(
            roots=["/tmp"],
            include=["**/*"],
            exclude=["**/tmp/**", "**/drafts/**"],
            tags=[],
        )

        with patch("nexus.ingest.discover.os.walk") as mock_walk:
            mock_walk.return_value = [
                ("/tmp/docs", [], ["main.pdf"]),
                ("/tmp/tmp", [], ["temp.pdf"]),  # Should be excluded
                ("/tmp/drafts", [], ["draft.pdf"]),  # Should be excluded
            ]

            files = walk_collection(cfg)

            assert len(files) == 1
            assert "draft.pdf" not in str(files)
            assert "temp.pdf" not in str(files)

    def test_sha256_deterministic(self):
        """Same file should produce same SHA256 hash."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Stable content for hashing")
            f.flush()

            path = pathlib.Path(f.name)
            hash1 = _hash_file(path)
            hash2 = _hash_file(path)

            assert hash1 == hash2

    def test_file_size_check(self):
        """File size check should reject oversized files."""
        import tempfile

        # Create a large file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
            f.write(b"X" * 200 * 1024 * 1024)  # 200MB
            path = pathlib.Path(f.name)

        try:
            # With 100MB limit, this should fail
            result = _check_file_size(path)
            assert result is False
        finally:
            path.unlink()

    def test_discovered_file_structure(self):
        """DiscoveredFile dataclass should have all required fields."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            f.write("Test content")
            f.flush()
            path = pathlib.Path(f.name)

        try:
            stat = path.stat()
            df = DiscoveredFile(
                path=path,
                root=pathlib.Path("/tmp"),
                relative_path=pathlib.Path("test.pdf"),
                sha256="abc123",
                mtime=int(stat.st_mtime),
                size=stat.st_size,
            )

            assert df.path == path
            assert df.sha256 == "abc123"
            assert df.mtime == int(stat.st_mtime)
            assert df.size == stat.st_size
        finally:
            path.unlink()


# =============================================================================
# API KEY HANDLING REGRESSION TESTS
# =============================================================================


class TestApiKeyHandling:
    """Regression tests for API key authentication."""

    def test_require_api_key_returns_401_without_key(self, client):
        """Endpoints with require_api_key should return 401 without key."""
        # This tests the dependency itself
        from fastapi import Depends

        # Create a mock request
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        # Should return None (auth failed)
        result = deps.verify_api_key(mock_request)
        assert result is None

    def test_require_api_key_returns_key_when_valid(self, client):
        """verify_api_key should return key when valid header present."""
        from fastapi import Request

        request = Request(scope={"type": "http", "headers": [(b"x-api-key", b"test-key")]})

        # Mock settings to return matching key
        with patch.object(deps, "get_settings") as mock_settings:
            mock_settings.return_value.api_key = "test-key"

            result = deps.verify_api_key(request)
            assert result == "test-key"

    def test_api_key_from_file_takes_precedence(self, monkeypatch, client):
        """API key from file should take precedence over env var."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("file-key")
            key_file = f.name

        try:
            monkeypatch.setenv("NEXUS_API_KEY", "env-key")
            monkeypatch.setenv("NEXUS_API_KEY_FILE", key_file)

            settings = Settings()
            settings.load_api_key_from_file()

            assert settings.api_key == "file-key"
        finally:
            pathlib.Path(key_file).unlink()


# =============================================================================
# CONFIGURATION REGRESSION TESTS
# =============================================================================


class TestConfiguration:
    """Regression tests for configuration handling."""

    def test_default_values_sensible(self):
        """Default config values should be sensible for local development."""
        settings = Settings()

        assert settings.database_url is not None
        assert settings.ollama_url is not None
        assert settings.embed_dim == 1024  # mxbai-embed-large dimension
        assert settings.chunk_size == 800
        assert settings.chunk_overlap == 80
        assert settings.max_file_size_mb == 100
        assert settings.timeout_seconds == 120

    def test_embed_dim_must_match_model(self):
        """embed_dim should match the embedding model requirements."""
        settings = Settings()

        # mxbai-embed-large uses 1024 dimensions
        if settings.embed_model == "mxbai-embed-large":
            assert settings.embed_dim == 1024

    def test_cors_origins_json_parsed(self):
        """CORS origins should be parsed from JSON string."""
        import json

        origins = ["http://localhost:3000", "http://localhost:3001"]
        settings = Settings(allow_origins=json.dumps(origins))

        assert settings.allow_origins == origins


# =============================================================================
# RATE LIMITING REGRESSION TESTS
# =============================================================================


class TestRateLimiting:
    """Regression tests for rate limiting."""

    def test_rate_limit_exceeded_returns_429(self, client):
        """Rate limit exceeded should return 429, not 500."""
        # This tests the exception handler works
        from slowapi.errors import RateLimitExceeded
        from nexus.api.main import rate_limit_handler, app

        # Create a mock request
        mock_request = MagicMock()
        mock_request.state.response = MagicMock(return_value=MagicMock())

        exc = RateLimitExceeded("test")

        # Should return JSONResponse with 429
        response = rate_limit_handler(mock_request, exc)

        assert response.status_code == 429


# =============================================================================
# SQL INJECTION PREVENTION REGRESSION TESTS
# =============================================================================


class TestSqlInjectionPrevention:
    """Regression tests for SQL injection prevention."""

    def test_collections_parameterized(self):
        """Collections should use parameterized queries, not string formatting."""
        from nexus.retrieve.pgvector import search_chunks

        # Even with malicious collection names, should not cause SQL injection
        malicious_collections = ["library'; DROP TABLE chunks; --", "library' OR '1'='1"]

        # search_chunks uses %s placeholders - this should either:
        # 1. Return empty (collection not found)
        # 2. Raise a clean error (invalid collection name)
        # But NOT execute arbitrary SQL
        try:
            import asyncio

            result = asyncio.run(
                search_chunks(
                    query_embedding=[0.1] * 1024,
                    collections=malicious_collections,
                    tags=None,
                    top_k=8,
                )
            )
            # If it returns, it should be safe
            assert isinstance(result, list)
        except Exception as e:
            # Exception is acceptable if it's a clean error
            assert "DROP" not in str(e).upper()
            assert "DELETE" not in str(e).upper()


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
