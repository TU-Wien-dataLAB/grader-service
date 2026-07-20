# Grader Platform

A comprehensive grading platform for Jupyter notebooks with automatic grading capabilities.

## Components

This monorepo contains two main packages:

- **[Grader Service](packages/service/README.rst)** - Backend service for managing users, assignments, submissions, and grading
- **[Grader Labextension](packages/labextension/README.md)** - JupyterLab extension providing UI for the grading platform

## Quick Start

### Development Setup

```bash
# Clone the repository
git clone https://github.com/TU-Wien-dataLAB/grader-service.git
cd grader

# Install all dependencies including dev and docs requirements
make sync

# Run tests
make test

# Start development environment
make dev-up
```



## Documentation

- [Development Guide](DEVELOPMENT.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Service Documentation](https://grader-service.readthedocs.io/en/latest/)
- [Labextension README](packages/labextension/README.md)

## Directory Structure

```
grader/
├── packages/
│   ├── service/          # Grader Service backend
│   └── labextension/     # JupyterLab extension
├── dev/
│   └── docker-compose/   # Development environment
├── tests/
│   └── integration/      # Integration tests
└── ...
```

## Badges

[![Documentation Status](https://readthedocs.org/projects/grader-service/badge/?version=latest)](https://grader-service.readthedocs.io/en/latest/)
[![License](https://img.shields.io/github/license/TU-Wien-dataLAB/grader-service)](LICENSE)

## License

BSD-3-Clause License - see [LICENSE](LICENSE) for details.
