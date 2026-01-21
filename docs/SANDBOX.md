# Sandbox Directory Mounts

## Overview

Nexus RAG allows you to mount additional host directories into the API container for secure file access. This enables processing of documents from your local file system while maintaining container isolation.

## Configuration

Mounts are defined in `docker-compose.yml`:

```yaml
services:
  api:
    volumes:
      - /path/to/host/docs:/documents:ro
      - /path/to/host/projects:/projects:ro
```

## Modes

- `ro` - Read-only: Container cannot modify files
- `rw` - Read-write: Container can modify files

**Default**: Use read-only (`:ro`) unless you need write access

## Allowed Mount Points

By default, Nexus allows mounting to these container paths:

- `/corpora` - Document collections
- `/documents` - User documents
- `/downloads` - Downloaded files
- `/project` - Project files
- `/app/data` - Application data

## Using Mounts in corpora.yml

Reference mounted paths in your collection configuration:

```yaml
collections:
  library:
    roots: ["/documents"]
    include: ["**/*.pdf"]
```

## Security

The mount validator enforces these rules:

1. **No path traversal**: Paths containing `..` are rejected
2. **No system directories**: `/etc`, `/proc`, `/sys`, `/root`, `/var/run`, `/tmp` are blocked
3. **Allowed paths only**: Only paths under allowed mount points are permitted
4. **Real path resolution**: Symlinks are resolved and validated

## Examples

### Mount Documents directory (read-only)

```bash
# .env
NEXUS_MOUNT_DOCUMENTS=/Users/jane/Documents:/documents:ro

# corpora.yml
collections:
  library:
    roots: ["/documents"]
    include: ["**/*.pdf"]
```

### Mount Projects directory (read-write)

```bash
# .env
NEXUS_MOUNT_PROJECTS=/Users/jane/Projects:/projects:rw

# corpora.yml
collections:
  code:
    roots: ["/projects/my-app/docs"]
    include: ["**/*.md"]
```

## Docker Compose

Mounts are defined directly in `docker-compose.yml`:

```yaml
services:
  api:
    volumes:
      - ${NEXUS_MOUNT_DOCUMENTS:-/Users/jane/Documents:/documents:ro}
```

Or use fixed paths:

```yaml
services:
  api:
    volumes:
      - /Users/jane/Documents:/documents:ro
```

Empty values (`:-`) make mounts optional - they won't be created if not defined.

## Troubleshooting

### Permission denied

If you get "Path not in allowed mount directories" error:

1. Check your `.env` has the correct mount variable
2. Verify the mount path matches the format
3. Ensure the host path exists
4. Restart containers: `make down && make up`

### Files not found

If ingestion can't find files:

1. Verify the mount is active: `docker-compose ps`
2. Check container has access: `docker-compose exec api ls /documents`
3. Ensure read-only mounts if you only need read access

## Best Practices

1. **Use read-only mounts**: Default to `:ro` unless write access is required
2. **Separate concerns**: Use different mounts for different purposes
3. **Absolute paths**: Always use absolute paths from host
4. **Test mounts**: Verify mounts work before running full ingestion
5. **Document paths**: Keep a record of which collection uses which mount
