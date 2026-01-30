# 0711 Intelligence Platform - Test Suite

Comprehensive test suite including unit, integration, and end-to-end tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests (isolated, fast)
├── integration/             # Integration tests (require services)
├── e2e/                     # End-to-end tests (full stack)
│   ├── conftest.py         # E2E fixtures
│   ├── helpers.py          # E2E utilities
│   ├── test_complete_onboarding_flow.py
│   ├── test_data_ingestion_flow.py
│   ├── test_chat_interaction_flow.py
│   ├── test_customer_isolation.py
│   ├── test_mcp_orchestration.py
│   └── test_authentication_flow.py
├── utils/                   # Test utilities
│   ├── api_client.py       # HTTP test client
│   ├── websocket_client.py # WebSocket test client
│   └── docker_manager.py   # Docker container management
├── fixtures/                # Test data
│   ├── sample_data/        # Sample files (PDF, CSV, etc.)
│   └── mock_responses.py   # Mock LLM responses
└── conftest.py             # Global pytest fixtures
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx websockets minio

# Start services (for E2E tests)
./START_ALL.sh
```

### Run All Tests

```bash
# With coverage
./run_all_tests.sh

# Without coverage
./run_all_tests.sh --no-coverage

# Fast tests only (exclude slow tests)
./run_all_tests.sh --fast
```

### Run Specific Test Types

```bash
# Unit tests only
./run_all_tests.sh --unit

# Integration tests
./run_all_tests.sh --integration

# E2E tests
./run_e2e_tests.sh
```

### Run Specific E2E Test Suites

```bash
# Onboarding flow
./run_e2e_tests.sh onboarding

# Data ingestion
./run_e2e_tests.sh ingestion

# Chat interactions
./run_e2e_tests.sh chat

# Customer isolation
./run_e2e_tests.sh isolation

# MCP orchestration
./run_e2e_tests.sh mcp

# Authentication
./run_e2e_tests.sh auth

# Fast E2E tests (exclude slow)
./run_e2e_tests.sh fast
```

### Run Individual Test Files

```bash
# Run specific file
pytest tests/e2e/test_chat_interaction_flow.py -v

# Run specific test
pytest tests/e2e/test_chat_interaction_flow.py::TestChatInteractionFlow::test_rest_chat_basic -v

# Run with markers
pytest -m "e2e and not slow" -v
```

## Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.e2e` - End-to-end tests (require full stack)
- `@pytest.mark.slow` - Slow tests (can be skipped for quick feedback)
- `@pytest.mark.skip_ci` - Skip in CI/CD (for manual testing only)

## Test Environment

### Local Development

Tests use services running on localhost (ports 40XX):
- Control Plane API: http://localhost:4080
- Console Backend: http://localhost:4010
- PostgreSQL: localhost:4005
- MinIO: localhost:4050

### Test Environment (Isolated)

Use `docker-compose.test.yml` for isolated test environment (ports 50XX):

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run tests against test services
TEST_API_BASE=http://localhost:5080 \
TEST_CONSOLE_BASE=http://localhost:5010 \
pytest tests/e2e/ -v

# Stop test services
docker-compose -f docker-compose.test.yml down
```

## Coverage

Generate coverage report:

```bash
# HTML report
pytest --cov=ingestion --cov=lakehouse --cov=mcps --cov-report=html

# Open report
firefox htmlcov/index.html

# Terminal report
pytest --cov=ingestion --cov=lakehouse --cov=mcps --cov-report=term-missing
```

## Writing Tests

### E2E Test Example

```python
import pytest
from tests.e2e.helpers import wait_for_ingestion_complete

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_my_feature(
    authenticated_console_client,
    test_customer,
    minio_client
):
    """Test my feature end-to-end."""
    # Upload test file
    bucket = f"customer-{test_customer['customer_id']}"
    # ... upload logic

    # Trigger ingestion
    response = await authenticated_console_client.post("/api/ingest", json={
        "path": f"/data/{bucket}"
    })

    # Wait for completion
    job = response.json()
    await wait_for_ingestion_complete(
        authenticated_console_client,
        job["job_id"]
    )

    # Verify results
    # ... assertions
```

### Using Test Utilities

```python
from tests.utils.api_client import TestConsoleClient
from tests.utils.websocket_client import test_websocket_chat

# REST API
async with TestConsoleClient("http://localhost:4010") as client:
    await client.authenticate(email, password)
    response = await client.send_chat("What is VAT?")

# WebSocket
response = await test_websocket_chat(
    "ws://localhost:4010/api/ws/chat",
    token,
    "What is VAT?"
)
```

## Troubleshooting

### Services Not Running

```bash
# Check service health
curl http://localhost:4080/health
curl http://localhost:4010/health

# Start services
./START_ALL.sh

# Check logs
tail -f /tmp/0711_api.log
tail -f /tmp/0711_console_backend.log
```

### Test Failures

```bash
# Run with verbose output
pytest -vv tests/e2e/test_chat_interaction_flow.py

# Run with debug output
pytest -vv --log-cli-level=DEBUG

# Skip failing tests temporarily
pytest -v -k "not test_failing_test"
```

### Database Issues

```bash
# Reset test database
docker exec 0711-postgres psql -U 0711 -c "DROP DATABASE IF EXISTS 0711_test;"
docker exec 0711-postgres psql -U 0711 -c "CREATE DATABASE 0711_test;"

# Run migrations
alembic upgrade head
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: 0711_test
          POSTGRES_USER: 0711
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v -m "not e2e" --cov
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use fixtures to ensure cleanup (MinIO buckets, database records)
3. **Fast Feedback**: Mark slow tests with `@pytest.mark.slow` so they can be skipped
4. **Real Services**: E2E tests should use real services, not mocks
5. **Customer Isolation**: Always test with `customer_id` to ensure multi-tenancy works
6. **Error Cases**: Test both success and failure scenarios
7. **Skip When Needed**: Use `pytest.skip()` when features aren't implemented yet

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Cover all API endpoints
- **E2E Tests**: Cover complete user journeys

## Contributing

When adding new features:

1. Write unit tests first (TDD)
2. Add integration tests for API endpoints
3. Add E2E tests for complete workflows
4. Run all tests before submitting PR: `./run_all_tests.sh`
