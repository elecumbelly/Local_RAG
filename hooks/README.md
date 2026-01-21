# Hooks System

## Directory Structure

```
hooks/
├── README.md                          # This file
├── pre-ingest-{collection}.sh         # Run before ingesting a collection
├── post-ingest-{collection}.sh        # Run after ingesting a collection
├── pre-query.sh                      # Run before processing user query
├── post-retrieve.sh                   # Run after retrieving chunks
├── pre-answer.sh                      # Run before generating answer
├── post-answer.sh                     # Run after generating answer
└── examples/                         # Example hooks
    ├── notify-slack.sh
    ├── validate-pdfs.sh
    └── log-metrics.sh
```

## Naming Conventions

### Ingestion Hooks
- `pre-ingest-{collection}.sh` - Runs before ingestion of specified collection
- `post-ingest-{collection}.sh` - Runs after ingestion of specified collection
- Example: `pre-ingest-library.sh`, `post-ingest-dev.sh`

### Query Hooks
- `pre-query.sh` - Runs before query embedding and retrieval
- `post-retrieve.sh` - Runs after chunk retrieval, before answer generation
- `pre-answer.sh` - Runs before generating final answer
- `post-answer.sh` - Runs after answer is generated

## Hook Environment Variables

All hooks receive these environment variables:

### Ingestion Hooks
- `NEXUS_COLLECTION` - Name of collection being processed
- `NEXUS_FILES` - Comma-separated list of file paths being ingested
- `NEXUS_PROCESSED_COUNT` - Number of files processed
- `NEXUS_SKIPPED_COUNT` - Number of files skipped
- `NEXUS_FAILED_COUNT` - Number of files that failed

### Query Hooks
- `NEXUS_QUERY` - The user's query string
- `NEXUS_COLLECTIONS` - Comma-separated list of collections searched
- `NEXUS_CHUNK_COUNT` - Number of chunks retrieved

## Hook Return Values

Hooks can influence behavior by printing to stdout:

### Modify Query
Print modified query: `echo "MODIFIED_QUERY:expanded query text"`

### Skip Processing
Print skip directive: `echo "SKIP:reason for skipping"`

### Add Metadata
Print metadata: `echo "METADATA:key=value"`

## Execution Rules

1. Hooks must be executable (`chmod +x`)
2. Hooks must exit with status 0 on success, non-zero on failure
3. Ingestion continues if hook fails (logs warning)
4. Query hooks that return non-zero status stop request processing

## Security

- Hooks run with limited permissions
- Only allowed to access mounted directories
- Timeout after 60 seconds
- Cannot modify system configuration

## Usage Examples

### Creating a Pre-Ingest Hook

```bash
cat > hooks/pre-ingest-library.sh << 'EOF'
#!/bin/bash
set -e

echo "Validating PDF files before ingestion for collection: $NEXUS_COLLECTION"

# Example: Check file sizes
for file in $(echo "$NEXUS_FILES" | tr "," "\n")
do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        size_mb=$((size / 1024 / 1024))
        if [ $size_mb -gt 100 ]; then
            echo "WARNING: File $file is larger than 100MB ($size_mb MB)"
        fi
    fi
done

echo "Validation complete, proceeding with ingestion"
EOF

chmod +x hooks/pre-ingest-library.sh
```

### Creating a Post-Ingest Hook for Notifications

```bash
cat > hooks/post-ingest-library.sh << 'EOF'
#!/bin/bash
set -e

echo "Ingestion complete for collection: $NEXUS_COLLECTION"
echo "Processed: $NEXUS_PROCESSED_COUNT documents"
echo "Skipped: $NEXUS_SKIPPED_COUNT documents"
echo "Failed: $NEXUS_FAILED_COUNT documents"

# Example: Send notification to external service
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    payload="{
        \"text\": \"Nexus RAG: Ingestion complete for '$NEXUS_COLLECTION'\",
        \"username\": \"Nexus Bot\",
        \"icon_emoji\": \":white_check_mark:\"
    }"
    
    curl -X POST -H 'Content-Type: application/json' \
        -d "$payload" \
        "$SLACK_WEBHOOK_URL"
fi

echo "Post-ingestion hook executed"
EOF

chmod +x hooks/post-ingest-library.sh
```

### Configuring Hooks in corpora.yml

Add hook configuration to your collection:

```yaml
collections:
  library:
    roots: ["/corpora/library"]
    include: ["**/*.pdf"]
    exclude: []
    tags: ["library"]
    hooks:
      pre_ingest: "hooks/pre-ingest-library.sh"
      post_ingest: "hooks/post-ingest-library.sh"
  
  dev:
    roots: ["/corpora/dev"]
    include: ["**/*.pdf"]
    exclude: ["**/tmp/**"]
    tags: ["dev"]
```

### Query Transformation Hook Example

```bash
cat > hooks/pre-query.sh << 'EOF'
#!/bin/bash
set -e

# Example: Expand common abbreviations
query="$NEXUS_QUERY"

# Expand abbreviations
query="${query//RAG/Retrieval Augmented Generation}"
query="${query//LLM/Large Language Model}"
query="${query//API/Application Programming Interface}"

if [ "$query" != "$NEXUS_QUERY" ]; then
    echo "MODIFIED_QUERY:$query"
else
    echo "No query modifications needed"
fi
EOF

chmod +x hooks/pre-query.sh
```

### Chunk Filtering Hook Example

```bash
cat > hooks/post-retrieve.sh << 'EOF'
#!/bin/bash
set -e

# This hook receives NEXUS_CHUNK_COUNT but doesn't have access to chunk data
# It can only influence retrieval behavior

echo "Retrieved $NEXUS_CHUNK_COUNT chunks for collections: $NEXUS_COLLECTIONS"

# Example: Log for analytics
echo "METADATA:chunks_retrieved=$NEXUS_CHUNK_COUNT"
echo "METADATA:query=$(echo "$NEXUS_QUERY" | base64)"
EOF

chmod +x hooks/post-retrieve.sh
```

## Troubleshooting

### Hook Not Executing

If a hook isn't executing:
1. Check file permissions: `ls -l hooks/pre-ingest-library.sh`
2. Make executable: `chmod +x hooks/pre-ingest-library.sh`
3. Check hook path in corpora.yml
4. Check logs for error messages

### Hook Failing Ingestion

If ingestion stops due to hook failure:
1. Run hook manually to see error: `NEXUS_COLLECTION=library NEXUS_FILES=/corpora/test.pdf ./hooks/pre-ingest-library.sh`
2. Check hook script for syntax: `bash -n hooks/pre-ingest-library.sh`
3. Check file paths in hook environment variables

### Hook Timeout

If hooks time out after 60 seconds:
1. Check hook performs long-running operations
2. Optimize hook to complete faster
3. Consider using background tasks for async operations

## Best Practices

1. **Use set -e**: Exit on first error
2. **Log all actions**: Echo what the hook is doing
3. **Validate inputs**: Check environment variables before processing
4. **Handle errors gracefully**: Provide useful error messages
5. **Keep hooks simple**: Complex hooks are harder to debug
6. **Test hooks locally**: Before adding to production system
