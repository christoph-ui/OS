"""
E2E Test Helpers

Utility functions for end-to-end testing.
"""

import time
import asyncio
from typing import Callable, Any, Optional
import httpx


async def poll_until(
    check_fn: Callable[[], Any],
    condition: Callable[[Any], bool],
    timeout: int = 60,
    interval: float = 1.0,
    error_message: str = "Timeout waiting for condition"
) -> Any:
    """
    Poll a function until a condition is met.

    Args:
        check_fn: Function to call repeatedly
        condition: Function that returns True when result is satisfactory
        timeout: Maximum seconds to wait
        interval: Seconds between checks
        error_message: Error message if timeout occurs

    Returns:
        The result that satisfied the condition

    Raises:
        TimeoutError: If condition not met within timeout

    Example:
        result = await poll_until(
            lambda: get_job_status(job_id),
            lambda status: status == "completed",
            timeout=30
        )
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = check_fn() if not asyncio.iscoroutinefunction(check_fn) else await check_fn()

        if condition(result):
            return result

        await asyncio.sleep(interval)

    raise TimeoutError(f"{error_message} (timeout after {timeout}s)")


async def wait_for_ingestion_complete(
    client: httpx.AsyncClient,
    job_id: str,
    timeout: int = 120
) -> dict:
    """
    Wait for an ingestion job to complete.

    Args:
        client: Authenticated HTTP client
        job_id: Ingestion job ID
        timeout: Maximum seconds to wait

    Returns:
        Final job status dict

    Raises:
        TimeoutError: If job doesn't complete in time
        RuntimeError: If job fails
    """
    async def check_status():
        response = await client.get(f"/api/ingest/{job_id}/status")
        if response.status_code == 200:
            return response.json()
        return None

    result = await poll_until(
        check_status,
        lambda status: status and status.get("status") in ["completed", "failed"],
        timeout=timeout,
        interval=2.0,
        error_message=f"Ingestion job {job_id} did not complete"
    )

    if result.get("status") == "failed":
        errors = result.get("errors", [])
        raise RuntimeError(f"Ingestion job failed: {errors}")

    return result


async def wait_for_deployment_ready(
    client: httpx.AsyncClient,
    deployment_id: str,
    timeout: int = 300
) -> dict:
    """
    Wait for a deployment to become active.

    Args:
        client: Authenticated HTTP client
        deployment_id: Deployment ID
        timeout: Maximum seconds to wait (default 5 minutes)

    Returns:
        Final deployment status dict
    """
    async def check_status():
        response = await client.get(f"/api/onboarding/status/{deployment_id}")
        if response.status_code == 200:
            return response.json()
        return None

    return await poll_until(
        check_status,
        lambda status: status and status.get("status") in ["complete", "active"],
        timeout=timeout,
        interval=5.0,
        error_message=f"Deployment {deployment_id} did not become ready"
    )


def upload_file_to_minio(
    minio_client,
    bucket_name: str,
    file_path: str,
    object_name: Optional[str] = None
) -> str:
    """
    Upload a file to MinIO.

    Args:
        minio_client: MinIO client instance
        bucket_name: Target bucket
        file_path: Path to local file
        object_name: Object name in bucket (defaults to filename)

    Returns:
        Object name in bucket
    """
    from pathlib import Path

    if object_name is None:
        object_name = Path(file_path).name

    # Ensure bucket exists (bucket_name is keyword arg in MinIO 7.2+)
    if not minio_client.bucket_exists(bucket_name=bucket_name):
        minio_client.make_bucket(bucket_name=bucket_name)

    # MinIO 7.2+ requires keyword arguments
    minio_client.fput_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=file_path
    )
    return object_name


async def send_chat_message(
    client: httpx.AsyncClient,
    message: str,
    mcp: Optional[str] = None,
    context: Optional[dict] = None
) -> dict:
    """
    Send a chat message and get response.

    Args:
        client: Authenticated HTTP client
        message: Chat message
        mcp: Specific MCP to use (or None for auto-routing)
        context: Additional context dict

    Returns:
        Chat response dict
    """
    payload = {
        "message": message,
        "mcp": mcp,
        "context": context
    }

    response = await client.post("/api/chat", json=payload)
    response.raise_for_status()
    return response.json()


async def verify_data_in_lakehouse(
    client: httpx.AsyncClient,
    query: str,
    expected_count: int = None
) -> dict:
    """
    Verify data exists in the lakehouse.

    Args:
        client: Authenticated HTTP client
        query: Search query or SQL
        expected_count: Expected number of results (optional)

    Returns:
        Query results dict
    """
    response = await client.get("/api/data/search", params={"q": query})
    response.raise_for_status()

    results = response.json()

    if expected_count is not None:
        actual_count = len(results.get("results", []))
        if actual_count != expected_count:
            raise AssertionError(
                f"Expected {expected_count} results, got {actual_count}"
            )

    return results


def assert_response_success(response: httpx.Response, expected_status: int = 200):
    """
    Assert HTTP response is successful.

    Args:
        response: HTTP response
        expected_status: Expected status code

    Raises:
        AssertionError: If response is not successful
    """
    if response.status_code != expected_status:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text

        raise AssertionError(
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {error_detail}"
        )


def assert_contains_keys(data: dict, keys: list, message: str = ""):
    """
    Assert dict contains all specified keys.

    Args:
        data: Dict to check
        keys: List of required keys
        message: Optional error message
    """
    missing = [k for k in keys if k not in data]
    if missing:
        msg = message or f"Missing keys: {missing}"
        raise AssertionError(msg)


def cleanup_test_customer(customer_id: str):
    """
    Clean up all resources for a test customer.

    Args:
        customer_id: Customer ID to clean up

    Note:
        This is a placeholder. In production, would need to:
        - Remove MinIO buckets
        - Delete lakehouse data
        - Remove database records
        - Stop Docker containers
    """
    # TODO: Implement cleanup
    pass
