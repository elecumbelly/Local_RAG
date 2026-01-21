from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import tempfile
import os

from nexus.hooks.executor import HookExecutor, IngestHookError


@pytest.fixture
def temp_hooks_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_path = Path(tmpdir) / "hooks"
        hooks_path.mkdir()
        yield hooks_path


def test_hook_executor_initialization():
    executor = HookExecutor(hooks_dir=Path("/custom/hooks"))

    assert executor.hooks_dir == Path("/custom/hooks")


def test_run_hook_nonexistent_path():
    executor = HookExecutor(hooks_dir=Path("/nonexistent/hooks"))

    result = executor._run_hook("pre-ingest-library.sh", {})

    assert result == {}


def test_run_hook_not_executable(temp_hooks_dir):
    hook_path = temp_hooks_dir / "test-hook.sh"
    hook_path.write_text("#!/bin/bash\necho test")
    os.chmod(hook_path, 0o644)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor._run_hook("test-hook.sh", {})

    assert result == {}


def test_run_hook_timeout(temp_hooks_dir):
    hook_path = temp_hooks_dir / "timeout-hook.sh"
    hook_path.write_text("#!/bin/bash\nsleep 70")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor._run_hook("timeout-hook.sh", {})

    assert result == {}


def test_run_hook_non_zero_exit(temp_hooks_dir):
    hook_path = temp_hooks_dir / "fail-hook.sh"
    hook_path.write_text("#!/bin/bash\nexit 1")
    hook_path.chmod(0o755)

    executor = HookExecutor(hooks_dir=temp_hooks_dir)
    result = executor._run_hook("fail-hook.sh", {})

    assert result == {}


def test_parse_hook_output_modified_query():
    executor = HookExecutor()

    output = "Some other output\nMODIFIED_QUERY:expanded query\nMore output"
    result = executor._parse_hook_output(output)

    assert result.get("query") == "expanded query"


def test_parse_hook_output_skip():
    executor = HookExecutor()

    output = "Some output\nSKIP:validation failed\nMore output"
    result = executor._parse_hook_output(output)

    assert result.get("skip") == "validation failed"


def test_parse_hook_output_metadata():
    executor = HookExecutor()

    output = "MODIFIED_QUERY:test\nMETADATA:key=value\nMETADATA:other=data"
    result = executor._parse_hook_output(output)

    assert result.get("query") == "test"
    assert result.get("metadata_key") == "value"
    assert result.get("metadata_other") == "data"


def test_parse_hook_output_empty():
    executor = HookExecutor()

    output = "Just regular output"
    result = executor._parse_hook_output(output)

    assert result == {}


def test_parse_hook_output_multiple_same_type():
    executor = HookExecutor()

    output = "MODIFIED_QUERY:first\nMODIFIED_QUERY:second"
    result = executor._parse_hook_output(output)

    assert result.get("query") == "second"


def test_parse_hook_output_whitespace_handling():
    executor = HookExecutor()

    output = "MODIFIED_QUERY:  query with spaces  "
    result = executor._parse_hook_output(output)

    assert result.get("query") == "query with spaces"


def test_parse_hook_output_colon_in_value():
    executor = HookExecutor()

    output = "METADATA:key=value:with:colons"
    result = executor._parse_hook_output(output)

    assert result.get("metadata_key") == "value:with:colons"


def test_hook_executor_with_default_hooks_dir():
    executor = HookExecutor()

    assert executor.hooks_dir == Path("hooks")
