---
name: open-source-cohort
description: Invoke a multi-agent cohort to research, analyze, and compare open-source alternatives and patterns for the Local RAG codebase. Use when the user wants multiple AI perspectives on architectural decisions, library choices, or implementation patterns.
---

This skill invokes The Cohort to research open-source solutions, analyze competitive/alternative implementations, and provide multi-perspective recommendations for the Local RAG project.

## Architecture

**Two-tier early return**: Priority agents (Claude, Gemini, Codex) return immediately after consensus. Background agents continue in parallel and update session files incrementally.

## When to Use

Use this skill when the user:
- Wants to research open-source alternatives to current implementations
- Needs comparison of libraries/frameworks used in the codebase
- Asks for "what are other RAG stacks doing", "how do other projects handle X"
- Wants multi-agent research on a technical decision
- Needs to understand how similar problems are solved in other repos

## Research Focus Areas for Local RAG

### Common Research Questions
- **Vector databases**: pgvector vs FAISS vs Chroma vs Qdrant tradeoffs
- **PDF extraction**: pypdf vs pdfplumber vs PyMuPDF vs unstructured
- **OCR**: OCRmyPDF vs Tesseract vs cloud alternatives
- **Embeddings**: Ollama vs HuggingFace vs OpenAI API vs cloud embeddings
- **Chunking strategies**: semantic vs fixed-size vs document-structure-aware
- **Chat interfaces**: streaming patterns, citation implementations
- **Frontend stacks**: Next.js vs alternatives, UI component libraries
- **Backend patterns**: FastAPI vs Flask vs other Python frameworks

## Commands

The Cohort CLI is available at `~/.cohort` or via the project at `/Users/sspence/coding_projects/Learnin/The_Cohort`.

### Quick Commands

```bash
# Research open-source alternatives for a component
cohort decide "Should we use FAISS or pgvector for local embeddings?"

# Research library alternatives
cohort ask "What's the best Python PDF extraction library in 2024?"

# Compare implementation patterns
cohort debate "Should chunking be done at extraction time or query time?"

# Research specific implementation details
cohort decide "How do other RAG projects implement citations?"
```

### Command Reference

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `cohort decide "question"` | Seek consensus | `--rounds N`, `--pg` |
| `cohort debate "topic"` | Structured debate | `--monitor` |
| `cohort ask "question"` | Quick question | `--pg` |
| `cohort multi "question"` | N parallel cohorts | `-n 3`, `-v` |

## Implementation Pattern

When the user requests open-source research, use Task agents to avoid context bloat:

### Research + Analysis (Single Cohort)

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    Working directory: /Users/sspence/coding_projects/Learnin/The_Cohort

    Run this cohort research on the Local RAG codebase context:
    Current project: /Users/sspence/Library/CloudStorage/OneDrive-Personal/Hobbyist Development/Local_RAG
    
    Research question: "USER'S RESEARCH QUESTION HERE"
    
    Steps:
    1. Read the project's architecture docs (README.md, docs/ARCHITECTURE.md)
    2. Understand the current implementation in backend/src/nexus/
    3. Run cohort research:
       .venv/bin/cohort decide "RESEARCH QUESTION" --rounds 3 --pg
    
    Capture and return:
    - Final status (UNANIMOUS/STRONG_MAJORITY/WEAK_MAJORITY/SPLIT)
    - Agreement percentage
    - Session ID (ses_xxx)
    - Key findings and recommendations
    - Specific library/tool recommendations if applicable
    - Any alternative approaches suggested

    Return a concise markdown summary with actionable recommendations.
    """,
)
```

### Comparative Analysis (Multi-Cohort)

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    Working directory: /Users/sspence/coding_projects/Learnin/The_Cohort

    Run 3 parallel cohorts to research different aspects:
    
    Cohort 1 - Backend patterns:
    Research: "What are the best practices for RAG ingestion pipelines in Python?"
    
    Cohort 2 - Frontend patterns:
    Research: "How do production RAG UIs implement streaming chat with citations?"
    
    Cohort 3 - Infrastructure:
    Research: "What are the tradeoffs between local vs cloud embedding providers?"

    Command:
    .venv/bin/cohort multi "RESEARCH QUESTION" -n 3 -v

    For each cohort capture:
    - Key findings
    - Recommended libraries/approaches
    - Potential issues or considerations
    - Session IDs

    Return executive summary with specific recommendations for the Local RAG project.
    """,
)
```

## Token Efficiency

**CRITICAL**: Always use Task agents, never poll background Bash processes.

| Approach | Tokens/Cohort | 3 Cohorts |
|----------|---------------|-----------|
| Background Bash + polling | ~40,000 | ~120,000 |
| Task agent delegation | ~500 | ~1,500 |

## Output Interpretation

### Consensus Levels
- **UNANIMOUS**: All agents agree
- **STRONG_MAJORITY**: 75%+ agreement
- **WEAK_MAJORITY**: 50-75% agreement
- **SPLIT**: No majority reached

### For Research
When researching alternatives, a SPLIT result is often valuable - it shows tradeoffs that different agents weight differently.

## Session Analysis

After running a cohort, analyze the session:

```bash
# Get session highlights
cohort highlights ses_abc123

# View raw session data
cohort summary ses_abc123
```

## Project-Specific Research Templates

### Template: Library Comparison

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    Research alternatives to CURRENT_LIBRARY for the Local RAG project.
    
    Current implementation: /Users/sspence/Library/CloudStorage/OneDrive-Personal/Hobbyist Development/Local_RAG/backend/src/nexus/PATH_TO_FILE.py
    
    Research question: "Is CURRENT_LIBRARY the best choice, or should we consider ALTERNATIVE1/ALTERNATIVE2?"
    
    Context from project:
    - Use case: DESCRIBE_HOW_IT'S_USED
    - Requirements: LIST_REQUIREMENTS (e.g., "async", "PDF support", "low memory")
    - Current constraints: LIST_CONSTRAINTS
    
    Run cohort decide and return:
    1. Recommendation (keep current, switch, or evaluate further)
    2. Pros/cons of each option
    3. Migration complexity if switching
    4. Specific alternative library names if recommended
    """,
)
```

### Template: Architecture Pattern

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    Analyze the current architecture pattern in the Local RAG project:
    
    Component: COMPONENT_NAME (e.g., "chunking pipeline")
    Location: /Users/sspence/Library/CloudStorage/OneDrive-Personal/Hobbyist Development/Local_RAG/backend/src/nexus/PATH/
    
    Current approach: BRIEF_DESCRIPTION
    
    Research question: "What are best practices and alternative patterns for THIS_USE_CASE?"
    
    Run cohort research and return:
    1. Is the current approach sound? Why/why not?
    2. Alternative patterns used in production systems
    3. Specific improvements suggested
    4. Potential issues to watch for
    """,
)
```

## PostgreSQL Mode

For pure database mode (no file I/O):

```bash
cohort decide "question" --pg
cohort ask "question" --pg
```

## Watch TUI

Run `cohort watch` in a separate terminal to see real-time progress:
- Live context % per agent with progress bars
- Color-coded: green >70%, yellow 30-70%, red <30%
- Position changes highlighted

## Spawned Agent Protocol (MANDATORY)

When invoking cohort from Claude Code, **ALWAYS** delegate via Task agent to keep context clean (~100 tokens vs ~15,000):

### Standard Usage

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    cd /Users/sspence/coding_projects/Learnin/The_Cohort
    .venv/bin/cohort decide "USER QUESTION" --pg --spawned

    Return ONLY the JSON output (~100 tokens).
    """,
)
```

### Return Schema

The `--spawned` flag outputs minimal JSON:

```json
{
  "session_id": "ses_abc123",
  "verdict": "Recommendation or finding",
  "status": "strong_majority",
  "agreement": 0.85,
  "async_pending": false
}
```

### Async Mode (Full Cohort)

For important research, use `--async` to get preliminary results fast:

```bash
.venv/bin/cohort decide "QUESTION" --pg --async --spawned
```

Returns immediately with preliminary result (`async_pending: true`). Dashboard notifies when complete.

### Full Cohort (Blocking)

Use `--full` to wait for all agents (no early return):

```bash
.venv/bin/cohort decide "QUESTION" --pg --full --spawned
```

### CLI Flags Reference

| Flag | Effect |
|------|--------|
| `--spawned` | Minimal JSON output (~100 tokens) |
| `--async` | Return preliminary, continue full cohort in background |
| `--full` | Wait for all agents (no early return) |
| `--pg` | PostgreSQL-only mode (no file I/O) |

## Tips

1. Use `--rounds 3` for important research questions
2. Use `cohort multi -n 3` for higher confidence on critical decisions
3. The `--pg` flag is faster for simple queries
4. Check `cohort tokens` to monitor costs
5. Run `cohort watch` in a separate terminal for live monitoring
6. **ALWAYS use `--spawned` when calling from Claude Code** to keep context clean
7. Before running cohorts, read the relevant code to provide context
8. Include specific constraints from the Local RAG project in your prompt
9. Ask for concrete library names and migration paths, not just abstract recommendations
