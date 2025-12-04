Generic single-database configuration.

# Create Revision

```shell
alembic -c <path-to-alembic-ini> revision -m "<optional message>"
```

# Run a Migration

Remember to change into the directory where the database is. Otherwise, Alembic will create an empty
database in the current directory.

```shell
alembic -c <path-to-alembic-ini> upgrade head
```
