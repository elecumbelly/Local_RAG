from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Collection:
    id: int
    name: str
    version: int
    embed_model: str
    embed_dim: int
    chunk_size: int
    overlap: int
    active: bool = True
    created_at: datetime | None = None


@dataclass
class Document:
    id: int
    collection_id: int
    path: str
    source_sha256: str
    mtime: int
    size: int
    tags: List[str]
    status: str
    ocr_applied: bool
    extracted_chars: int
    empty_page_ratio: float
    error: Optional[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Chunk:
    id: int
    document_id: int
    page: int
    chunk_index: int
    content: str
    content_hash: str
    embedding: list[float] | None


@dataclass
class EvalRun:
    id: int
    collection_id: int
    model: str
    score: dict
    created_at: datetime
