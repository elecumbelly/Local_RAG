from __future__ import annotations

from typing import List, Optional
import pathlib

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from psycopg import rows

from nexus.api import deps
from nexus.config import get_settings
from nexus.db import db_connection

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(deps.require_api_key)],
)


def _ensure_allowed_path(path: pathlib.Path, settings) -> None:
    """
    Prevent serving files outside allowed roots.
    """
    resolved = path.resolve()
    allowed_roots = [settings.processed_dir.resolve()]
    for coll in settings.corpora().collections.values():
        allowed_roots.extend([pathlib.Path(root).resolve() for root in coll.roots])
    if not any(resolved.is_relative_to(root) for root in allowed_roots):
        raise HTTPException(status_code=400, detail="Requested file outside allowed roots")


@router.get("")
async def list_documents(
    collection: Optional[str] = None,
    q: Optional[str] = None,
    tag: Optional[str] = None,
):
    if collection and len(collection) > 100:
        raise HTTPException(status_code=400, detail="Collection name too long")
    if q and len(q) > 500:
        raise HTTPException(status_code=400, detail="Query too long")
    if tag and len(tag) > 100:
        raise HTTPException(status_code=400, detail="Tag too long")

    settings = get_settings()
    clauses = []
    params: list = []
    if collection:
        clauses.append("c.name = %s")
        params.append(collection)
    if q:
        clauses.append("d.path ILIKE %s")
        params.append(f"%{q}%")
    if tag:
        clauses.append("%s = ANY(d.tags)")
        params.append(tag)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
    SELECT d.id, d.path, d.tags, d.status, d.ocr_applied, d.processed_path, d.extracted_chars, d.empty_page_ratio, d.quality, c.name AS collection
    FROM documents d
    JOIN collections c ON c.id = d.collection_id
    {where}
    ORDER BY d.updated_at DESC
    LIMIT 200;
    """
    async with db_connection(row_factory=rows.dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            result_rows = await cur.fetchall()
            return result_rows


@router.get("/collections")
async def list_collections():
    settings = get_settings()
    items = []
    corpora = settings.corpora().collections
    for name, cfg in corpora.items():
        items.append({"name": name, "tags": cfg.tags, "roots": cfg.roots})
    return items


@router.patch("/{doc_id}/tags")
async def update_tags(doc_id: int, tags: List[str]):
    async with db_connection(row_factory=rows.dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE documents SET tags = %s WHERE id = %s RETURNING id", (tags, doc_id)
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "tags": tags}


@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    async with db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
    return {"status": "deleted"}


@router.get("/{doc_id}/file")
async def fetch_document_file(doc_id: int, processed: bool = False):
    settings = get_settings()
    async with db_connection(row_factory=rows.dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT path, processed_path FROM documents WHERE id = %s",
                (doc_id,),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
    target = row["processed_path"] if processed and row.get("processed_path") else row["path"]
    file_path = pathlib.Path(target)
    _ensure_allowed_path(file_path, settings)
    resolved = file_path.resolve()
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(resolved, filename=resolved.name)
