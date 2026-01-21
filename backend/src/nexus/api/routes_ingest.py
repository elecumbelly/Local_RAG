from __future__ import annotations

import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from nexus.api import deps
from nexus.ingest.pipeline import ingest_collection

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    dependencies=[Depends(deps.require_api_key)],
)


@router.post("/{collection}")
async def trigger_ingest(collection: Literal["library", "dev", "test"]):
    try:
        summary = await ingest_collection(collection)
        return summary.__dict__
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
