from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

import psycopg
from psycopg.rows import dict_row

from .config import get_settings


def _conn_args() -> dict:
    return {"row_factory": dict_row, "autocommit": True}


async def ensure_schema() -> None:
    settings = get_settings()
    conn = await psycopg.AsyncConnection.connect(settings.database_url, **_conn_args())
    try:
        async with conn.cursor() as cur:
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await cur.execute(open_schema_sql())
    finally:
        await conn.close()


def open_schema_sql() -> str:
    from importlib.resources import files

    schema_path = files("nexus").joinpath("schema.sql")
    with open(schema_path, "r", encoding="utf-8") as handle:
        return handle.read()


@asynccontextmanager
async def db_cursor() -> AsyncIterator[psycopg.AsyncCursor]:
    settings = get_settings()
    conn = await psycopg.AsyncConnection.connect(settings.database_url, **_conn_args())
    try:
        async with conn.cursor() as cur:
            yield cur
    finally:
        await conn.close()


@asynccontextmanager
async def db_connection(row_factory=dict_row) -> AsyncIterator[psycopg.AsyncConnection]:
    """Async context manager for database connections."""
    settings = get_settings()
    conn = await psycopg.AsyncConnection.connect(settings.database_url, row_factory=row_factory)
    try:
        yield conn
    finally:
        await conn.close()


async def run_tx(fn: Callable[[psycopg.AsyncCursor], asyncio.Future]):
    async with db_cursor() as cur:
        return await fn(cur)
