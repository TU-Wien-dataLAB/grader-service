# Contributing to Grader Platform

Thank you for contributing to Grader Platform! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/grader.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Set up development environment:

```bash
make sync
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## Development Workflow

### 1. Make Changes

- Service: `packages/service/grader_service/`
- Labextension: `packages/labextension/`

### 2. Run Tests

```bash
# Run all tests
make test-all

# Run specific test file
pytest packages/service/grader_service/tests/test_example.py
```

### 3. Lint Code

```bash
make lint-all
```

### 4. Commit Changes

Pre-commit hooks run automatically. Ensure all checks pass:

```bash
pre-commit run --all-files
```

### 5. Create Pull Request

Push your branch and create a PR on GitHub.

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Use ruff for linting and formatting
- Write docstrings for public APIs

### TypeScript

- Follow existing code style
- Use ESLint and Prettier
- Write JSDoc comments for public APIs

## Testing

### Writing Tests

- Write tests for new features
- Maintain or improve code coverage
- Use pytest for Python tests
- Use Jest for TypeScript tests

### Test Categories

- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Keep documentation up to date with code changes

### User Documentation

- Update Sphinx documentation in `docs/`
- Update README if adding new features
- Add changelog entries

## Release Process

### Service Release

```bash
cd packages/service
tbump minor  # or patch/major
git push origin main
git push origin grader-service-X.Y.Z
```

### Labextension Release

```bash
cd packages/labextension
tbump minor  # or patch/major
git push origin main
git push origin grader-labextension-X.Y.Z
```

GitHub Actions automatically:
1. Builds the package
2. Runs tests
3. Publishes to PyPI
4. Creates Docker image (for service)

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Read [DEVELOPMENT.md](DEVELOPMENT.md)
