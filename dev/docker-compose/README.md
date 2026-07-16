# Grader Platform - Development Environment

This directory contains a Docker Compose setup for local development with hot-reload capabilities.

## Features

- **Hot-reload for Service**: Python code changes in `packages/service/grader_service/` are automatically picked up
- **Hot-reload for Labextension**: TypeScript changes in `packages/labextension/` trigger rebuilds
- **Full stack environment**: Includes Grader Service, Labextension, JupyterHub, RabbitMQ, and Celery worker
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

### Editing Labextension Code

1. Edit TypeScript files in `packages/labextension/src/`
2. The `hub` container will rebuild on changes
3. Refresh your browser to see changes

### Editing Configuration

- `grader_service_config.py`: Grader Service configuration
- `jupyterhub_config.py`: JupyterHub configuration

After editing configuration files, restart the affected containers:
```bash
docker compose restart service hub
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

### Labextension not loading

1. If you run the project for the first time, you may just have to wait a while.
   The `grader-labextension` Docker image has to be pulled from the registry, but this
   is only done on `docker compose up`. Try refreshing the start page and relaunching
   the server if it has failed to start.

2. Check `hub` service build logs:
   ```bash
   docker compose logs hub
   ```
3. Rebuild the `hub` container:
   ```bash
   docker compose up -d --build hub
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
