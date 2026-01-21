# Local RAG - Claude Code Configuration

## Context Management
Use Explore agents for multi-file searches. Read directly for known single files.

## Skills: .claude/skills/
Read SKILL.md before using each skill.

### Available Skills:
- `open-source-cohort` - Multi-agent research on open-source alternatives, library comparisons, and architectural patterns for the Local RAG project. Use when researching RAG stacks, vector databases, PDF extraction, embeddings, or frontend patterns.

## Project Context

This is a local, offline RAG (Retrieval Augmented Generation) stack with:
- **Backend**: FastAPI with async Python (psycopg, httpx)
- **Database**: PostgreSQL 15 + pgvector for vector search
- **LLM**: Ollama (local models: mxbai-embed-large, llama3.1:8b-instruct)
- **Frontend**: Next.js App Router with streaming chat UI
- **PDF Processing**: pypdf extraction + OCRmyPDF for scanned docs
- **Chunking**: Fixed-size with overlap, configurable via settings

### Key Directories
- `backend/src/nexus/` - Core application code
- `web/` - Next.js frontend
- `corpora/` - Document collections (library, dev, test)
- `docs/` - Architecture and operational documentation

### Configuration Files
- `backend/src/nexus/config.py` - Settings (chunk_size, embed_dim, etc.)
- `corpora.yml` - Collection definitions
- `docker-compose.yml` - Service orchestration

## MCP Servers
See `~/.claude/settings.json` for global MCP configuration.
