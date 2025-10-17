#!/usr/bin/env bash
# Initialize a PostgreSQL database: run migrations and load initial data.
set -e

/venv/bin/grader-service-migrate -f /app/grader_service_config.py
# Try to load the initial data. This will fail on the first error (e.g. if the data already exists)
# and roll back the transaction.
psql -v ON_ERROR_STOP=1 -h postgres -U postgres -d grader --single-transaction -f /app/data_only.sql
