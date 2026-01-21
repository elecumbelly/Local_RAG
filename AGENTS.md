## Gemini CLI Agent - Project Hardening & Polish
- **Forensic Audit**: Conducted end-to-end analysis of security, build systems, and documentation gaps.
- **Security Hardening**:
    - Established CI pipeline (`.github/workflows/ci.yml`) with automated security scanning (Trivy, Semgrep, Bandit).
    - Hardened production deployment via `docker-compose.prod.yml` (secrets validation, image pinning).
    - Implemented static-analysis "ratchet" for `mypy` and `ruff` to prevent technical debt.
- **UI/UX Refinement**:
    - Migrated to `sonner` for robust toast notifications and ingestion feedback.
    - Added skeleton loaders and "Thinking..." state transitions to the RAG UI.
    - Secured PDF document serving and enabled citation deep-linking.
- **Documentation**: Standardized project governance with `LICENSE`, `ARCHITECTURE.md`, and `SECURITY.md`.

---

## OpenAI Codex - Code Review & Critical Fixes (2025-01-21)

### Critical/High Priority Fixes
- [x] **BaseModel Import Fix**: Added missing `BaseModel` import in `backend/src/nexus/config.py` (would cause crash on startup)
- [x] **Rate Limiting Fix**: Fixed `rate_limit_handler` to use `JSONResponse` instead of non-existent `request.state.response`
- [x] **API Key Forwarding**: Wired `x-api-key` header to all 10+ Next.js API routes via new `server-api.ts` utility
- [x] **Client-Side Key Removal**: Removed `NEXT_PUBLIC_API_KEY` exposure from `DocumentTable.tsx` and `CitationList.tsx`
- [x] **Auth Endpoint Protection**: Added `Depends(deps.require_api_key)` to `/models/ollama` route
- [x] **Frontend Endpoint Fix**: Changed `apiBase` to `/api/proxy` for server-side key injection

### Medium Priority Fixes
- [x] **Config Wiring**: Connected `NEXUS_MAX_FILE_SIZE_MB` to `discover.py` instead of hardcoded 100MB
- [x] **Empty Collections Guard**: Added early return in `pgvector.py` and validation in `routes_chat.py` to prevent SQL errors
- [x] **Mount Validation**: Wired `MountValidator` at ingest startup in `pipeline.py`

### Documentation Fixes
- [x] Removed unsupported `NEXUS_PASSWORD_FILE` from docs/configuration.md
- [x] Restricted to PDF-only ingestion in docs (removed `.md` claims)
- [x] Fixed SANDBOX.md to match actual implementation (no `NEXUS_MOUNT_*` vars)

### Test Coverage
- [x] Added API key requirement test in `tests/test_models_api.py`
- [x] Created `tests/test_empty_collections.py` with 4 regression tests
- [x] Created comprehensive `tests/test_regression.py` (480+ lines, 27 tests across 8 categories)

---

## TODO
- [x] ~~Investigate and fix the Docker daemon socket permissions so `make test-e2e` (Playwright suite) can run locally~~ - **Fixed by Claude Code (2024-12-30)**:
  - Docker socket was already working; actual issue was path with spaces in Makefile volume mount
  - Fixed `Makefile` to quote the volume path: `-v "$(PWD)/web:/work"`
  - Added missing `"use client"` directives to `ChatPanel.tsx` and `DocumentTable.tsx`
  - Added missing `eventsource-parser` dependency to `package.json`
  - Fixed Playwright config: added `baseURL` and `webServer` configuration
  - Fixed test assertions to properly fill input before clicking disabled button
  - All 3 e2e tests now pass
