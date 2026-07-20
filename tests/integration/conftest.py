"""Conftest for integration tests with user server spawning."""

import pytest
import requests
import time
import os
import uuid

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:8000/services/grader/api")
SERVICE_BASE_URL = SERVICE_URL.replace("/api", "")
HUB_API_URL = f"{BASE_URL}/hub/api"


@pytest.fixture(scope="session")
def hub_service_token():
    """Get the grader service token from environment variable."""
    token = os.environ.get("GRADER_API_TOKEN")
    if not token:
        pytest.skip("GRADER_API_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for services to be ready."""
    max_retries = 60
    print(f"Waiting for services at {BASE_URL} and {SERVICE_URL}...")
    for i in range(max_retries):
        try:
            hub_response = requests.get(f"{BASE_URL}/hub/health", timeout=2)
            service_response = requests.get(f"{SERVICE_URL}/health", timeout=2)
            if hub_response.status_code == 200 and service_response.status_code == 200:
                print("Services are ready")
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    pytest.skip("Services did not start in time (skipping integration tests)")


@pytest.fixture
def admin_auth_token(wait_for_services, hub_service_token):
    """Get authentication token for admin user."""
    headers = {"Authorization": f"token {hub_service_token}"}
    hub_token = None
    try:
        response = requests.post(
            f"{HUB_API_URL}/users/admin/tokens",
            headers=headers,
            json={"note": "integration test"},
            timeout=5,
        )
        if response.status_code == 201:
            hub_token = response.json()["token"]
        elif response.status_code == 409:
            response = requests.get(f"{HUB_API_URL}/users/admin/tokens", headers=headers, timeout=5)
            if response.status_code == 200:
                tokens = response.json()
                if tokens:
                    hub_token = tokens[0]["token"]
    except requests.exceptions.RequestException:
        pass

    if not hub_token:
        return None

    try:
        response = requests.post(f"{SERVICE_BASE_URL}/login", json={"token": hub_token}, timeout=5)
        if response.status_code == 200:
            return response.json()["api_token"]
    except requests.exceptions.RequestException as e:
        print(f"Failed to login to service: {e}")
        pass
    return None


@pytest.fixture
def test_user(wait_for_services, hub_service_token):
    """Create a test user and return credentials.

    Note: With DummyAuthenticator, passwords are not required.
    Users are created without passwords and can authenticate via token.
    """
    username = f"testuser_{uuid.uuid4().hex[:8]}"

    headers = {"Authorization": f"token {hub_service_token}"}

    try:
        response = requests.post(
            f"{HUB_API_URL}/users/{username}", headers=headers, json={}, timeout=5
        )
        if response.status_code in [201, 409]:
            return {"username": username}
    except requests.exceptions.RequestException as e:
        print(f"Failed to create user: {e}")
        pass

    return None


@pytest.fixture
def user_server(test_user, hub_service_token, wait_for_services):
    """Spawn a user server and yield server info."""
    if not test_user:
        pytest.skip("Could not create test user")

    username = test_user["username"]
    headers = {"Authorization": f"token {hub_service_token}"}

    server_spawned = False
    try:
        response = requests.post(
            f"{HUB_API_URL}/users/{username}/server", headers=headers, timeout=10
        )
        if response.status_code == 202:
            max_wait = 30
            for _ in range(max_wait):
                status_response = requests.get(
                    f"{HUB_API_URL}/users/{username}", headers=headers, timeout=5
                )
                if status_response.status_code == 200:
                    user_data = status_response.json()
                    if user_data.get("servers", {}).get("", {}).get("ready"):
                        server_url = user_data["servers"][""]["url"]
                        print(f"Server ready for {username} at {server_url}")
                        server_spawned = True
                        yield {
                            "username": username,
                            "server_url": server_url,
                            "test_user": test_user,
                        }
                        break
                time.sleep(2)
            else:
                pytest.skip("Server did not start in time")
        else:
            pytest.skip(f"Failed to spawn server: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to spawn server: {e}")
        pytest.skip("Could not spawn user server")
    finally:
        if server_spawned:
            try:
                requests.delete(
                    f"{HUB_API_URL}/users/{username}/server", headers=headers, timeout=10
                )
            except Exception:
                pass


@pytest.fixture
def user_service_token(user_server, hub_service_token):
    """Get service token for the spawned user server."""
    if not user_server:
        return None

    username = user_server["username"]
    headers = {"Authorization": f"token {hub_service_token}"}

    try:
        response = requests.post(
            f"{HUB_API_URL}/users/{username}/tokens",
            headers=headers,
            json={"note": "user server token"},
            timeout=5,
        )
        if response.status_code == 201:
            hub_token = response.json()["token"]
        response = requests.post(f"{SERVICE_BASE_URL}/login", json={"token": hub_token}, timeout=5)
        if response.status_code == 200:
            return response.json()["api_token"]
    except requests.exceptions.RequestException:
        pass
    return None


@pytest.fixture
def lecture_data():
    """Sample lecture data."""
    return {"name": "Test Lecture", "code": "TEST101", "description": "Integration Test Lecture"}


@pytest.fixture
def assignment_data():
    """Sample assignment data."""
    return {
        "name": "Test Assignment 1",
        "description": "Integration Test Assignment",
        "due_date": "2026-12-31T23:59:59Z",
    }
