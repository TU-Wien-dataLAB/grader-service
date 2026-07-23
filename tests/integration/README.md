# Integration Tests

Integration tests for the Grader Platform that test the complete system with spawned user servers.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with `uv` package manager
- Required Python packages installed: `pytest`, `requests`

## Quick Start

### Run Integration Tests with Docker Compose

The easiest way to run integration tests is to use the provided Makefile target:

```bash
make test-integration
```

This command will:
1. Start all required services (service, hub, rabbitmq, celery-worker)
2. Wait for services to be healthy
3. Run integration tests
4. Stop and remove all containers

### Run Tests Against Existing Environment

To run tests against an environment you have already started, invoke pytest directly:

```bash
# Start the environment
GRADER_API_TOKEN=$(openssl rand -hex 16) docker-compose -f dev/docker-compose/docker-compose.yml up -d

# Run tests against the existing environment
uv run pytest tests/integration -vvv

# Stop the environment when done
make dev-down
```

Note: `make test-integration` creates the env, runs tests, then tears it down. To run tests against an already-running env instead, use `uv run pytest tests/integration -vvv` directly as shown above.

## Test Structure

### Fixtures

The integration tests use several pytest fixtures:

- `wait_for_services`: Waits for all services to be healthy
- `hub_service_token`: Gets the service token from environment
- `admin_auth_token`: Authenticates as admin user
- `test_user`: Creates a test user
- `user_server`: Spawns a user server for testing
- `user_service_token`: Gets service token for spawned user
- `lecture_data`: Sample lecture data
- `assignment_data`: Sample assignment data

### Test Classes

1. **TestServiceHealth**: Basic health checks for all services
2. **TestUserManagement**: User creation, authentication, and server spawning
3. **TestLectureManagement**: CRUD operations for lectures
4. **TestAssignmentWorkflow**: Assignment creation and management
5. **TestStudentWorkflow**: Student-specific operations
6. **TestDatabaseOperations**: Database connectivity and persistence
7. **TestErrorHandling**: Error cases and edge cases

## Configuration

### Environment Variables

- `GRADER_API_TOKEN`: Service token for authentication (auto-generated if not set)
- `BASE_URL`: JupyterHub URL (default: http://localhost:8080)
- `SERVICE_URL`: Grader service URL (default: http://localhost:8000/services/grader/api)
- `DATABASE_TYPE`: Database type (sqlite or postgres, default: sqlite)

### Docker Compose Configuration

The dev docker-compose file includes:
- **service**: Grader service with hot-reload
- **hub**: JupyterHub with DockerSpawner
- **rabbitmq**: Message broker
- **celery-worker**: Celery worker for async tasks
- **test-runner**: Optional test runner service (use with `--profile test`)

## Makefile Targets

```bash
make test-integration   # Create env, run tests, then tear it down
make dev-up             # Start the dev environment
make dev-down           # Stop the dev environment
make dev-logs           # Tail logs from all services
```

## Running Specific Tests

Run specific test classes:

```bash
# Run only health tests
uv run pytest tests/integration/test_integration.py::TestServiceHealth -v

# Run only user management tests
uv run pytest tests/integration/test_integration.py::TestUserManagement -v

# Run only student workflow tests
uv run pytest tests/integration/test_integration.py::TestStudentWorkflow -v
```

## Debugging

### View Service Logs

```bash
# View all logs
make dev-logs

# View specific service logs
docker compose -f dev/docker-compose/docker-compose.yml logs service
docker compose -f dev/docker-compose/docker-compose.yml logs hub
docker compose -f dev/docker-compose/docker-compose.yml logs celery-worker
```

### Run Tests with Verbose Output

```bash
GRADER_API_TOKEN=$(openssl rand -hex 16) uv run pytest tests/integration -v -s
```

### Check Service Health Manually

```bash
# Check JupyterHub health
curl http://localhost:8080/hub/health

# Check grader service health
curl http://localhost:8000/services/grader/api/health

# Check RabbitMQ health
docker-compose -f dev/docker-compose/docker-compose.yml exec rabbitmq rabbitmq-diagnostics -q ping
```

## Common Issues

### Services Not Starting

If services don't start properly:

```bash
# Clean and restart
make dev-down
make test-integration
```

### Tests Timeout

If tests timeout waiting for services:

1. Increase the wait time in `conftest.py`
2. Check service logs: `make dev-logs`
3. Verify Docker has enough resources

### Token Issues

If authentication fails:

```bash
# Generate a new token and restart
GRADER_API_TOKEN=$(openssl rand -hex 16) docker-compose -f dev/docker-compose/docker-compose.yml down -v
GRADER_API_TOKEN=$(openssl rand -hex 16) docker-compose -f dev/docker-compose/docker-compose.yml up -d
```

## Adding New Tests

When adding new integration tests:

1. Use appropriate fixtures for setup/teardown
2. Add descriptive test names and docstrings
3. Handle connection errors gracefully with `pytest.skip()`
4. Clean up resources in `finally` blocks
5. Test both success and error cases

Example:

```python
def test_new_feature(self, admin_auth_token):
    """Test new feature functionality."""
    headers = {"Authorization": f"Bearer {admin_auth_token}"}
    try:
        response = requests.get(
            f"{SERVICE_URL}/new-feature",
            headers=headers,
            timeout=5
        )
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Service not available")
```

## CI/CD Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Integration Tests
  run: |
    make test-integration
  env:
    GRADER_API_TOKEN: ${{ secrets.GRADER_API_TOKEN }}
```

## Performance Tips

- Use `--profile test` to run tests in the test-runner container
- Parallelize independent tests with `pytest-xdist`
- Use test markers to run subsets of tests
- Clean up volumes periodically to free disk space
