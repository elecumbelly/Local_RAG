from __future__ import annotations

import hashlib
import os
import pathlib
from dataclasses import dataclass
from typing import Iterable, List

import yaml
from pydantic import BaseModel

from nexus.config import CollectionConfig, get_settings


def _max_file_size_bytes() -> int:
    return get_settings().max_file_size_mb * 1024 * 1024


@dataclass
class DiscoveredFile:
    path: pathlib.Path
    root: pathlib.Path
    relative_path: pathlib.Path
    sha256: str
    mtime: int
    size: int


def walk_collection(cfg: CollectionConfig) -> List[DiscoveredFile]:
    files: list[DiscoveredFile] = []
    include = set(cfg.include)
    exclude = set(cfg.exclude)
    for root in map(pathlib.Path, cfg.roots):
        for dirpath, _, filenames in os.walk(root):
            dir_path = pathlib.Path(dirpath)
            for filename in filenames:
                if not filename.lower().endswith(".pdf"):
                    continue
                abs_path = dir_path.joinpath(filename)
                if _skip(abs_path, include, exclude):
                    continue
                if not _check_file_size(abs_path):
                    continue
                sha256 = _hash_file(abs_path)
                stat = abs_path.stat()
                relative_path = abs_path.relative_to(root)
                files.append(
                    DiscoveredFile(
                        path=abs_path,
                        root=root,
                        relative_path=relative_path,
                        sha256=sha256,
                        mtime=int(stat.st_mtime),
                        size=stat.st_size,
                    )
                )
    return files


def _check_file_size(path: pathlib.Path) -> bool:
    try:
        stat = path.stat()
        if stat.st_size > _max_file_size_bytes():
            return False
        return True
    except OSError:
        return False


def _skip(path: pathlib.Path, include: set[str], exclude: set[str]) -> bool:
    rel = str(path)
    for pattern in exclude:
        if path.match(pattern):
            return True
    if include:
        return not any(path.match(pattern) for pattern in include)
    return False


def _hash_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
