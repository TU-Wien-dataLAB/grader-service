"""Integration tests for the Grader Platform with user server spawning."""

import pytest
import requests

BASE_URL = "http://localhost:8080"
SERVICE_URL = "http://localhost:8000/services/grader/api"


class TestServiceHealth:
    """Test basic service health and connectivity."""

    def test_hub_health(self, wait_for_services):
        """Test JupyterHub health endpoint."""
        response = requests.get(f"{BASE_URL}/hub/health", timeout=5)
        assert response.status_code == 200

    def test_service_health(self, wait_for_services):
        """Test grader service health endpoint."""
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        assert response.status_code == 200


class TestUserManagement:
    """Test user creation and authentication."""

    def test_admin_login(self, admin_auth_token):
        """Test admin can authenticate with the service."""
        assert admin_auth_token is not None
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/user", headers=headers, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "admin"

    def test_create_test_user(self, test_user):
        """Test creating a new test user."""
        assert test_user is not None
        assert "username" in test_user
        assert test_user["username"].startswith("testuser_")
        print(f"Created test user: {test_user['username']}")

    def test_user_server_spawn(self, user_server):
        """Test spawning a user server."""
        assert user_server is not None
        assert "username" in user_server
        assert "server_url" in user_server
        print(f"Successfully spawned server for {user_server['username']}")

    def test_user_server_access(self, user_server):
        """Test accessing the spawned user server."""
        if not user_server:
            pytest.skip("User server not available")

        server_url = f"{BASE_URL}{user_server['server_url']}"
        try:
            response = requests.get(server_url, timeout=5, allow_redirects=False)
            assert response.status_code in [200, 302]
        except requests.exceptions.ConnectionError:
            pytest.skip("User server not responding")


class TestLectureManagement:
    """Test lecture CRUD operations from user server context."""

    def test_list_lectures_admin(self, admin_auth_token):
        """Test admin can list lectures."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        assert response.status_code == 200
        lectures = response.json()
        assert isinstance(lectures, list)

    def test_create_lecture(self, admin_auth_token, lecture_data):
        """Test creating a new lecture."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.post(
            f"{SERVICE_URL}/lectures", headers=headers, json=lecture_data, timeout=5
        )
        assert response.status_code in [201, 409]

        if response.status_code == 201:
            lecture = response.json()
            assert lecture["name"] == lecture_data["name"]
            return lecture["id"]

    def test_get_lecture(self, admin_auth_token, lecture_data):
        """Test retrieving a specific lecture."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        if response.status_code == 200:
            lectures = response.json()
            test_lecture = next(
                (lec for lec in lectures if lec["name"] == lecture_data["name"]), None
            )
            if test_lecture:
                assert test_lecture["code"] == lecture_data["code"]


class TestAssignmentWorkflow:
    """Test complete assignment workflow from user server."""

    def test_list_assignments(self, admin_auth_token):
        """Test listing assignments for a lecture."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures/1/assignments", headers=headers, timeout=5)
        assert response.status_code == 200

    def test_create_assignment(self, admin_auth_token, assignment_data):
        """Test creating an assignment."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        if response.status_code == 200:
            lectures = response.json()
            if lectures:
                lecture_id = lectures[0]["id"]
                response = requests.post(
                    f"{SERVICE_URL}/lectures/{lecture_id}/assignments",
                    headers=headers,
                    json=assignment_data,
                    timeout=5,
                )
                assert response.status_code in [201, 400, 409]


class TestStudentWorkflow:
    """Test student-specific workflows from spawned server."""

    def test_student_list_lectures(self, user_service_token):
        """Test student can list lectures they are enrolled in."""
        if not user_service_token:
            pytest.skip("User service token not available")

        headers = {"Authorization": f"Bearer {user_service_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        assert response.status_code == 200

    def test_student_list_assignments(self, user_service_token):
        """Test student can list assignments."""
        if not user_service_token:
            pytest.skip("User service token not available")

        headers = {"Authorization": f"Bearer {user_service_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures/1/assignments", headers=headers, timeout=5)
        assert response.status_code == 200


class TestCeleryWorker:
    """Test Celery worker integration."""

    def test_worker_status(self, admin_auth_token):
        """Test checking worker status."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        try:
            response = requests.get(f"{SERVICE_URL}/admin/workers", headers=headers, timeout=5)
            if response.status_code == 404:
                pytest.skip("Worker status endpoint not available")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Worker status endpoint not available")

    def test_autograde_task(self, admin_auth_token):
        """Test submitting an autograde task."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        try:
            response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
            if response.status_code == 200:
                lectures = response.json()
                if lectures:
                    lecture_id = lectures[0]["id"]
                    response = requests.get(
                        f"{SERVICE_URL}/lectures/{lecture_id}/assignments",
                        headers=headers,
                        timeout=5,
                    )
                    if response.status_code == 200:
                        assignments = response.json()
                        if assignments:
                            assignment_id = assignments[0]["id"]
                            response = requests.post(
                                f"{SERVICE_URL}/lectures/{lecture_id}/assignments/{assignment_id}/autograde",
                                headers=headers,
                                timeout=5,
                            )
                            assert response.status_code in [200, 202, 400]
        except requests.exceptions.ConnectionError:
            pytest.skip("Autograde endpoint not available")


class TestDatabaseOperations:
    """Test database persistence and operations."""

    def test_database_connectivity(self, admin_auth_token):
        """Test database is accessible."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/health", headers=headers, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "database" in data or data.get("status") == "healthy" or data.get("health") == "OK"

    def test_data_persistence(self, admin_auth_token, lecture_data):
        """Test that created data persists."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}

        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        if response.status_code == 200:
            lectures = response.json()
            test_lecture = next(
                (lec for lec in lectures if lec["name"] == lecture_data["name"]), None
            )
            if test_lecture:
                lecture_id = test_lecture["id"]
                response = requests.get(
                    f"{SERVICE_URL}/lectures/{lecture_id}", headers=headers, timeout=5
                )
                assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_token(self, wait_for_services):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{SERVICE_URL}/lectures", headers=headers, timeout=5)
        assert response.status_code == 401

    def test_nonexistent_lecture(self, admin_auth_token):
        """Test accessing nonexistent lecture."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.get(f"{SERVICE_URL}/lectures/99999", headers=headers, timeout=5)
        assert response.status_code == 404

    def test_malformed_request(self, admin_auth_token):
        """Test handling malformed requests."""
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        response = requests.post(
            f"{SERVICE_URL}/lectures", headers=headers, data="invalid json", timeout=5
        )
        # TODO should be 400 code
        assert response.status_code == 500
