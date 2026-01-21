# Configuration

## Environment Variables

### Core API Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXUS_API_KEY` | No | None | API key for backend routes (prefer `API_KEY_FILE` in production) |
| `NEXUS_API_KEY_FILE` | No | None | Path to file containing API key (Docker secret) |
| `NEXUS_DATABASE_URL` | Yes | `postgresql://nexus:nexus@localhost:5432/nexus` | PostgreSQL connection string |
| `NEXUS_OLLAMA_URL` | Yes | `http://localhost:11434` | Ollama API base URL |
| `NEXUS_ALLOW_ORIGINS` | No | `["http://localhost:3000"]` | JSON array of CORS-allowed origins |
| `NEXUS_CORPORA_MANIFEST` | No | `corpora.yml` | Path to corpus configuration file |
| `NEXUS_PROCESSED_DIR` | No | `/processed` | Directory for OCR output |

### Authentication
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXUS_PASSWORD` | No | `nexus-local-rag` | Password for NextAuth.js login page |

### LLM Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXUS_EMBED_MODEL` | No | `mxbai-embed-large` | Ollama embedding model |
| `NEXUS_CHAT_MODEL` | No | `llama3.1:8b-instruct` | Ollama chat model |
| `NEXUS_EMBED_DIM` | No | `1024` | Embedding dimension |
| `NEXUS_CHUNK_SIZE` | No | `800` | Text chunk size in characters |
| `NEXUS_CHUNK_OVERLAP` | No | `80` | Chunk overlap in characters |
| `NEXUS_MAX_FILE_SIZE_MB` | No | `100` | Maximum PDF file size |
| `NEXUS_TIMEOUT_SECONDS` | No | `120` | HTTP request timeout |
| `NEXUS_MAX_RESPONSE_TOKENS` | No | `4096` | Max LLM response tokens |

### Cloud AI Providers
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXUS_OPENAI_API_KEY` | No | None | OpenAI API key |
| `NEXUS_OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `NEXUS_ANTHROPIC_API_KEY` | No | None | Anthropic API key |
| `NEXUS_GOOGLE_AI_API_KEY` | No | None | Google AI API key |

### Frontend Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | Yes | `http://localhost:8000` | Backend URL for Next.js proxy |
| `API_KEY` | No | None | Server-side API key for proxy (preferred over `NEXT_PUBLIC_API_KEY`) |
| `API_KEY_FILE` | No | None | Path to API key file for Next.js proxy |

## Docker Secrets

For production, use Docker secrets instead of environment variables:

```bash
# Create secrets directory
mkdir -p secrets

# Create API key file
echo "your-secure-api-key" > secrets/api_key

# Create password file (optional)
echo "your-secure-password" > secrets/password
```

Then reference in docker-compose:
```yaml
services:
  api:
    secrets:
      - api_key
    environment:
      NEXUS_API_KEY_FILE: /run/secrets/api_key
```

## corpora.yml Schema

```yaml
collections:
  library:
    roots: ["/corpora/library"]
    include: ["**/*.pdf"]
    exclude: ["**/tmp/**", "**/drafts/**"]
    tags: ["library", "important"]
    hooks:
      pre_ingest: "hooks/pre-ingest-library.sh"
      post_ingest: "hooks/post-ingest-library.sh"
  
  dev:
    roots: ["/corpora/dev", "/projects/docs"]
    include: ["**/*.pdf"]
    exclude: []
    tags: ["development"]
  
  test:
    roots: ["/corpora/test"]
    include: ["**/*.pdf"]
    exclude: []
    tags: ["testing"]
```

### Collection Schema
| Field | Type | Description |
|-------|------|-------------|
| `roots` | List[str] | Absolute paths to root directories (read-only mounts) |
| `include` | List[str] | Glob patterns to include (PDFs only: `**/*.pdf`) |
| `exclude` | List[str] | Glob patterns to exclude |
| `tags` | List[str] | Default tags for all documents |
| `hooks` | Dict | Hook scripts for pre/post processing |

## Rate Limiting

All API endpoints are rate-limited using SlowAPI:
- **Global**: 100 requests per hour per IP
- **Chat endpoints**: 10 requests per minute per IP
- **Exceeded**: Returns HTTP 429 with `{"detail": "Rate limit exceeded"}`

## Storage

| Path | Purpose | Persistence |
|------|---------|-------------|
| `/corpora/{collection}` | Source PDFs (read-only) | External mount |
| `/processed/{collection}` | OCR output PDFs | Docker volume |
| `/data` | Database storage | Docker volume |
| `/root/.ollama` | Ollama models | Docker volume |
