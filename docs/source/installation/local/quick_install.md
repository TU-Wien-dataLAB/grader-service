# Quick installation

This is the fastest way to get the Grader platform running locally from source. It uses the repository's `Makefile` targets, which wrap [uv](https://docs.astral.sh/uv/) and the workspace packages so you don't have to run commands manually in each package.

```{note}
This setup is intended for **local development and testing purposes only**.
It is **not suitable for production use**. Use the [Kubernetes installation](../kubernetes) for production deployments.
```

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ (only needed when rebuilding the labextension frontend)
- Git

## 1. Clone the repository

```bash
git clone https://github.com/TU-Wien-dataLAB/grader.git
cd grader
```

The repository is a monorepo containing both the `grader-service` backend (`packages/service`) and the `grader-labextension` frontend (`packages/labextension`). You no longer need to clone them separately.

## 2. Install dependencies

```bash
make sync
```

This runs `uv sync --all-packages --all-groups`, which creates a single virtual environment with both packages installed in editable mode plus all development, test, and documentation dependencies.

## 3. Create the database

The repository ships example configuration files in `dev/local/token/`. Create the database schema by running the migration against the service config:

```bash
uv run grader-service-migrate -f dev/local/token/grader_service_config.py
```

The default config uses an embedded SQLite database and runs autograding tasks eagerly, so no external database or message broker is required for local testing.

## 4. Start Grader Service and JupyterHub

Start the Grader Service:

```bash
make run-service
```

Grader Service runs at `http://127.0.0.1:4010`.

In a separate terminal, start JupyterHub:

```bash
make run-hub
```

JupyterHub will be running at `http://127.0.0.1:8080`.

```{note}
Start the Grader Service **before** JupyterHub.
```

## Full stack with Docker Compose

If you prefer a fully containerized environment (including PostgreSQL, RabbitMQ, a Celery worker, and hot-reload), use:

```bash
make dev-up
```

See the [Docker installation guide](../docker) for details.

## Cleanup

To remove build artifacts and caches:

```bash
make clean
```

This does not delete the virtual environment. To recreate it from scratch, run `make sync` again.
