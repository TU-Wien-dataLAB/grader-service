# Docker

## Prerequisites
- Docker engine
    - [Install Docker Engine](https://docs.docker.com/engine/install/)

```{note}
This setup is intended for local development and testing purposes only.
It is not suitable for production use. Use the [Kubernetes installation](./kubernetes) for production deployments.
```
## Docker compose

For local development, use the docker-compose configuration in the `dev/docker-compose` directory:

### Using docker compose with `SQLite` database

Run the following command from the repository root:
```bash
make dev-up
```

Or directly with docker-compose:
```bash
docker-compose -f dev/docker-compose/docker-compose.yml up -d --build
```

This command builds the images and starts the containers in detached mode. It sets SQLite as its database that is integrated in `Grader Service`.

JupyterHub service will be running on `http://127.0.0.1:8080`

To stop and remove the containers, run:
```bash
make dev-down
```

Or directly:
```bash
docker-compose -f dev/docker-compose/docker-compose.yml down -v
```
This command makes sure that both named and anonymous volumes are removed.
