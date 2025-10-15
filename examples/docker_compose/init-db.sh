
/venv/bin/grader-service-migrate -f /app/grader_service_config.py

psql -h postgres -U postgres -d grader -f /app/data_only.sql
