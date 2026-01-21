from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence


@dataclass
class RetrievedChunk:
    document_id: int
    path: str
    page: int
    score: float
    content: str


class Embedder(Protocol):
    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        ...


class Retriever(Protocol):
    async def search(
        self,
        query_embedding: list[float],
        collections: list[str],
        tags: list[str] | None,
        top_k: int,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]:
        ...
