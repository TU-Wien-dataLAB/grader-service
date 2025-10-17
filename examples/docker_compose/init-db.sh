#!/usr/bin/env bash
# Initialize an sqlite database: run migrations and load initial data.
set -e

grader-service-migrate -f /app/grader_service_config.py
# Insert some initial data into the database. The import will fail if the data already
#  has been inserted, so we ignore errors and just continue.
sqlite3 /app/service_dir/grader.db < /app/data_only.sql || true
