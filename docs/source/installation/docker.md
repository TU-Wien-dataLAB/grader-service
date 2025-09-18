# Docker

## Prerequisites
- Docker engine 
    - [Install Docker Engine](https://docs.docker.com/engine/install/)

```{note}
This setup is intended for local development and testing purposes only.
It is not suitable for production use. Use the [Kubernetes installation](./kubernetes) for production deployments.
```
## Docker compose

Navigate to `examples/docker_compose` directory. From there you can use the predefined `docker-compose.yml` file to start 
the containers together with their services.

### Using docker compose with `SQLite` database

Run the following command:
```bash
docker compose up --build -d
```

This command builds the images and starts the containers in detached mode. It sets SQLite as its database that is integrated in `Grader Service`.

JupyterHub service will be running on `http://127.0.0.1:8080`

To stop and remove the containers, run:
```bash
docker compose down -v
```
This command makes sure that both named and anonymous volumes are removed.
### Using docker compose with `PostgreSQL` database

There is an option to use an externalized and containerized `PostgreSQL` database. Necessary setup for this database is 
defined in a separate `docker-compose-postgres.yml` file.

Run the following command:
```bash
docker compose -f docker-compose.yml -f docker-compose-postgres.yml up -d
```

To stop and remove the containers, run:
```bash
docker compose -f docker-compose.yml -f docker-compose-postgres.yml down -v
```
