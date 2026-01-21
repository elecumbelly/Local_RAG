# Local RAG - TODO

## Session 2024-12-30 Progress

### Fixed
- [x] Docker path with spaces issue in Makefile
- [x] Missing "use client" directives in React components
- [x] psycopg async context manager pattern across all files
- [x] Pydantic ChatRequest model (was using Dict instead of BaseModel)
- [x] Ollama API endpoint `/api/embed` (was `/api/embeddings`)
- [x] **Infinite loop bug in chunking.py** - When remaining text ≤ overlap, loop never terminates, causing OOM

### Partially Fixed
- [ ] Ollama context length errors - Added truncation fallback for chunks that exceed token limit

## Next Session TODO

### High Priority
1. **Debug remaining ingest OOM** - Ingest still gets killed (exit 137) after ~30-50 seconds
   - Chunking now works (1261 chunks from 380 pages)
   - Individual embeddings work fine
   - Suspect: Either memory accumulation during batch processing, or container limits
   - Try: Batch embeddings, add progress logging, increase container memory

2. **Wire up chunking settings to API** - UI has controls but they're not sent to backend
   - `IngestControls.tsx` has state for chunkSize, chunkOverlap, minChars, maxEmptyRatio
   - Need to pass these to `/ingest/{collection}` endpoint

### Medium Priority
3. **Add inbox folder as collection source** - User mentioned PDFs in `inbox/` folder

4. **E2E tests pass** - All 3 Playwright tests working

### Files Modified This Session
- `backend/src/nexus/ingest/chunking.py` - Fixed infinite loop
- `backend/src/nexus/embed/ollama_embed.py` - Fixed endpoint, added truncation fallback
- `backend/src/nexus/ingest/pipeline.py` - Added debug logging
- `backend/src/nexus/db.py` - Fixed async context manager
- `backend/src/nexus/api/routes_chat.py` - Fixed ChatRequest model
- `docker-compose.yml` - Added source mount, memory limit, debug logging
- `web/components/IngestControls.tsx` - Added chunking settings UI with help tooltips

### Test Commands
```bash
# Test chunking (should complete quickly now)
docker compose run --rm api python -c "
from nexus.ingest import pdf_extract_pypdf, chunking
pages = pdf_extract_pypdf.extract_text('/corpora/test/Quality Control for DUMmIES.pdf')
total = sum(len(chunking.chunk_text(p.text, p.page)) for p in pages)
print(f'Total chunks: {total}')
"

# Test single embedding
curl -s -X POST http://localhost:11434/api/embed \
  -d '{"model":"mxbai-embed-large","input":"test"}' \
  -H "Content-Type: application/json" | jq '.embeddings | length'

# Full ingest (currently fails with OOM)
docker compose run --rm api python -c "
import asyncio
from nexus.ingest.pipeline import ingest_collection
asyncio.run(ingest_collection('test'))
"
```
