# Security and Deployment Assumptions

## Authentication

### Frontend Authentication (NextAuth.js)
- Login page at `/login` with password-based authentication
- Session managed via JWT cookies (24-hour expiry)
- All frontend routes protected by middleware redirect to `/login`
- Password configured via `NEXUS_PASSWORD` environment variable (default: `nexus-local-rag`)

### Backend Authentication (API Key)
- All API routes require `x-api-key` header
- API key loaded from `NEXUS_API_KEY` env var or `NEXUS_API_KEY_FILE` (Docker secret)
- Frontend proxy injects API key server-side; client never sees it

## Rate Limiting
- **Global**: 100 requests per hour per IP address
- **Chat endpoints**: 10 requests per minute per IP address
- **Response**: HTTP 429 with `{"detail": "Rate limit exceeded"}`
- Implemented via SlowAPI

## CORS
- Lock `NEXUS_ALLOW_ORIGINS` to trusted origins (default: `["http://localhost:3000"]`)
- All origins validated before request processing

## Document File Serving
- Only files under configured corpus roots and `/processed` are served
- Path traversal attempts rejected with HTTP 400
- Resolved paths checked against allowlist before serving

## Secrets Management
- Provide API keys via environment variables or Docker secrets
- Never commit secrets to version control
- Use `API_KEY_FILE` for production (mount secrets at `/run/secrets/`)
- Rotate keys regularly

## Container Security
- **Non-root users**: All containers run as non-root (`appuser` for API, `nextjs` for web)
- **Image pinning**: Production uses SHA256-pinned images via `PGVECTOR_IMAGE` and `OLLAMA_IMAGE`
- **Dependency lockfiles**: `uv pip compile` for backend, `npm ci` for frontend
- **No root in containers**: Users added in Dockerfiles, containers run with minimal privileges

## Network Exposure
- Development: services bound to localhost
- Production: use reverse proxy with TLS termination
- Ollama accessible on local network by default; restrict in production

## Security Headers (Frontend)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-DNS-Prefetch-Control: off`

## Prompt Injection Protection
- User queries and document chunks sanitized before LLM prompts
- Length limits enforced (query: 1000 chars, content: 5000 chars)
- LLM system prompt includes security instructions

## File Size Limits
- Maximum PDF file size: 100MB (configurable via `NEXUS_MAX_FILE_SIZE_MB`)
- Files exceeding limit skipped during ingestion

## Response Size Limits
- Maximum LLM response tokens: 4096 (configurable via `NEXUS_MAX_RESPONSE_TOKENS`)
- Prevents resource exhaustion from excessive responses
