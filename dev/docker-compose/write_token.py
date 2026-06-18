#!/usr/bin/env python3
"""Write the grader service token to a file that can be read by tests."""
import os
import sqlite3
import time

DB_PATH = "/app/jupyterhub.sqlite"
TOKEN_FILE = "/app/grader_api_token.txt"

def get_service_token():
    """Extract the service token from JupyterHub's database."""
    # Wait for database to be populated
    for _ in range(30):
        try:
            if not os.path.exists(DB_PATH):
                time.sleep(1)
                continue

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if api_tokens table exists and has the grader token
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_tokens'")
            if not cursor.fetchone():
                conn.close()
                time.sleep(1)
                continue

            # Try to get the token info - we need to find it by client_id
            cursor.execute("SELECT id, client_id FROM api_tokens WHERE client_id = 'grader'")
            result = cursor.fetchone()
            conn.close()

            if result:
                # We found the token record, but the actual token value is hashed
                # We can't retrieve it - JupyterHub stores only the hash
                # The token was generated during service registration
                # We need to use a different approach
                print(f"Found grader token record: {result}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

    return None

if __name__ == "__main__":
    token = get_service_token()
    if token:
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print(f"Token written to {TOKEN_FILE}")
    else:
        print("Could not retrieve token")
