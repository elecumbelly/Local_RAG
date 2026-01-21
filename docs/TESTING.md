# Testing Strategy

## Overview

Nexus RAG uses a multi-layered testing approach to ensure reliability across the full stack:
- Unit tests for individual components
- Integration tests for service interactions
- E2E tests for user-facing workflows
- Security tests for vulnerability detection
- Performance tests for scalability

## Test Organization

```
backend/tests/
├── test_models_api.py           # Ollama model listing endpoint
├── test_chat_parameters.py      # Temperature, top_p, max_tokens handling
├── test_providers.py             # All chat provider integrations
├── test_hooks.py                # Pre/post-ingest hook execution
├── test_hooks_executor.py        # Hook parsing and error handling
├── test_ingest_integration.py    # Full ingestion pipeline
├── test_security.py              # SQL injection, XSS, path traversal
├── test_performance.py           # Throughput and latency benchmarks
├── test_*.py                     # Other existing tests
```

```
web/tests/
├── chat.spec.ts                 # Basic chat functionality (existing)
├── model-selector.spec.ts       # Model selector UI
├── advanced-controls.spec.ts     # Temperature, top_p, max_tokens UI
```

## Running Tests

### Backend Tests

```bash
# Run all backend tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/test_models_api.py -v

# Run with coverage
pytest tests/ --cov=nexus --cov-report=html
```

### E2E Tests

```bash
# Run all E2E tests
cd web
npm run test:e2e

# Run specific test file
npx playwright test model-selector.spec.ts

# Run with UI
npx playwright test --ui
```

## Coverage Goals

### Target Coverage

| Component | Target | Priority |
|-----------|--------|----------|
| API Endpoints | 80% | High |
| Chat Providers | 85% | High |
| Hook System | 75% | Medium |
| Ingestion Pipeline | 80% | High |
| Security | 70% | Medium |
| Performance | 60% | Low |

### Coverage Measurement

Backend:
```bash
pytest --cov=nexus --cov-report=term --cov-report=html
```

View report at: `backend/htmlcov/index.html`

## Test Categories

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies (Ollama, database)
- Focus on edge cases and error handling
- Fast execution (< 100ms per test)

### Integration Tests
- Test service interactions
- Use real database fixtures
- Test hook execution flow
- Test parameter passing through layers

### E2E Tests
- Test complete user workflows
- Test UI interactions and state
- Test cross-browser compatibility (Chromium, Firefox)
- Test mobile responsive design
- Test accessibility

### Security Tests
- SQL injection: Validate input sanitization
- XSS: Verify output encoding
- Path traversal: Validate file access restrictions
- Authentication: Test API key validation
- Rate limiting: Verify headers are present

### Performance Tests

- **Embedding Throughput**: Target > 10 docs/sec
- **Search Latency**: Target < 100ms for 8 chunks
- **Concurrent Search**: 10 parallel requests < 10s total
- **Memory Efficiency**: < 500MB increase per ingestion

## CI/CD Integration

Tests run automatically on pull requests via GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.lock
      - run: pytest tests/ --cov=nexus

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install
      - run: npm run test:e2e
```

## Test Data Management

- Test fixtures in `backend/tests/fixtures/` directory
- Sample PDFs in `backend/tests/samples/` directory
- Mock Ollama responses for predictable testing
- Database in-memory SQLite for isolated tests

## Debugging Failed Tests

1. Run specific test file: `pytest tests/test_failing.py -v`
2. Add temporary print statements to see state
3. Use `--pdb` flag to drop into debugger on failure
4. Check logs: `docker-compose logs api` for runtime errors

## Test Maintenance

- Update tests when adding new features
- Remove outdated tests
- Refactor duplicate test logic
- Keep test descriptions clear and actionable
- Run full test suite before major releases

## Future Improvements

- Add load testing for capacity planning
- Add contract testing for API versioning
- Add chaos engineering tests for resilience
- Add mutation testing for security
- Add accessibility testing with axe-core

---

**Testing and Quality Gates**

- **Backend**: `cd backend && uv run ruff check . && uv run pytest`
- **Frontend**: `cd web && npm run lint && npm run build && npm run test:e2e`
- **Playwright on macOS**: If local browsers fail with Crashpad permissions, run `make test-e2e` (Docker-based) instead.
- **CI**: See `.github/workflows/ci.yml` for current pipeline (backend lint/tests; frontend lint/build).
- **Integration ideas**: add ingest/retrieval/chat flow tests with mocked providers; validate file-serving guard rejects paths outside corpora/processed.
- **Security scanning** (add in follow-up): pip-audit, npm audit, trivy (containers), semgrep/bandit (SAST), pip-audit (backend), npm audit (frontend).
- **Dependency locks**: backend installs from `backend/requirements.lock`; regenerate via `uv pip compile pyproject.toml -o requirements.lock` when dependencies change.
- **CI scans**: semgrep SBOM, trivy filesystem + image scans, mypy, semgrep (p/default), bandit (backend), pip-audit (backend), npm audit (frontend).
- **Static-analysis ratchet**: mypy runs only on changed Python files vs `origin/main` (configurable via `MYPY_BASELINE_REF`). Semgrep uses `SEMGREP_BASELINE_REF` for PRs when available.
