from __future__ import annotations

import json

import psycopg
from fastapi import APIRouter, Depends

from nexus.api import deps
from nexus.config import get_settings
from nexus.db import db_connection
from nexus.eval.inspect_suite import run_eval

router = APIRouter(
    prefix="/eval",
    tags=["eval"],
    dependencies=[Depends(deps.require_api_key)],
)


@router.post("/run")
async def eval_run():
    score = run_eval()
    return {"score": score}


@router.get("/latest")
async def eval_latest():
    async with db_connection(row_factory=psycopg.rows.dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT er.score, er.created_at
                FROM eval_runs er
                JOIN collections c ON c.id = er.collection_id
                WHERE c.name = 'test'
                ORDER BY er.created_at DESC
                LIMIT 1
                """
            )
            row = await cur.fetchone()
            if not row:
                return {"score": None}
            return {"score": row["score"], "created_at": row["created_at"]}
