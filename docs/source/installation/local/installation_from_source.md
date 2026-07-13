# Installation from Source

This guide installs both packages from the repository in editable (development) mode. The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) monorepo, so a single `make sync` installs the `grader-service` and `grader-labextension` packages together with all development, test, and documentation dependencies.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- Node.js 20+ (required to build the labextension frontend)
- Git

## 1. Clone the repository

```bash
git clone https://github.com/TU-Wien-dataLAB/grader.git
cd grader
```

The monorepo contains both packages, so you no longer need to clone the service and labextension repositories separately:

- `packages/service/` — `grader-service` backend
- `packages/labextension/` — `grader-labextension` JupyterLab extension

## 2. Install dependencies

```bash
make sync
```

This runs `uv sync --all-packages --all-groups` and creates a single virtual environment with both packages installed in editable mode. Because the repository is configured as a uv workspace, the labextension's dependency on `grader-service` is resolved from the local package (see `tool.uv.sources` in `packages/labextension/pyproject.toml`).

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

## 5. Developing the labextension

The labextension is installed in editable mode, so Python server-extension changes are picked up automatically. The TypeScript frontend, however, must be rebuilt to be visible in JupyterLab.

To rebuild the frontend once:

```bash
jlpm build
```

To watch the source directory and rebuild automatically on every change:

```bash
make watch-labextension
```

With the watch command running, every saved change is rebuilt and made available in your running JupyterLab after a browser refresh. Note that it may take several seconds for the extension to rebuild. Keep in mind that `make watch-labextension` continues running until you stop it and can consume significant system resources, so `jlpm build` is preferable for one-off changes.

## Next steps

- For the full list of development commands (tests, linting, building, docs, Docker Compose), see the [Development Guide](https://github.com/TU-Wien-dataLAB/grader/blob/main/DEVELOPMENT.md).
- For a fully containerized local stack, see the [Docker installation guide](../docker).
