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

## TODO
- [x] ~~Investigate and fix the Docker daemon socket permissions so `make test-e2e` (Playwright suite) can run locally~~ - **Fixed by Claude Code (2024-12-30)**:
  - Docker socket was already working; actual issue was path with spaces in Makefile volume mount
  - Fixed `Makefile` to quote the volume path: `-v "$(PWD)/web:/work"`
  - Added missing `"use client"` directives to `ChatPanel.tsx` and `DocumentTable.tsx`
  - Added missing `eventsource-parser` dependency to `package.json`
  - Fixed Playwright config: added `baseURL` and `webServer` configuration
  - Fixed test assertions to properly fill input before clicking disabled button
  - All 3 e2e tests now pass
