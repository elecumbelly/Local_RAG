CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    embed_model TEXT NOT NULL,
    embed_dim INT NOT NULL,
    chunk_size INT NOT NULL,
    overlap INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_collections_unique ON collections(name, version);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    collection_id INT NOT NULL REFERENCES collections(id),
    path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    mtime BIGINT NOT NULL,
    size BIGINT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    ocr_applied BOOLEAN NOT NULL DEFAULT FALSE,
    processed_path TEXT,
    extracted_chars INT NOT NULL DEFAULT 0,
    empty_page_ratio DOUBLE PRECISION NOT NULL DEFAULT 0,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique ON documents(collection_id, path);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags);

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page INT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding VECTOR(1024),
    score_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS eval_runs (
    id SERIAL PRIMARY KEY,
    collection_id INT NOT NULL REFERENCES collections(id),
    model TEXT NOT NULL,
    score JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
