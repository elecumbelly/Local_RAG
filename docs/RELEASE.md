# Build and Release Notes

## Build Types

### Development Build
```bash
make up
```
- Uses `docker-compose.yml`
- API: `backend/Dockerfile` (dev mode)
- Web: `web/Dockerfile` (next dev with hot reload)
- No image pinning

### Production Build
```bash
make deploy
# or
make up-prod
```
- Uses `docker-compose.yml` + `docker-compose.prod.yml`
- API: `backend/Dockerfile.prod` (multi-stage, non-root)
- Web: `web/Dockerfile.prod` (multi-stage build)
- Image pinning via `PGVECTOR_IMAGE` and `OLLAMA_IMAGE`

## Production Images

### Backend (backend/Dockerfile.prod)
Multi-stage build for minimal image:
1. **Builder stage**: Python virtual environment with dependencies
2. **Production stage**: Slim image with runtime deps only
3. **Non-root user**: Runs as `appuser`
4. **Size**: ~400MB (vs ~1GB dev image)

### Frontend (web/Dockerfile.prod)
Multi-stage build:
1. **Build stage**: npm install, next build
2. **Production stage**: minimal Node Alpine with standalone output
3. **Non-root user**: Runs as `nextjs`
4. **Size**: ~150MB (vs ~500MB dev image)

### Image Pinning
```bash
# Set before deployment
export PGVECTOR_IMAGE=ankane/pgvector@sha256:ad2a8a1572e4f9d5c6a8d814971eabddff796265b5a43f63efa9be1cf6cbb2c6
export OLLAMA_IMAGE=ollama/ollama@sha256:0c4c4fdf49a046aa5111ef1f61c2167e4fbba27de6d7da6f61be993ec7aee1c4
```

## Dependency Management

### Backend
```bash
# Update lockfile
cd backend
uv pip compile pyproject.toml -o requirements.lock
```

### Frontend
```bash
# Install from lockfile
cd web
npm ci
```

## Versioning

1. Tag releases: `git tag v0.1.0`
2. Build images with tags: `nexus-api:v0.1.0`, `nexus-web:v0.1.0`
3. Push to registry
4. Update `docker-compose.prod.yml` with new tags

## Deployment Checklist

- [ ] Set `NEXUS_PASSWORD` to secure value
- [ ] Set `API_KEY_FILE` to Docker secret path
- [ ] Pin image versions (SHA256 digests)
- [ ] Configure `NEXUS_ALLOW_ORIGINS`
- [ ] Set up TLS termination (reverse proxy)
- [ ] Configure backup strategy
- [ ] Test in staging environment
- [ ] Run E2E tests: `make test-e2e`

## Docker Secrets

Create secrets directory:
```bash
mkdir -p secrets
echo "secure-api-key" > secrets/api_key
echo "secure-password" > secrets/password
```

Reference in compose:
```yaml
secrets:
  api_key:
    file: ./secrets/api_key
  password:
    file: ./secrets/password

services:
  api:
    secrets:
      - api_key
    environment:
      NEXUS_API_KEY_FILE: /run/secrets/api_key
      NEXUS_PASSWORD_FILE: /run/secrets/password
```

## Environment Configuration

### Required
- `NEXUS_API_KEY` or `NEXUS_API_KEY_FILE`
- `NEXUS_DATABASE_URL`
- `NEXUS_OLLAMA_URL`
- `NEXUS_PASSWORD`

### Recommended
- `NEXUS_ALLOW_ORIGINS` - Frontend origins
- `PGVECTOR_IMAGE` - Pinned digest
- `OLLAMA_IMAGE` - Pinned digest

### Optional
- Cloud AI provider keys (`NEXUS_OPENAI_API_KEY`, etc.)
- Custom collection configurations
