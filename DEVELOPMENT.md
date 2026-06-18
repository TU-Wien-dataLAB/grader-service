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
git clone https://github.com/TU-Wien-dataLAB/grader.git
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
- Grader Labextension (with hot-reload)
- PostgreSQL database
- RabbitMQ
- JupyterHub

Access JupyterHub at `http://localhost:8080`

### 3. Make Changes

- **Service**: Edit Python files in `packages/service/grader_service/`
- **Labextension**: Edit TypeScript files in `packages/labextension/src/`

Changes are automatically picked up by the development environment.

## Development Commands

```bash
# Sync dependencies (dev, test, and docs)
make sync

# Run tests
make test-service      # Service tests only
make test-labextension # Labextension tests only
make test-all          # All tests
make test-integration  # Integration tests (requires dev environment running)

# Linting
make lint-service
make lint-labextension
make lint-all

# Building
make build-service
make build-labextension
make build-all

# Documentation
make docs        # Build Sphinx docs
make docs-clean  # Clean docs
make docs-live   # Live-reload docs

# Docker Compose
make dev-up      # Start dev environment
make dev-down    # Stop dev environment
make dev-logs    # View dev logs

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
make test-all
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

Hot-reload enabled for both packages:

```bash
make dev-up
```



## Debugging

### All Service Logs

```bash
make dev-logs
```

To view logs for a specific service:

```bash
docker-compose -f dev/docker-compose/docker-compose.yml logs -f service
docker-compose -f dev/docker-compose/docker-compose.yml logs -f labextension
docker-compose -f dev/docker-compose/docker-compose.yml logs -f hub
```

### Database Access

```bash
docker-compose -f dev/docker-compose/docker-compose.yml exec postgres psql -U grader -d grader
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

Each package has independent versioning:

```bash
# Bump service version
cd packages/service
tbump minor

# Bump labextension version
cd packages/labextension
tbump minor
```

## Release Process

1. Bump version with tbump
2. Create git tag: `git tag grader-service-X.Y.Z` or `git tag grader-labextension-X.Y.Z`
3. Push tag: `git push origin grader-service-X.Y.Z`
4. GitHub Actions automatically builds and publishes to PyPI

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed release instructions.
