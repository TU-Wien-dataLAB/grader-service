#!/usr/bin/env bash
set -e

echo "Initialize a PostgreSQL database: run migrations, load initial data, and create initial repos."

/app/.venv/bin/grader-service-migrate -f /app/grader_service_config.py
# Try to load the initial data. This will fail on the first error (e.g. if the data already exists)
# and roll back the transaction.
if ! psql -v ON_ERROR_STOP=1 -h postgres -U postgres -d grader --single-transaction -f /app/data_only.sql; then
  echo "Initial data import failed; probably the database already exists and contains the data."
fi

cp -r /app/init_repos/* /app/service_dir/git
