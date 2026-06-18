#!/bin/bash
# Script to get the grader service token from JupyterHub's database
# This is needed because JupyterHub auto-generates tokens when not specified

# Wait for JupyterHub to be ready
sleep 5

# Get the token from JupyterHub's SQLite database
HUB_DB="/data/jupyterhub.sqlite"

if [ -f "$HUB_DB" ]; then
    TOKEN=$(sqlite3 "$HUB_DB" "SELECT token FROM api_tokens WHERE client_id='grader' LIMIT 1;" 2>/dev/null || echo "")
    if [ -n "$TOKEN" ]; then
        echo "GRADER_API_TOKEN=$TOKEN"
        exit 0
    fi
fi

echo "Failed to retrieve GRADER_API_TOKEN" >&2
exit 1
