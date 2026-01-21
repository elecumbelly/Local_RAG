# Runbook

## Health Checks

### API Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### Database Readiness
```bash
docker compose exec db pg_isready -U nexus
# Expected: /var/run/postgresql:5432 - accepting connections
```

### Ollama Status
```bash
curl http://localhost:11434/api/tags
# Expected: JSON response with installed models
```

### Web Status
```bash
curl http://localhost:3003
# Expected: Next.js HTML response
```

## Authentication

### First Login
1. Visit http://localhost:3003 (or your deployment URL)
2. You'll be redirected to `/login`
3. Enter the password (default: `nexus-local-rag`)
4. Click "Sign in" to access the application

### Changing Password
Set `NEXUS_PASSWORD` environment variable:
```bash
# In .env
NEXUS_PASSWORD=your-secure-password

# Or in docker-compose.yml
environment:
  NEXUS_PASSWORD: your-secure-password
```

### API Key Authentication
All API routes require `x-api-key` header:
```bash
curl -H "x-api-key: your-api-key" http://localhost:8000/health
```

The frontend proxy handles this automatically using the server-side `API_KEY` or `API_KEY_FILE`.

## Rate Limiting

| Endpoint | Limit | Response |
|----------|-------|----------|
| All API routes | 100 requests/hour/IP | HTTP 429 |
| Chat endpoints | 10 requests/minute/IP | HTTP 429 |

If you hit rate limits:
- Wait for the limit to reset
- Use different IP address for testing
- Contact administrator for adjustments

## Common Issues

### 401 Unauthorized Responses
- Ensure `NEXUS_API_KEY` is set in API container
- Ensure `API_KEY` or `API_KEY_FILE` is set for frontend proxy
- Include `x-api-key` header on direct API calls

### CORS Errors
- Set `NEXUS_ALLOW_ORIGINS` to your frontend origin
- Example: `NEXUS_ALLOW_ORIGINS='["http://localhost:3003"]'`

### Login Page Redirect Loop
- Clear browser cookies
- Ensure `NEXUS_PASSWORD` is set in web container
- Check browser console for errors

### Ingest Fails
- Verify corpus mount paths exist
- Ensure OCR dependencies available (ocrmypdf, tesseract)
- Check API logs: `docker compose logs api`
- Verify file size < 100MB (configurable via `NEXUS_MAX_FILE_SIZE_MB`)

### Chat Returns Empty Response
- Ensure embeddings exist (run ingestion first)
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check collections are selected in UI
- Verify model is available: `llama3.1:8b-instruct`

### Slow Responses
- Check rate limiting headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- Monitor resource usage: `make stats`
- Check Ollama memory: `docker compose exec ollama ps`

## Backup and Restore

### Database Backup
```bash
# Backup to file with timestamp
make backup
# Creates: backup_YYYYMMDD_HHMMSS.sql

# Manual backup
docker compose exec db pg_dump -U nexus -d nexus > backup.sql
```

### Database Restore
```bash
# Restore from backup file
make restore < backup.sql

# Manual restore
docker compose exec -T db psql -U nexus -d nexus < backup.sql
```

### Processed Files
```bash
# Backup OCR output volume
docker compose exec api tar czf - /processed | tar xzf - -C /path/to/backup
```

### Corpus Files
Source PDFs are read-only mounts - back up at their source location.

## Logs and Troubleshooting

### API Logs
```bash
# Follow logs
make logs

# Last 100 lines
docker compose logs api --tail 100
```

### Web Logs
```bash
docker compose logs web --tail 100
```

### Database Logs
```bash
docker compose logs db --tail 100
```

### Ollama Logs
```bash
docker compose logs ollama --tail 100
```

### Ingestion Errors
- OCR errors return HTTP 400 with error details
- Chunking failures logged server-side
- Embedding failures cause request retries

## Docker Compose Commands

### Development
```bash
make up              # Start all services with hot reload
make down            # Stop all services
make logs            # Follow all logs
make ps              # List running containers
make stats           # Show container resource usage
```

### Production
```bash
make up-prod         # Start production stack
make down-prod       # Stop production stack
make logs-prod       # Follow production logs
make deploy          # Deploy + show endpoints
```

### Utilities
```bash
make clean           # Stop + remove volumes (DATA LOSS!)
make stop            # Stop without removing volumes
make doctor          # Check Docker availability
```

### Model Management
```bash
make pull-models     # Download mxbai-embed-large + llama3.1:8b-instruct
```

### Ingestion
```bash
make ingest-test     # Ingest test collection
make ingest-dev      # Ingest dev collection
make ingest-library # Ingest library collection
```

### Evaluation
```bash
make eval            # Run inspect_ai evaluation suite
```

## Environment Setup

### Development .env Example
```bash
NEXUS_API_KEY=dev-local-key
NEXUS_DATABASE_URL=postgresql://nexus:nexus@localhost:5432/nexus
NEXUS_OLLAMA_URL=http://localhost:11434
NEXUS_ALLOW_ORIGINS='["http://localhost:3003"]'
NEXUS_PASSWORD=nexus-local-rag
NEXT_PUBLIC_API_BASE=http://localhost:8000
API_KEY=dev-local-key
```

### Production Environment
```bash
# Use Docker secrets for sensitive values
API_KEY_FILE=/run/secrets/api_key
NEXUS_PASSWORD_FILE=/run/secrets/password

# Pin image versions
PGVECTOR_IMAGE=ankane/pgvector@sha256:...
OLLAMA_IMAGE=ollama/ollama@sha256:...
```

## Performance Tuning

### Resource Limits
Edit `docker-compose.yml`:
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 8G
        cpus: '4'
```

### GPU Support
```bash
make up-gpu  # With NVIDIA GPU acceleration
```

### Ollama Memory
Reduce if needed:
```bash
docker compose exec ollama ollama stop
docker compose exec ollama rm -rf /root/.ollama
```
