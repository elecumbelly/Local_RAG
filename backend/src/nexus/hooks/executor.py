from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IngestHookError(Exception):
    pass


class HookExecutor:
    def __init__(self, hooks_dir: Path | None = None):
        self.hooks_dir = hooks_dir or Path("hooks")

    def run_pre_ingest(self, collection: str, files: list[Path]) -> dict[str, str]:
        return self._run_hook(
            f"pre-ingest-{collection}.sh",
            {"NEXUS_COLLECTION": collection, "NEXUS_FILES": ",".join(str(f) for f in files)},
        )

    def run_post_ingest(self, collection: str, stats: dict[str, int]) -> dict[str, str]:
        env = {
            "NEXUS_COLLECTION": collection,
            "NEXUS_PROCESSED_COUNT": str(stats.get("processed", 0)),
            "NEXUS_SKIPPED_COUNT": str(stats.get("skipped", 0)),
            "NEXUS_FAILED_COUNT": str(stats.get("failed", 0)),
        }
        return self._run_hook(f"post-ingest-{collection}.sh", env)

    def _run_hook(self, hook_name: str, env: dict[str, str]) -> dict[str, str]:
        hook_path = self.hooks_dir / hook_name

        if not hook_path.exists():
            logger.debug(f"Hook not found: {hook_path}")
            return {}

        if not os.access(hook_path, os.X_OK):
            logger.warning(f"Hook exists but not executable: {hook_path}")
            return {}

        logger.info(f"Running hook: {hook_path}")

        try:
            result = subprocess.run(
                [str(hook_path)],
                env={**os.environ, **env},
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.warning(
                    f"Hook {hook_name} failed with exit code {result.returncode}: {result.stderr}"
                )
                return {}

            return self._parse_hook_output(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error(f"Hook {hook_name} timed out after 60 seconds")
            return {}
        except Exception as e:
            logger.error(f"Hook {hook_name} failed: {e}")
            return {}

    def _parse_hook_output(self, output: str) -> dict[str, str]:
        result = {}
        for line in output.strip().split("\n"):
            if line.startswith("MODIFIED_QUERY:"):
                result["query"] = line[len("MODIFIED_QUERY:") :].strip()
            elif line.startswith("SKIP:"):
                result["skip"] = line[len("SKIP:") :].strip()
            elif line.startswith("METADATA:"):
                key, value = line[len("METADATA:") :].split("=", 1)
                result[f"metadata_{key}"] = value
        return result
