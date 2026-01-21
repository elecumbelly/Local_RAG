from __future__ import annotations

import json
from typing import List

import psycopg
from psycopg import rows

from nexus.config import get_settings
from nexus.db import db_connection
from nexus.domain.interfaces import RetrievedChunk


async def search_chunks(
    query_embedding: list[float],
    collections: list[str],
    tags: list[str] | None,
    top_k: int,
    min_score: float | None = None,
) -> List[RetrievedChunk]:
    if not collections:
        return []

    settings = get_settings()
    placeholders = ", ".join(["%s"] * len(collections))
    tag_filter = ""
    params: list = list(collections)
    score_filter = "AND similarity >= %s" if min_score is not None else ""
    sql = f"""
    WITH collection_ids AS (
        SELECT id, embed_dim FROM collections WHERE name IN ({placeholders}) AND active = TRUE
    )
    SELECT
        c.id AS chunk_id,
        d.id AS document_id,
        d.path,
        c.page,
        1 - (c.embedding <=> %s::vector) AS similarity,
        c.content
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    JOIN collection_ids col ON col.id = d.collection_id
    WHERE col.embed_dim = %s
    {"AND d.tags && %s" if tags else ""}
    {score_filter}
    ORDER BY similarity DESC
    LIMIT %s;
    """
    params.append(query_embedding)
    params.append(settings.embed_dim)
    if tags:
        params.append(tags)
    if min_score is not None:
        params.append(min_score)
    params.append(top_k)

    async with db_connection(row_factory=rows.dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            result_rows = await cur.fetchall()
            results: list[RetrievedChunk] = []
            for row in result_rows:
                results.append(
                    RetrievedChunk(
                        document_id=row["document_id"],
                        path=row["path"],
                        page=row["page"],
                        score=float(row["similarity"]),
                        content=row["content"],
                    )
                )
            return results
