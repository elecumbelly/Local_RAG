from __future__ import annotations

import hashlib
from typing import Iterable, List

from nexus.config import get_settings


def chunk_text(text: str, page: int) -> list[tuple[int, str, str]]:
    """Return list of (chunk_index, content, content_hash)."""
    settings = get_settings()
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap
    if len(text) <= chunk_size:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return [(0, text, content_hash)]
    chunks: list[tuple[int, str, str]] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        content_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
        chunks.append((idx, chunk, content_hash))
        idx += 1
        # If we've reached the end of text, we're done
        if end >= len(text):
            break
        # Advance by (chunk_size - overlap), ensuring we always make progress
        prev_start = start
        start = end - overlap
        if start <= prev_start:
            # If overlap >= chunk, we'd get stuck - ensure forward progress
            start = prev_start + 1
    return chunks
