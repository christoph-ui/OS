"""
E2E Test Configuration and Fixtures

Provides fixtures for end-to-end testing with real services.
"""

import pytest
import asyncio
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, AsyncGenerator
import httpx
from minio import Minio


# Test configuration
TEST_API_BASE = os.getenv("TEST_API_BASE", "http://localhost:4080")
TEST_CONSOLE_BASE = os.getenv("TEST_CONSOLE_BASE", "http://localhost:4010")
TEST_MINIO_ENDPOINT = os.getenv("TEST_MINIO_ENDPOINT", "localhost:4050")
TEST_MINIO_ACCESS_KEY = os.getenv("TEST_MINIO_ACCESS_KEY", "0711admin")
TEST_MINIO_SECRET_KEY = os.getenv("TEST_MINIO_SECRET_KEY", "0711secret")
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://0711:0711_dev_password@localhost:4005/0711_control")

# Enable testing mode for Console Backend (uses MockPlatform)
os.environ["CONSOLE_TESTING"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test data fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "sample_data"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for Control Plane API."""
    async with httpx.AsyncClient(base_url=TEST_API_BASE, timeout=30.0) as client:
        yield client


@pytest.fixture
async def console_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for Console Backend API."""
    async with httpx.AsyncClient(base_url=TEST_CONSOLE_BASE, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def minio_client() -> Minio:
    """MinIO client for file storage tests."""
    return Minio(
        endpoint=TEST_MINIO_ENDPOINT,
        access_key=TEST_MINIO_ACCESS_KEY,
        secret_key=TEST_MINIO_SECRET_KEY,
        secure=False
    )


@pytest.fixture
async def test_customer(api_client: httpx.AsyncClient) -> dict:
    """
    Create a test customer with authentication.

    Returns dict with:
        - customer_id
        - email
        - token
        - password
    """
    import uuid
    from datetime import datetime

    # Generate unique test customer
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"test-{timestamp}-{uuid.uuid4().hex[:8]}@test.0711.io"
    password = "TestPass123!"
    company_name = f"Test Company {timestamp}"

    # MinIO bucket names must be DNS-compliant (no underscores)
    # Use timestamp + random for unique customer_id
    customer_id = f"test-{timestamp}-{uuid.uuid4().hex[:6]}"

    # Try to signup (might not be implemented yet, so we'll create a token manually)
    try:
        response = await api_client.post("/api/auth/signup", json={
            "email": email,
            "password": password,
            "company_name": company_name,
            "contact_name": "Test User"
        })

        if response.status_code == 201:
            data = response.json()
            customer_id = data.get("customer_id", customer_id)
            token = data.get("token", "mock_token_for_testing")
        else:
            # Fallback: use generated customer_id
            token = "mock_token_for_testing"
    except Exception:
        # Fallback for testing without auth
        token = "mock_token_for_testing"

    return {
        "customer_id": customer_id,
        "email": email,
        "password": password,
        "company_name": company_name,
        "token": token
    }


@pytest.fixture
async def test_customer_2(api_client: httpx.AsyncClient) -> dict:
    """Second test customer for isolation testing."""
    import uuid
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"test2-{timestamp}-{uuid.uuid4().hex[:8]}@test.0711.io"
    customer_id = f"test2-{timestamp}-{uuid.uuid4().hex[:6]}"  # DNS-compliant (no underscores)

    return {
        "customer_id": customer_id,
        "email": email,
        "password": "TestPass456!",
        "company_name": f"Test Company 2 {timestamp}",
        "token": "mock_token_2_for_testing"
    }


@pytest.fixture
async def authenticated_api_client(
    api_client: httpx.AsyncClient,
    test_customer: dict
) -> httpx.AsyncClient:
    """API client with authentication headers."""
    api_client.headers.update({
        "Authorization": f"Bearer {test_customer['token']}"
    })
    return api_client


@pytest.fixture
async def authenticated_console_client(
    console_client: httpx.AsyncClient,
    test_customer: dict
) -> httpx.AsyncClient:
    """Console client with authentication headers."""
    console_client.headers.update({
        "Authorization": f"Bearer {test_customer['token']}"
    })
    return console_client


@pytest.fixture
async def test_minio_bucket(
    minio_client: Minio,
    test_customer: dict
) -> Generator[str, None, None]:
    """
    Create a test MinIO bucket for the customer.
    Cleans up after the test.
    """
    bucket_name = f"customer-{test_customer['customer_id']}"

    # Create bucket (bucket_name is now a keyword argument in MinIO 7.2+)
    if not minio_client.bucket_exists(bucket_name=bucket_name):
        minio_client.make_bucket(bucket_name=bucket_name)

    yield bucket_name

    # Cleanup: remove all objects and bucket
    try:
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            minio_client.remove_object(bucket_name, obj.object_name)
        minio_client.remove_bucket(bucket_name)
    except Exception as e:
        print(f"Warning: Failed to cleanup bucket {bucket_name}: {e}")


@pytest.fixture
def sample_pdf_file(test_data_dir: Path) -> Path:
    """Path to sample PDF file."""
    return test_data_dir / "sample_invoice.pdf"


@pytest.fixture
def sample_docx_file(test_data_dir: Path) -> Path:
    """Path to sample DOCX file."""
    return test_data_dir / "sample_contract.docx"


@pytest.fixture
def sample_csv_file(test_data_dir: Path) -> Path:
    """Path to sample CSV file."""
    return test_data_dir / "sample_tax_report.csv"


@pytest.fixture
def sample_unknown_file(test_data_dir: Path) -> Path:
    """Path to unknown format file (for Claude handler generation)."""
    return test_data_dir / "sample_unknown.dat"


@pytest.fixture(autouse=True)
def wait_for_services():
    """
    Wait for services to be ready before running tests.
    This runs automatically before each test.
    """
    # Check if we should skip service checks (for unit tests)
    if os.getenv("SKIP_SERVICE_CHECK", "false").lower() == "true":
        return

    # Give services a moment to be ready
    time.sleep(0.5)


def wait_for_service(url: str, timeout: int = 30, check_interval: float = 1.0) -> bool:
    """
    Wait for a service to become available.

    Args:
        url: URL to check (e.g., "http://localhost:4080/health")
        timeout: Maximum seconds to wait
        check_interval: Seconds between checks

    Returns:
        True if service is available, False if timeout
    """
    import httpx

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(check_interval)

    return False


@pytest.fixture(scope="session", autouse=True)
def check_test_services():
    """
    Check that all required services are running before test session.
    Runs once at the start of the test session.
    Also seeds test database if in test mode.
    """
    if os.getenv("SKIP_SERVICE_CHECK", "false").lower() == "true":
        return

    services = {
        "Control Plane API": f"{TEST_API_BASE}/health",
        "Console Backend": f"{TEST_CONSOLE_BASE}/health",
    }

    print("\n🔍 Checking test services...")
    for service_name, health_url in services.items():
        if wait_for_service(health_url, timeout=10):
            print(f"✓ {service_name} is ready")
        else:
            pytest.skip(f"{service_name} is not available at {health_url}")

    print("✓ All services ready\n")

    # Seed test database if in test mode
    if os.getenv("TESTING", "false").lower() == "true":
        print("🌱 Seeding test database...")
        try:
            import sys
            from pathlib import Path
            # Add parent to path for imports
            test_dir = Path(__file__).parent.parent
            if str(test_dir) not in sys.path:
                sys.path.insert(0, str(test_dir))

            from tests.fixtures.seed_test_users import seed_test_users
            seed_test_users(database_url=TEST_DB_URL)
            print("✓ Test users seeded\n")
        except Exception as e:
            print(f"⚠ Could not seed test users: {e}\n")
