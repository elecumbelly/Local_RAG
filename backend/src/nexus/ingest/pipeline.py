from __future__ import annotations

import asyncio
import json
import logging
import pathlib
from dataclasses import dataclass
from typing import List

import psycopg
from psycopg import rows

from nexus.config import get_settings
from nexus.db import db_connection
from nexus.embed.ollama_embed import OllamaEmbedder
from nexus.ingest import chunking, discover, ocr, pdf_extract_pypdf, quality

logger = logging.getLogger(__name__)


@dataclass
class IngestSummary:
    scanned: int
    processed: int
    skipped: int
    failed: int
    duplicates: int = 0


async def ensure_collection(cur: psycopg.AsyncCursor, name: str):
    settings = get_settings()
    await cur.execute(
        """
        INSERT INTO collections(name, version, embed_model, embed_dim, chunk_size, overlap, active)
        VALUES (%s, 1, %s, %s, %s, %s, TRUE)
        ON CONFLICT (name, version) DO UPDATE SET embed_model = EXCLUDED.embed_model
        RETURNING id, embed_dim;
        """,
        (
            name,
            settings.embed_model,
            settings.embed_dim,
            settings.chunk_size,
            settings.chunk_overlap,
        ),
    )
    row = await cur.fetchone()
    if row["embed_dim"] != settings.embed_dim:
        raise ValueError("Embedding dimension mismatch for collection contract")
    return row["id"]


async def _doc_exists(
    cur: psycopg.AsyncCursor, collection_id: int, path: str, sha: str, mtime: int
):
    await cur.execute(
        """
        SELECT id FROM documents
        WHERE collection_id = %s AND path = %s AND source_sha256 = %s AND mtime = %s
        """,
        (collection_id, path, sha, mtime),
    )
    row = await cur.fetchone()
    return row["id"] if row else None


async def _has_duplicate(cur: psycopg.AsyncCursor, collection_id: int, sha: str, path: str) -> bool:
    await cur.execute(
        """
        SELECT path FROM documents WHERE collection_id = %s AND source_sha256 = %s AND path <> %s
        """,
        (collection_id, sha, path),
    )
    return bool(await cur.fetchone())


async def _upsert_document(
    cur: psycopg.AsyncCursor,
    collection_id: int,
    path: str,
    sha: str,
    mtime: int,
    size: int,
    tags: list[str],
    ocr_applied: bool,
    processed_path: str | None,
    quality_report: quality.QualityReport,
    status: str = "ingested",
):
    await cur.execute(
        """
        INSERT INTO documents(collection_id, path, source_sha256, mtime, size, tags, status, ocr_applied, processed_path, extracted_chars, empty_page_ratio, quality, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (collection_id, path) DO UPDATE
        SET source_sha256 = EXCLUDED.source_sha256,
            mtime = EXCLUDED.mtime,
            size = EXCLUDED.size,
            tags = EXCLUDED.tags,
            status = EXCLUDED.status,
            ocr_applied = EXCLUDED.ocr_applied,
            processed_path = EXCLUDED.processed_path,
            extracted_chars = EXCLUDED.extracted_chars,
            empty_page_ratio = EXCLUDED.empty_page_ratio,
            quality = EXCLUDED.quality,
            updated_at = NOW()
        RETURNING id;
        """,
        (
            collection_id,
            path,
            sha,
            mtime,
            size,
            tags,
            status,
            ocr_applied,
            processed_path,
            quality_report.extracted_chars,
            quality_report.empty_page_ratio,
            json.dumps(
                {
                    "doc": {
                        "extracted_chars": quality_report.extracted_chars,
                        "empty_page_ratio": quality_report.empty_page_ratio,
                    },
                    "pages": quality_report.pages,
                }
            ),
        ),
    )
    row = await cur.fetchone()
    return row["id"]


async def _insert_chunks(
    cur: psycopg.AsyncCursor,
    document_id: int,
    page_chunks: list[tuple[int, int, str, str, list[float]]],
):
    await cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
    for page, idx, content, content_hash, embedding in page_chunks:
        await cur.execute(
            """
            INSERT INTO chunks(document_id, page, chunk_index, content, content_hash, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (document_id, page, idx, content, content_hash, embedding),
        )


def _quality_from_pages(pages: list[pdf_extract_pypdf.PageText]) -> quality.QualityReport:
    metrics: list[dict] = []
    for page in pages:
        text = page.text or ""
        chars = len(text)
        metrics.append({"page": page.page, "chars": chars, "empty": len(text.strip()) == 0})
    total_chars = sum(m["chars"] for m in metrics)
    empty_ratio = sum(1 for m in metrics if m["empty"]) / max(1, len(metrics))
    return quality.QualityReport(
        extracted_chars=total_chars, empty_page_ratio=empty_ratio, pages=metrics
    )


async def ingest_collection(name: str) -> IngestSummary:
    settings = get_settings()
    corpora = settings.corpora()
    if name not in corpora.collections:
        raise ValueError(f"Unknown collection {name}")
    cfg = corpora.collections[name]
    logger.info("Starting ingest for collection %s", name)
    discovered = discover.walk_collection(cfg)
    logger.info("Discovered %d files in collection %s", len(discovered), name)
    embedder = OllamaEmbedder()
    summary = IngestSummary(scanned=len(discovered), processed=0, skipped=0, failed=0, duplicates=0)

    async with db_connection(row_factory=rows.dict_row) as conn:
        async with conn.cursor() as cur:
            collection_id = await ensure_collection(cur, name)
        await conn.commit()

    for file in discovered:
        try:
            async with db_connection(row_factory=rows.dict_row) as conn:
                async with conn.cursor() as cur:
                    unchanged = await _doc_exists(
                        cur, collection_id, str(file.path), file.sha256, file.mtime
                    )
                    if unchanged:
                        summary.skipped += 1
                        await conn.commit()
                        continue

                    if await _has_duplicate(cur, collection_id, file.sha256, str(file.path)):
                        await _upsert_document(
                            cur,
                            collection_id,
                            str(file.path),
                            file.sha256,
                            file.mtime,
                            file.size,
                            cfg.tags,
                            False,
                            None,
                            quality.QualityReport(extracted_chars=0, empty_page_ratio=0, pages=[]),
                            status="duplicate",
                        )
                        summary.duplicates += 1
                        await conn.commit()
                        continue

                # Extract text outside SQL transaction
            logger.info("Extracting text from %s", file.path)
            pages = pdf_extract_pypdf.extract_text(str(file.path))
            logger.info("Extracted %d pages from %s", len(pages), file.path)
            report = _quality_from_pages(pages)

            source_path = file.path
            processed_path: str | None = None
            ocr_applied = False
            if report.needs_ocr:
                logger.info("Running OCR on %s", file.path)
                source_path = ocr.run_ocr(file.path, name, relative_root=file.root)
                processed_path = str(source_path)
                pages = pdf_extract_pypdf.extract_text(str(source_path))
                report = _quality_from_pages(pages)
                ocr_applied = True

            page_chunks: list[tuple[int, int, str, str, list[float]]] = []
            total_chunks = 0
            for page in pages:
                for idx, content, content_hash in chunking.chunk_text(page.text, page.page):
                    total_chunks += 1
            logger.info("Will embed %d chunks from %s", total_chunks, file.path)

            chunk_num = 0
            for page in pages:
                for idx, content, content_hash in chunking.chunk_text(page.text, page.page):
                    chunk_num += 1
                    if chunk_num % 10 == 0:
                        logger.info("Embedding chunk %d/%d", chunk_num, total_chunks)
                    embeddings = await embedder.embed_documents([content])
                    embedding = embeddings[0]
                    if len(embedding) != settings.embed_dim:
                        raise ValueError("Embedding dimension mismatch")
                    page_chunks.append((page.page, idx, content, content_hash, embedding))

            async with db_connection(row_factory=rows.dict_row) as conn:
                async with conn.cursor() as cur:
                    doc_id = await _upsert_document(
                        cur,
                        collection_id,
                        str(file.path),
                        file.sha256,
                        file.mtime,
                        file.size,
                        cfg.tags,
                        ocr_applied,
                        processed_path,
                        report,
                    )
                    await _insert_chunks(cur, doc_id, page_chunks)
                await conn.commit()
            summary.processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to ingest %s: %s", file.path, exc)
            summary.failed += 1
    return summary


async def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True, help="Collection name to ingest")
    args = parser.parse_args()
    summary = await ingest_collection(args.collection)
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
