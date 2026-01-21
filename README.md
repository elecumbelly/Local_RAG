# Nexus Local RAG

Local, offline retrieval augmented generation stack with incremental ingestion, selective OCR, pgvector search, and streaming chat UI.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              NEXUS LOCAL RAG                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

                              EXTERNAL SERVICES
     ┌─────────────────────────────────────────────────────────────────────────┐
     │                                                                          │
     │   ┌─────────────┐     ┌─────────────────────────────────────────────┐    │
     │   │   USER      │     │           DOCUMENT CORPUS                   │    │
     │   │   BROWSER   │     │                                             │    │
     │   └──────┬──────┘     │   /corpora/                                 │    │
     │          │            │   ├── library/    (main documents)          │    │
     │          │            │   ├── dev/        (development docs)        │    │
     │          │            │   └── test/       (evaluation set)          │    │
     │          │            │                                             │    │
     │          │            └─────────────────────────────────────────────┘    │
     │          │                                                                │
     │          ▼                                                                │
     │   ┌─────────────────────────────────────────────────────────────────┐    │
     │   │                      NGINX / REVERSE PROXY                       │    │
     │   │                  (Terminate TLS, Load Balance)                   │    │
     │   └─────────────────────────────────────────────────────────────────┘    │
     │                                   │                                       │
     └───────────────────────────────────┼───────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER COMPOSE STACK                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                           web (Next.js :3000)                             │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        Frontend Components                         │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │  │
│  │  │  │ChatPanel │  │  Library │  │ Ingest   │  │     Header       │   │  │  │
│  │  │  │          │  │          │  │Controls  │  │  (Auth + Nav)    │   │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │  │  │
│  │  │                                                                      │  │  │
│  │  │  ┌────────────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │                    NextAuth.js Session                         │ │  │  │
│  │  │  │  ┌─────────────┐  ┌─────────────────────────────────────────┐  │ │  │  │
│  │  │  │  │  Login Page │──││  JWT Session  (24h)  ││  Middleware   │  │ │  │  │
│  │  │  │  │ /login      │  ││  Cookie Store        ││  Route Guard  │  │ │  │  │
│  │  │  │  └─────────────┘  └─────────────────────────────────────────┘  │ │  │  │
│  │  │  └────────────────────────────────────────────────────────────────┘ │  │  │
│  │  │                                                                      │  │  │
│  │  │  ┌────────────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │                     API Proxy Route                            │ │  │  │
│  │  │  │  /api/proxy/*  →  Forwards requests + injects API key         │ │  │  │
│  │  │  └────────────────────────────────────────────────────────────────┘ │  │  │
│  │  └──────────────────────────────────────────────────────────────────────┘  │
│  │                                    │                                         │
│  │                                    │ :8000                                  │
│  │                                    ▼                                         │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  │                    api (FastAPI :8000)                               │  │
│  │  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  │                     API Routes                                 │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │  │  │
│  │  │  │  │/chat     │  │/ingest   │  │/documents│  │ /eval          │  │  │  │
│  │  │  │  │ /stream  │  │/{col}    │  │ /models  │  │                │  │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │  │  │
│  │  │  │                                                                      │  │  │
│  │  │  │  ┌────────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  │              Rate Limiting (SlowAPI)                       │  │  │  │
│  │  │  │  │    100 requests/hour  |  10 requests/minute per IP         │  │  │  │
│  │  │  │  └────────────────────────────────────────────────────────────┘  │  │  │
│  │  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │  │                                    │                                  │  │
│  │  │            ┌───────────────────────┼───────────────────────┐         │  │
│  │  │            │                       │                       │         │  │
│  │  │            ▼                       ▼                       ▼         │  │
│  │  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   │  │
│  │  │  │    INGESTION    │   │    RETRIEVAL    │   │    GENERATION   │   │  │
│  │  │  │   Pipeline      │   │   pgvector      │   │   Ollama Chat   │   │  │
│  │  │  └─────────────────┘   └─────────────────┘   └─────────────────┘   │  │
│  │  └──────────────────────────────────────────────────────────────────────┘  │
│  │                                    │                                         │
│  │            ┌───────────────────────┼───────────────────────┐                │
│  │            │                       │                       │                │
│  │            ▼                       ▼                       ▼                │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │
│  │  │    ollama       │   │       db        │   │   processed/    │         │
│  │  │   :11434        │   │   :5432         │   │   :ocr-output   │         │
│  │  │                 │   │  (pgvector)     │   │                 │         │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘         │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAMS                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

  INGESTION FLOW (PDF → Vector DB)
  ─────────────────────────────────
  ┌──────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐
  │  PDF     │───►│  Discover  │───►│  Extract   │───►│  Quality   │───►│  OCR?    │
  │  Files   │    │  (sha256)  │    │  (pypdf)   │    │  Assess    │    │          │
  └──────────┘    └────────────┘    └────────────┘    └────────────┘    └────┬─────┘
                                                                          │        │
                                                                          │ Low    │ High
                                                                          ▼        ▼
                                                                       ┌───────┐  ┌───────┐
                                                                       │ OCRmy │  │ Skip  │
                                                                       │ PDF   │  │ OCR   │
                                                                       └───┬───┘  └───┬───┘
                                                                           │        │
                                                                           ▼        ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────────┐  │
  │  │ Chunk Text  │───►│  Generate   │───►│   Store in  │───►│   HNSW Index   │  │
  │  │ (800 chars) │    │ Embeddings  │    │  pgvector   │    │   Build        │  │
  │  │ +80 overlap │    │ (mxbai)     │    │             │    │                │  │
  │  └─────────────┘    └─────────────┘    └─────────────┘    └────────────────┘  │
  └────────────────────────────────────────────────────────────────────────────────┘

  QUERY FLOW (Question → Answer)
  ─────────────────────────────────
  ┌──────────┐    ┌────────────┐    ┌────────────┐    ┌─────────────┐    ┌────────┐
  │  User    │───►│  Embed     │───►│  Vector    │───►│   Build     │───►│ Stream  │
  │  Query   │    │  Query     │    │  Search    │    │   Prompt    │    │  LLM    │
  └──────────┘    └────────────┘    └────────────┘    └─────────────┘    │ Response│
                                                                        │  +      │
                                                                        │ Citations│
                                                                        └─────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AUTHENTICATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                        NEXTAUTH.JS SESSION FLOW                              │
  │                                                                              │
  │   ┌─────────┐                              ┌───────────────────────────┐    │
  │   │  User   │                              │       NextAuth.js         │    │
  │   │ Browser │                              │                           │    │
  │   └────┬────┘                              │   ┌───────────────────┐   │    │
  │        │                                   │   │  CredentialsProvider│   │    │
  │        │ POST /api/auth/callback           │   │  (Password Auth)   │   │    │
  │        │ credentials={password}            │   └─────────┬─────────┘   │    │
  │        │                                   │             │             │    │
  │        ▼                                   │             ▼             │    │
  │   ┌─────────┐                              │   ┌───────────────────┐   │    │
  │   │  Login  │                              │   │  Validate against │   │    │
  │   │   Page  │                              │   │  NEXUS_PASSWORD   │   │    │
  │   │ /login  │                              │   └─────────┬─────────┘   │    │
  │   └────┬────┘                              │             │             │    │
  │        │                                   │             ▼             │    │
  │        │                                   │   ┌───────────────────┐   │    │
  │        │                                   │   │  Generate JWT     │   │    │
  │        │                                   │   │  Session Cookie   │   │    │
  │        │                                   │   └─────────┬─────────┘   │    │
  │        │                                   │             │             │    │
  │        │                                   │             ▼             │    │
  │        │   Set-Cookie:                     │   ┌───────────────────┐   │    │
  │        │   next-auth.session-token=XXX     │   │  Session Store    │   │    │
  │        │                                   │   │  (JWT in Cookie)  │   │    │
  │        │                                   │   └───────────────────┘   │    │
  │        │                                   │                           │    │
  │        │                                   └───────────────────────────┘    │
  │        │                                                                       │
  │        ▼                                                                       │
  │   ┌─────────────────────────────────────────────────────────────────────┐     │
  │   │                         MIDDLEWARE PROTECTION                        │     │
  │   │                                                                      │     │
  │   │   /chat/*      →  Check session  →  Allow / Redirect to /login     │     │
  │   │   /library/*   →  Check session  →  Allow / Redirect to /login     │     │
  │   │   /ingest/*    →  Check session  →  Allow / Redirect to /login     │     │
  │   │   /eval/*      →  Check session  →  Allow / Redirect to /login     │     │
  │   │   /login       →  Check session  →  Redirect to /chat / Allow      │     │
  │   │   /api/auth/*  →  Allow (auth endpoints)                            │     │
  │   └─────────────────────────────────────────────────────────────────────┘     │
  │                                                                              │
  └─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TECHNOLOGY STACK                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

  FRONTEND                          BACKEND                          DATA
  ┌────────────────────┐           ┌────────────────────┐           ┌─────────────┐
  │  Next.js 14        │           │  FastAPI           │           │ PostgreSQL  │
  │  ├── App Router    │           │  ├── httpx         │           │  (pgvector) │
  │  ├── TypeScript    │           │  ├── psycopg       │           │             │
  │  ├── Tailwind CSS  │           │  ├── pydantic      │           │  ┌────────┐ │
  │  ├── NextAuth.js   │           │  └── tenacity      │           │  │documents│ │
  │  └── Sonner        │           │                    │           │  │chunks   │ │
  │                    │           │  ┌────────────────┐│           │  │collections│
  │  ┌────────────────┐│           │  │Ingestion       ││           │  └────────┘ │
  │  │React Components││           │  │├── pipeline.py ││           │             │
  │  │• ChatPanel     ││           │  │├── chunking.py ││           │  ┌────────┐ │
  │  │• DocumentTable ││           │  │├── pdf_extract ││           │  │ pgvector│ │
  │  │• IngestControls││           │  │└── ocr.py      ││           │  │ HNSW    │ │
  │  │• Header        ││           │  │                ││           │  │ Index   │ │
  │  └────────────────┘│           │  │┌────────────────┐│           │  └────────┘ │
  │                    │           │  ││Retrieval       ││           │             │
  │                    │           │  ││├── pgvector.py ││           │             │
  │                    │           │  │└────────────────┘│           │             │
  │                    │           │  │                  │           │             │
  │                    │           │  │┌────────────────┐│           │             │
  │                    │           │  ││Generation      ││           │             │
  │                    │           │  ││├── ollama_chat ││           │             │
  │                    │           │  ││├── openai_chat ││           │             │
  │                    │           │  │└────────────────┘│           │             │
  │                    │           │  └──────────────────┘           │             │
  │                    │           │                                  │             │
  └────────────────────┘           └──────────────────────────────────┘            │

                                    ┌──────────────────────────────────┐
                                    │           OLLAMA                  │
                                    │  ┌─────────────────────────────┐ │
                                    │  │ mxbai-embed-large (1024d)    │ │
                                    │  │   • Document embeddings      │ │
                                    │  └─────────────────────────────┘ │
                                    │  ┌─────────────────────────────┐ │
                                    │  │ llama3.1:8b-instruct         │ │
                                    │  │   • Chat completions         │ │
                                    │  │   • Streaming responses      │ │
                                    │  └─────────────────────────────┘ │
                                    └──────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER SERVICES                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                         docker-compose.yml                                   │
  │                                                                              │
  │   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐             │
  │   │   db    │────►│  ollama │────►│   api   │────►│   web   │             │
  │   │ :5432   │     │ :11434  │     │ :8000   │     │ :3000   │             │
  │   └─────────┘     └─────────┘     └─────────┘     └─────────┘             │
  │      │                │               │               │                    │
  │      │                │               │               │                    │
  │   pgdata           ollama         api_secrets     web_secrets              │
  │   volume          volume          (api_key)        (api_key)               │
  │                                                                              │
  │   Healthchecks:                                                              │
  │   • db:      pg_isready                                                     │
  │   • ollama:  curl -f http://localhost:11434/api/tags                        │
  │   • api:     curl -f http://localhost:8000/health                           │
  │   • web:     curl -f http://localhost:3000                                  │
  │                                                                              │
  │   Restart Policy: unless-stopped                                             │
  │   Resource Limits: 4G memory, 2 CPUs (api) | 8G memory, 4 CPUs (ollama)    │
  └─────────────────────────────────────────────────────────────────────────────┘

  Production Deployment:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d    │
  │                                                                              │
  │   • Image pinning (sha256 digests)                                          │
  │   • Multi-stage builds (smaller images)                                     │
  │   • Non-root users in containers                                            │
  │   • Docker secrets for API keys                                             │
  │   • Healthchecks on all services                                            │
  └─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              QUICKSTART COMMANDS                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  # Start development environment
  make up                    # Start all services
  make pull-models           # Download embedding + chat models
  make ingest-test           # Ingest test documents
  # Visit http://localhost:3003

  # Production deployment
  make deploy                # Deploy production stack
  # Visit http://localhost:3000

  # GPU support
  make up-gpu               # With NVIDIA GPU acceleration

  # Utilities
  make logs                  # Follow logs
  make down                  # Stop services
  make clean                 # Stop + remove volumes (DATA LOSS!)
  make backup                # Export database
  make restore               # Import database

  # Testing
  make test-e2e              # Playwright E2E tests


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ENVIRONMENT VARIABLES                               │
└─────────────────────────────────────────────────────────────────────────────────┘

  # Required for production
  NEXUS_PASSWORD             # Login password (default: nexus-local-rag)
  NEXUS_API_KEY              # Backend API key

  # Optional
  NEXUS_ALLOW_ORIGINS        # CORS origins (default: ["http://localhost:3000"])
  OLLAMA_IMAGE               # Ollama image (prod: pinned digest)
  PGVECTOR_IMAGE             # pgvector image (prod: pinned digest)

  # Docker Secrets (recommended for production)
  API_KEY_FILE=/run/secrets/api_key   # Mounted secret for API key

  # Directory mounts
  NEXUS_MOUNT_DOCUMENTS       # Additional corpus directories
  NEXUS_MOUNT_DOWNLOADS
  NEXUS_MOUNT_PROJECTS

  # Frontend
  NEXT_PUBLIC_API_BASE       # Backend URL (default: http://localhost:8000)

```

## Prerequisites
- Docker + Docker Compose
- macOS/Linux with OCRmyPDF available if running backend locally (Docker image bundles dependencies)

## Quickstart (10 minutes)
```bash
make up               # start db, ollama, api, web
make pull-models      # download embedding + chat models into ollama volume
make ingest-test      # ingest test corpus
open http://localhost:3003  # chat with citations
```

If Docker misbehaves locally: `make doctor` checks daemon and compose availability.

### Collections
- `library`, `dev`, `test` defined in `corpora.yml`
- Corpus directories mounted read-only at `/corpora/{collection}`

### Core Workflows
1. **Ingest**: `make ingest-test` (or dev/library). Incremental: skips unchanged files by sha256 + mtime. Runs OCR selectively when extraction quality is low. Supports hooks for pre/post-processing.
2. **Chat**: UI at `/chat` streams responses and shows citations (file, page, excerpt, score). Select Ollama models and adjust temperature, top_p, and max_tokens via Advanced controls.
3. **Library**: `/library` lists documents, tags, extraction quality, OCR flag. Actions include delete and re-ingest.
4. **Eval**: `/eval` runs `inspect_ai` suite against test collection; latest report is shown in UI. CLI: `make eval`.

### Services
- `db`: Postgres 16 with pgvector + HNSW enabled.
- `ollama`: local models `mxbai-embed-large` (embeddings) and `llama3.1:8b-instruct` (chat).
- `api`: FastAPI backend (`backend/`).
- `web`: Next.js App Router frontend (`web/`).

### Configuration
- `backend/src/nexus/config.py` for thresholds, model names, chunking, paths.
- `corpora.yml` for corpus roots, include/exclude globs, tags.
- `hooks/` directory for pre/post-processing scripts. See `docs/HOOKS.md` for details.
- `.env` for additional directory mounts. See `docs/SANDBOX.md` for configuration.

### GPU Support
NVIDIA GPU acceleration available via:
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up
```

Requires nvidia-container-toolkit on host.

### Authentication
NextAuth.js credentials-based authentication protects all routes:
- Default password: `nexus-local-rag` (set `NEXUS_PASSWORD` to customize)
- JWT sessions with 24-hour expiry
- All pages require login except `/login` and `/api/auth/*`

### Developer Notes
- `ruff`, `pytest`, and `uv` manage Python tooling (`backend/`).
- Playwright smoke tests in `web/` (see `package.json` scripts).
- Processed OCR output stored under `/processed/{collection}` to preserve source PDFs.
- Embedding dimension contract enforced per collection version; ingestion aborts on mismatch.

### One-command clean up
```bash
make down
```
