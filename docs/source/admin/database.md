# Database

Grader Service stores its state (lectures, assignments, submissions, users, roles, etc.) in a relational database. The schema is managed with [Alembic](https://alembic.sqlalchemy.org/) migrations that live in the `grader_service.migrate` module (with `alembic.ini`, `env.py` and a `versions/` directory). Migrations are applied with the `grader-service-migrate` command, the `grader_service.migrate.migrate:main` entry point installed with `grader-service`.

## Running migrations

`grader-service-migrate` runs `alembic upgrade head`, i.e. it applies all pending migrations up to the latest revision. It reads the database URL from the Grader Service configuration, so it must be pointed at the same config file the service uses:

```bash
grader-service-migrate -f /path/to/grader_service_config.py
```

The `-f` / `--config` option loads the config file, resolves `c.GraderService.db_url`, and applies the migrations to that database.

### Running migrations on upgrade

Always run the migrations before (re)starting the service after an upgrade. The development Docker Compose stack does exactly this: it runs `grader-service-migrate -f /app/grader_service_config.py` and only then starts `grader-service -f /app/grader_service_config.py`. Mirror this in your own deployment, for example:

```bash
grader-service-migrate -f /etc/grader/grader_service_config.py \
  && grader-service -f /etc/grader/grader_service_config.py
```

The `grader-service-migrate` entry point applies upgrades to `head` only; it does not expose a downgrade path. Before upgrading in production, take a database backup (see [Backup](#backup)) so you can restore if a migration ever needs to be rolled back.

## Backup

Grader Service stores all state in the relational database configured via `c.GraderService.db_url`. To back up a deployment, back up that database.

For a PostgreSQL deployment, use `pg_dump`:

```bash
pg_dump --format=custom --file=grader-$(date +%F).dump "$DATABASE_URL"
```

Restore with:

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" grader-YYYY-MM-DD.dump
```

Take a backup before every upgrade so you can restore if a migration needs to be rolled back, since `grader-service-migrate` only applies upgrades and does not expose a downgrade path.
