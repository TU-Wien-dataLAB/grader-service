# Docker

## Prerequisites
- Docker engine
    - [Install Docker Engine](https://docs.docker.com/engine/install/)

```{warning}
This setup is intended for local development and testing purposes only.
It is **not suitable for production use**, in particular because the default local autograding executors run student code with full access to the service database and filesystem - a malicious submission could read or alter grades and other students' work. Use the [Kubernetes installation](./kubernetes) with `KubeAutogradeExecutor`, which isolates each grading job in its own pod, for any deployment that grades untrusted student code.
```
## Docker compose

For local development, use the docker-compose configuration in the `dev/docker-compose` directory:

### Using docker compose with `SQLite` database

Run the following command from the repository root:
```bash
make dev-up
```

Or directly with docker compose:
```bash
docker compose -f dev/docker-compose/docker-compose.yml up -d --build
```

This command builds the images and starts the containers in detached mode. It sets SQLite as its database that is integrated in `Grader Service`.

JupyterHub service will be running on `http://127.0.0.1:8080`

To stop and remove the containers, run:
```bash
make dev-down
```

Or directly:
```bash
docker compose -f dev/docker-compose/docker-compose.yml down -v
```
This command makes sure that both named and anonymous volumes are removed.
