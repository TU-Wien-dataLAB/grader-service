Generic single-database configuration.

# Run Migrations (Primary)

The `grader-service-migrate` script is the primary entry point for applying migrations.
It loads the grader service config file, resolves the database URL, and wraps Alembic to
run `upgrade head`. The Alembic config it uses lives at `grader_service/migrate/alembic.ini`.

```shell
grader-service-migrate -f <path-to-grader-service-config>
```

# Create Revision (Manual)

```shell
alembic -c <path-to-alembic-ini> revision -m "<optional message>"
```

# Run a Migration (Manual)

Remember to change into the directory where the database is. Otherwise, Alembic will create an empty
database in the current directory.

```shell
alembic -c <path-to-alembic-ini> upgrade head
```
