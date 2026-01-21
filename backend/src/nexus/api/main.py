from __future__ import annotations

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from nexus.api import routes_chat, routes_docs, routes_eval, routes_ingest, routes_models
from nexus.config import get_settings
from nexus.db import ensure_schema

limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour", "10/minute"])

app = FastAPI(title="Nexus Local RAG")

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    await ensure_schema()


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(routes_ingest.router)
app.include_router(routes_chat.router)
app.include_router(routes_docs.router)
app.include_router(routes_eval.router)
app.include_router(routes_models.router)
