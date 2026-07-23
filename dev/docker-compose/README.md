# Grader Platform - Development Environment

This directory contains a Docker Compose setup for local development with hot-reload capabilities.

## Features

- **Hot-reload for Service**: Python code changes in `packages/service/grader_service/` are automatically picked up
- **Full stack environment**: Includes Grader Service, JupyterHub, RabbitMQ, and Celery worker
- **Pre-configured users**: admin, instructor, tutor, student

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

### 1. Start the Development Environment

```bash
cd dev/docker-compose
docker compose up -d
```

### 2. Check Service Status

```bash
docker compose ps
```

All services should show "Up" status.

### 3. Access JupyterHub

Open your browser and navigate to:
```
http://localhost:8080
```

### 4. Login Credentials

You can log in with any of the following users:
- `admin` (administrator)
- `instructor` (instructor role)
- `tutor` (tutor role)
- `student` (student role)

No password is required (using DummyAuthenticator).

## Viewing Logs

### View all logs
```bash
docker compose logs -f
```

### View specific service logs
```bash
docker compose logs -f service
docker compose logs -f hub
docker compose logs -f celery-worker
```

## Development Workflow

### Editing Service Code

1. Edit Python files in `packages/service/grader_service/`
2. The service container will automatically detect changes
3. Restart the service container if needed:
   ```bash
   docker compose restart service
   ```

### Editing the Labextension

TypeScript changes in `packages/labextension/src/`, `schema/`, or `style/` are
hot-reloaded into spawned user pods. Spawned pods run a local
`grader-labextension:dev` image that installs the extension in editable mode and
bind-mounts those source directories, with an in-pod watcher
(`tsc -w` + `jupyter labextension watch`) that recompiles on save.

1. Start the dev environment from the repo root (not from this directory) so the
   host path is picked up:
   ```bash
   make dev-up
   ```
   `make dev-up` builds the `grader-labextension:dev` image and sets
   `GRADER_REPO_ROOT`, which `jupyterhub_config.py` uses to bind-mount the
   source. Starting via `docker compose up` directly skips the image build and
   leaves `GRADER_REPO_ROOT` unset (no hot reload).

2. Log in at `http://localhost:8080` and start a server. The pod will have the
   watcher running.

3. Edit a file under `packages/labextension/src/` (or `schema/`, `style/`) and
   save. The in-pod watcher recompiles within a second or two.

4. Refresh the browser tab. The rebuilt labextension bundle is served on the
   next page load.

To watch the watcher output in a running pod:
```bash
docker exec -it jupyter-<username> tail -f /tmp/grader-labextension-watch.log
```

Rebuild the labextension image after changing package dependencies, Python code, or the
build setup in `packages/labextension/`:
```bash
make rebuild-labextension
```

### Editing Configuration

- `grader_service_config.py`: Grader Service configuration
- `jupyterhub_config.py`: JupyterHub configuration

After editing configuration files, restart the affected containers:
```bash
docker compose restart service hub
```

### Labextension not loading

1. If you run the project for the first time, you may just have to wait a while.
   The `grader-labextension:dev` image is built by `make dev-up`; try refreshing
   the start page and relaunching the server if it has failed to start.

2. Check `hub` service logs:
   ```bash
   docker compose logs hub
   ```

3. Check the watcher log inside the spawned pod:
   ```bash
   docker exec -it jupyter-<username> tail -50 /tmp/grader-labextension-watch.log
   ```

4. Rebuild the `grader-labextension:dev` image and restart:
   ```bash
   make rebuild-labextension
   ```

## Architecture

```
┌─────────────────┐
│   JupyterHub    │ :8080
│   (hub)         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌───▼──────────┐
│Service│  │Labextension  │
│:4010  │  │              │
└───┬──┘  └────────────────┘
    │
┌───▼──────┐
│RabbitMQ  │
│:5672     │
└──────────┘
```

## Stopping the Environment

```bash
docker compose down
```

To also remove volumes (database, etc.):
```bash
docker compose down -v
```

## Troubleshooting

### Port already in use

If port 8080 is already in use, you can change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Change 8080 to 8081
```

### Service not starting

Check the logs for errors:
```bash
docker compose logs service
```

Common issues:
- Database migration errors: Check `grader_service_config.py`
- RabbitMQ connection: Ensure rabbitmq container is running

## Network

All containers are connected via the `grader-network` bridge network.

## Volumes

- `service_dir`: Persistent storage for Grader Service data
- `hub_data`: JupyterHub data storage
- `rabbitmq_data`: RabbitMQ message queue data

## Next Steps

- Create your first lecture and assignment
- Test the grading workflow
- Add new features to the service or labextension

For more information, see the main [README.md](../../README.md) and [DEVELOPMENT.md](../../DEVELOPMENT.md).
