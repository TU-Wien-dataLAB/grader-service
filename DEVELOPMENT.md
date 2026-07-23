# Development Guide

This guide covers setting up a development environment for the Grader Platform monorepo.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- Node.js 20+ (for labextension)
- Docker and Docker Compose
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/TU-Wien-dataLAB/grader-service.git
cd grader

# Install all development and test dependencies
make sync
```

This creates a single virtual environment with both packages and all development, test, and documentation dependencies installed.

### 2. Start Development Environment

```bash
make dev-up
```

This starts:
- Grader Service (with hot-reload)
- JupyterHub
- RabbitMQ
- Celery worker
- SQLite database (default)

The Grader Labextension is loaded inside the JupyterHub-spawned user servers.

Access JupyterHub at `http://localhost:8080`

### 3. Make Changes

- **Service**: Edit Python files in `packages/service/grader_service/`
- **Labextension**: Edit TypeScript files in `packages/labextension/src/`

Service changes are picked up by the dev container; restart the service
container if a reload is needed (`docker compose -f dev/docker-compose/docker-compose.yml restart service`).

Labextension TypeScript changes are hot-reloaded: an in-pod watcher recompiles on save, so
refreshing the browser tab picks up the rebuilt extension. See
[dev/docker-compose/README.md](dev/docker-compose/README.md#editing-the-labextension)
for details. Dependency, Python code, or build-setup changes require rebuilding the
labextension image with `make rebuild-labextension`.

## Development Commands

```bash
# Sync dependencies (dev, test, and docs)
make sync

# Run tests
make test-service      # Service tests only
make test-labextension # Labextension tests only
make test             # All tests
make test-integration  # Integration tests (requires dev environment running)

# Linting
make lint-service
make lint-labextension
make lint

# Building
make build-service
make build-labextension
make build

# Documentation
make docs        # Build Sphinx docs
make docs-clean  # Clean docs
make docs-live   # Live-reload docs

# Docker Compose
make dev-up      # Start dev environment
make dev-down    # Stop dev environment
make dev-logs    # View dev logs
make rebuild-labextension  # Rebuild labextension dev image

# Cleanup
make clean       # Remove build artifacts
```

## Testing

### Unit Tests

```bash
# Service tests
uv run --package grader-service pytest packages/service/grader_service/tests

# Labextension tests
uv run --package grader-labextension pytest packages/labextension/grader_labextension/tests

# With coverage
make test
```

### Integration Tests

```bash
# Start dev environment first
make dev-up

# Wait for services to be ready, then run integration tests
make test-integration
```

## Docker Compose Environments

### Development Environment

Hot-reload for labextension TypeScript edits; service reloads on restart:

```bash
make dev-up
```

See [dev/docker-compose/README.md](dev/docker-compose/README.md) for the full
development workflow, including editing the service and labextension.



## Debugging

### All Service Logs

```bash
make dev-logs
```

To view logs for a specific service:

```bash
docker-compose -f dev/docker-compose/docker-compose.yml logs -f service
docker-compose -f dev/docker-compose/docker-compose.yml logs -f hub
```

### Database Access

```bash
docker compose -f dev/docker-compose/docker-compose.yml exec service sqlite3 /var/lib/grader-service/grader.db
```

## Common Issues

### Issue: Port already in use

```bash
# Check what's using the port
lsof -i :8080

# Stop the environment
make dev-down

# Start again
make dev-up
```

### Issue: Dependencies out of sync

```bash
uv clean
uv sync
```

### Issue: Build artifacts causing problems

```bash
make clean
uv sync
```

## Pre-commit Hooks

Pre-commit hooks run automatically on git commit:

```bash
# Install hooks (done automatically on first sync)
pre-commit install

# Run manually
pre-commit run --all-files
```

## Version Management

Each package is versioned independently with [tbump](https://github.com/your-tools/tbump). tbump is a root dev dependency (`uv sync` installs it) and is configured in each package's `pyproject.toml`.

```bash
# Bump service version (run from the package directory)
cd packages/service
tbump minor  # or: tbump patch, tbump major, tbump 0.13.0

# Bump labextension version
cd packages/labextension
tbump minor
```

tbump patches the version files, creates a `Bump ... to <version>` commit, creates the package tag (`grader-service-X.Y.Z` or `grader-labextension-X.Y.Z`), and pushes both the branch and the tag by default.

## Release Process

1. Update the package's `CHANGELOG.md` (rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`, add a fresh `## [Unreleased]` above it) and commit.
2. Run tbump from the package directory: `cd packages/service && tbump X.Y.Z` (bumps versions, commits, creates the tag, and pushes the branch + tag by default).
3. Create a GitHub Release from the tag (triggers CI: build, test, publish to PyPI, Docker, and Helm).
5. Verify on PyPI, Docker Hub/GHCR, and the Helm repo.

See [RELEASE.md](RELEASE.md) for the full release guide.
