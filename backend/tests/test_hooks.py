from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import tempfile
import os

from nexus.hooks.executor import HookExecutor


@pytest.fixture
def hook_executor():
    return HookExecutor(hooks_dir=Path("/tmp/hooks"))


@pytest.fixture
def temp_hooks_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_path = Path(tmpdir) / "hooks"
        hooks_path.mkdir()
        yield hooks_path


def test_run_pre_ingest_hook_not_exists(hook_executor):
    result = hook_executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {}


def test_run_pre_ingest_hook_not_executable(temp_hooks_dir, hook_executor):
    hook_path = temp_hooks_dir / "pre-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\necho 'pre ingest hook'")
    os.chmod(hook_path, 0o644)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {}


def test_run_pre_ingest_hook_success(temp_hooks_dir, hook_executor):
    hook_path = temp_hooks_dir / "pre-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\necho 'METADATA:pre_ingest=true'")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {"metadata_pre_ingest": "true"}


def test_run_pre_ingest_hook_skips_ingestion(temp_hooks_dir, hook_executor):
    hook_path = temp_hooks_dir / "pre-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\necho 'SKIP:validation failed'")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {"skip": "validation failed"}


def test_run_pre_ingest_hook_modifies_query(temp_hooks_dir, hook_executor):
    hook_path = temp_hooks_dir / "pre-query.sh"
    hook_path.write_text("#!/bin/bash\necho 'MODIFIED_QUERY:expanded query text'")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {"query": "expanded query text"}


def test_run_post_ingest_hook_not_exists(hook_executor):
    result = hook_executor.run_post_ingest("library", {"processed": 10, "skipped": 2, "failed": 0})

    assert result == {}


def test_run_post_ingest_hook_success(temp_hooks_dir):
    hook_path = temp_hooks_dir / "post-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\necho 'METADATA:post_ingest=complete'")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_post_ingest("library", {"processed": 10, "skipped": 2, "failed": 0})

    assert result == {"metadata_post_ingest": "complete"}


def test_run_post_ingest_hook_logs_metrics(temp_hooks_dir):
    hook_path = temp_hooks_dir / "post-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\necho 'Ingestion complete'")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_post_ingest("library", {"processed": 10, "skipped": 2, "failed": 0})

    assert result == {}


def test_hook_timeout(temp_hooks_dir):
    hook_path = temp_hooks_dir / "pre-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\nsleep 70")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {}


def test_hook_non_zero_exit_code(temp_hooks_dir):
    hook_path = temp_hooks_dir / "pre-ingest-library.sh"
    hook_path.write_text("#!/bin/bash\nexit 1")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor.run_pre_ingest("library", [Path("/corpora/test.pdf")])

    assert result == {}
