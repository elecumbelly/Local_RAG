from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class MountValidationError(Exception):
    pass


class MountValidator:
    ALLOWED_BASE_PATHS = {"/corpora", "/documents", "/downloads", "/project", "/app/data"}

    BLOCKED_PATTERNS = {
        "/etc",
        "/proc",
        "/sys",
        "/root",
        "/var/run",
        "/tmp",
    }

    def __init__(self):
        self.allowed_paths = {Path(p) for p in self.ALLOWED_BASE_PATHS}

    def validate_path(self, path: Path) -> None:
        real_path = path.resolve()

        if self._is_blocked_path(real_path):
            raise MountValidationError(f"Path {path} is in blocked system directory")

        if not self._is_allowed_path(real_path):
            raise MountValidationError(f"Path {path} is not in allowed mount directories")

        if self._is_path_traversal(real_path):
            raise MountValidationError(f"Path {path} contains path traversal sequence")

    def validate_collection_path(self, collection_roots: list[Path]) -> list[Path]:
        valid_roots = []
        for root in collection_roots:
            try:
                self.validate_path(root)
                valid_roots.append(root)
            except MountValidationError as e:
                logger.warning(f"Skipping invalid path {root}: {e}")
        return valid_roots

    def _is_blocked_path(self, path: Path) -> bool:
        path_str = str(path)
        for blocked in self.BLOCKED_PATTERNS:
            if path_str.startswith(blocked):
                return True
        return False

    def _is_allowed_path(self, path: Path) -> bool:
        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed)
                return True
            except ValueError:
                pass
        return False

    def _is_path_traversal(self, path: Path) -> bool:
        path_str = str(path)
        return ".." in path_str
