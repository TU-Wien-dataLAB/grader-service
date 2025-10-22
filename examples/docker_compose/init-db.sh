#!/usr/bin/env bash
set -e

echo "Initialize an sqlite database: run migrations and load initial data."

grader-service-migrate -f /app/grader_service_config.py
# Insert some initial data into the database. The import will fail if the data already
#  has been inserted, so we ignore errors and just continue.
# Note: For debugging, remove the stderr redirection: `2>/dev/null`.
if ! sqlite3 /app/service_dir/grader.db < /app/data_only.sql 2>/dev/null; then
  echo "Initial data import failed; probably the database already exists and contains the data."
fi
