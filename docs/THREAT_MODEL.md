# Threat Model

## Assets
- Corpus PDFs (and processed OCR outputs)
- Chunk embeddings in pgvector
- Chat queries and responses
- API keys and authentication credentials
- Session tokens (JWT cookies)

## Trust Boundaries
- **Frontend**: Browser exposes UI; all routes protected by NextAuth.js middleware
- **API**: Exposed over HTTP (protected by API key + rate limiting)
- **Database**: Behind API; not directly accessible from outside
- **Ollama**: Local network access; no authentication
- **File Storage**: Corpus roots and `/processed` directories

## Key Risks and Mitigations

| Risk | Mitigation | Status |
|------|------------|--------|
| Unauthenticated API access | API key required on all routes (`x-api-key` header) | ✅ Implemented |
| Frontend unauthorized access | NextAuth.js with JWT sessions; middleware redirects to `/login` | ✅ Implemented |
| CORS abuse | `NEXUS_ALLOW_ORIGINS` configurable allowlist | ✅ Implemented |
| Path traversal / LFI | Path resolution + root checks before file serving | ✅ Implemented |
| Brute force attacks | Rate limiting (100/hour global, 10/min chat) | ✅ Implemented |
| Supply-chain attacks | Image pinning (SHA256 digests), dependency lockfiles | ✅ Implemented |
| Credential leakage | Docker secrets support, `API_KEY_FILE` variable | ✅ Implemented |
| Container escape | Non-root users in all containers | ✅ Implemented |
| Large file DoS | 100MB file size limit during ingestion | ✅ Implemented |
| Response exhaustion | 4096 token limit on LLM responses | ✅ Implemented |
| Prompt injection | Content sanitization, length limits, system prompt hardening | ✅ Implemented |
| Credential brute force | Password complexity warnings, rate limiting | ✅ Implemented |
| XSS attacks | Security headers (X-Frame-Options, X-Content-Type-Options) | ✅ Implemented |
| SQL injection | Parameterized queries via psycopg | ✅ Implemented |

## Implemented Security Controls

### Authentication
- NextAuth.js credentials provider with password authentication
- JWT session cookies (24-hour expiry)
- API key authentication for all backend routes
- Session validation middleware

### Authorization
- Route-level protection via Next.js middleware
- API key validation on all endpoints

### Rate Limiting
- SlowAPI-based rate limiting
- 100 requests/hour global per IP
- 10 requests/minute for chat endpoints

### Input Validation
- Query parameter length limits (500 chars)
- Collection name validation (100 chars)
- Tag validation (100 chars)
- File size limits (100MB max)
- Content sanitization for LLM prompts

### Output Encoding
- Security headers on all responses
- Proper Content-Type handling
- No raw user input in responses

### Secret Management
- Docker secrets support (`API_KEY_FILE`)
- Environment variable fallback
- Secrets never logged or exposed

### Container Hardening
- Non-root users (appuser/nextjs)
- Minimal base images (python:3.12-slim, node:20-alpine)
- No unnecessary packages installed
- Read-only where possible

## Future Security Enhancements (Roadmap)
- TLS termination at reverse proxy
- OAuth providers (Google, GitHub) via NextAuth.js
- Role-based access control (RBAC)
- Audit logging
- Database encryption at rest
- Network segmentation
- Container image signing
- SBOM generation and scanning
- Dependency vulnerability scanning (trivy, pip-audit, npm audit)
