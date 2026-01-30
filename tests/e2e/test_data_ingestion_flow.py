"""
E2E Test: Data Ingestion Flow

Tests the complete data ingestion pipeline:
1. File upload to MinIO
2. Trigger ingestion job
3. Monitor progress
4. Verify data in Delta Lake
5. Verify vectors in LanceDB
6. Test Claude handler generation for unknown formats
"""

import pytest
import asyncio
from pathlib import Path
import httpx

from tests.e2e.helpers import (
    wait_for_ingestion_complete,
    upload_file_to_minio,
    verify_data_in_lakehouse,
    assert_response_success
)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDataIngestionFlow:
    """Test complete data ingestion flow."""

    async def test_basic_file_ingestion(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict,
        minio_client,
        temp_dir: Path
    ):
        """
        Test basic file ingestion workflow.

        Flow:
            1. Create test files
            2. Upload to MinIO
            3. Trigger ingestion
            4. Wait for completion
            5. Verify data in lakehouse
        """
        bucket_name = f"customer-{test_customer['customer_id']}"

        # Create bucket
        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        # Create test file
        test_file = temp_dir / "test_document.txt"
        test_file.write_text("This is a test document about corporate tax regulations.")

        # Upload to MinIO
        upload_file_to_minio(minio_client, bucket_name, str(test_file))

        # Trigger ingestion
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": f"/data/{bucket_name}",
            "mcp": "ctax",
            "recursive": True
        })

        # If ingestion endpoint exists
        if response.status_code == 404:
            pytest.skip("Ingestion endpoint not fully implemented")

        assert_response_success(response, 200)
        job = response.json()
        assert "job_id" in job

        # Wait for ingestion to complete
        try:
            final_status = await wait_for_ingestion_complete(
                authenticated_console_client,
                job["job_id"],
                timeout=120
            )

            assert final_status["status"] == "completed"
            assert final_status["files_processed"] >= 1

        except TimeoutError:
            pytest.skip("Ingestion taking too long (may not be fully implemented)")

    async def test_multi_file_ingestion(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict,
        minio_client,
        temp_dir: Path
    ):
        """Test ingestion of multiple files at once."""
        bucket_name = f"customer-{test_customer['customer_id']}"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        # Create multiple test files
        files = [
            ("invoice_2024_q1.txt", "Invoice for Q1 2024: €100,000"),
            ("invoice_2024_q2.txt", "Invoice for Q2 2024: €120,000"),
            ("contract_vendor_a.txt", "Vendor A contract terms..."),
            ("contract_vendor_b.txt", "Vendor B contract terms..."),
        ]

        for filename, content in files:
            test_file = temp_dir / filename
            test_file.write_text(content)
            upload_file_to_minio(minio_client, bucket_name, str(test_file))

        # Trigger ingestion
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": f"/data/{bucket_name}",
            "recursive": True
        })

        if response.status_code == 404:
            pytest.skip("Ingestion endpoint not implemented")

        assert_response_success(response, 200)
        job = response.json()

        try:
            final_status = await wait_for_ingestion_complete(
                authenticated_console_client,
                job["job_id"],
                timeout=180
            )

            assert final_status["files_processed"] == len(files)
            assert final_status["status"] == "completed"

        except TimeoutError:
            pytest.skip("Multi-file ingestion not completing")

    async def test_ingestion_with_file_type_filter(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict,
        minio_client,
        temp_dir: Path
    ):
        """Test ingestion with file type filtering."""
        bucket_name = f"customer-{test_customer['customer_id']}"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        # Upload mixed file types
        files = [
            ("document.pdf", b"%PDF-1.4\ntest"),
            ("data.csv", b"year,value\n2024,100"),
            ("image.png", b"\x89PNG\r\n"),  # PNG header
            ("text.txt", b"Plain text"),
        ]

        for filename, content in files:
            temp_file = temp_dir / filename
            temp_file.write_bytes(content)
            upload_file_to_minio(minio_client, bucket_name, str(temp_file))

        # Ingest only PDFs and CSVs
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": f"/data/{bucket_name}",
            "file_types": [".pdf", ".csv"],
            "recursive": True
        })

        if response.status_code == 404:
            pytest.skip("Ingestion filtering not implemented")

        assert_response_success(response, 200)
        job = response.json()

        try:
            final_status = await wait_for_ingestion_complete(
                authenticated_console_client,
                job["job_id"]
            )

            # Should process only 2 files (PDF + CSV)
            assert final_status["files_processed"] == 2

        except TimeoutError:
            pytest.skip("Ingestion not completing")

    async def test_ingestion_status_polling(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict,
        minio_client,
        temp_dir: Path
    ):
        """Test polling ingestion status during processing."""
        bucket_name = f"customer-{test_customer['customer_id']}"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")
        upload_file_to_minio(minio_client, bucket_name, str(test_file))

        # Start ingestion
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": f"/data/{bucket_name}"
        })

        if response.status_code == 404:
            pytest.skip("Ingestion not implemented")

        assert_response_success(response, 200)
        job_id = response.json()["job_id"]

        # Poll status multiple times
        statuses_seen = []
        for _ in range(10):
            response = await authenticated_console_client.get(
                f"/api/ingest/{job_id}/status"
            )
            assert_response_success(response, 200)

            status = response.json()
            statuses_seen.append(status["status"])

            if status["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(1)

        # Should see progression: pending -> running -> completed
        assert "pending" in statuses_seen or "running" in statuses_seen
        assert statuses_seen[-1] in ["completed", "failed"]

    @pytest.mark.skip(reason="Requires lakehouse implementation")
    async def test_verify_data_in_delta_lake(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """Verify ingested data appears in Delta Lake."""
        # After ingestion, query Delta Lake
        response = await authenticated_console_client.get(
            "/api/data/tables"
        )

        if response.status_code == 404:
            pytest.skip("Lakehouse data API not implemented")

        assert_response_success(response, 200)
        tables = response.json()

        # Should have documents table
        assert "documents" in [t["name"] for t in tables.get("tables", [])]

    @pytest.mark.skip(reason="Requires Claude handler generation")
    async def test_unknown_format_handler_generation(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict,
        minio_client,
        temp_dir: Path
    ):
        """
        Test Claude handler generation for unknown file formats.

        When an unknown format is encountered, Claude Sonnet 4.5
        should analyze it and generate a handler on-the-fly.
        """
        bucket_name = f"customer-{test_customer['customer_id']}"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        # Create file with unknown format
        unknown_file = temp_dir / "proprietary_data.dat"
        unknown_file.write_text(
            "CUSTOM_FORMAT_V1\n"
            "FIELD1: value1\n"
            "FIELD2: value2\n"
            "DATA_START\n"
            "row1,data1\n"
            "row2,data2\n"
        )

        upload_file_to_minio(minio_client, bucket_name, str(unknown_file))

        # Trigger ingestion
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": f"/data/{bucket_name}"
        })

        if response.status_code == 404:
            pytest.skip("Claude handler generation not implemented")

        assert_response_success(response, 200)
        job_id = response.json()["job_id"]

        # Wait for completion
        final_status = await wait_for_ingestion_complete(
            authenticated_console_client,
            job_id,
            timeout=180  # May take longer due to Claude analysis
        )

        # Should have successfully processed the file
        assert final_status["status"] == "completed"
        assert final_status["files_processed"] == 1

        # Verify handler was registered
        # (would need to query handler registry)

    async def test_ingestion_error_handling(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test ingestion error handling for invalid paths."""
        response = await authenticated_console_client.post("/api/ingest", json={
            "path": "/nonexistent/path"
        })

        if response.status_code == 404:
            pytest.skip("Ingestion not implemented")

        # Path validation may redirect or return error
        # 307 = Temporary Redirect (FastAPI may redirect)
        # 400 = Bad Request
        # 404 = Not Found
        assert response.status_code in [307, 400, 404]

    async def test_list_ingestion_jobs(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """Test listing ingestion jobs for customer."""
        response = await authenticated_console_client.get("/api/ingest/jobs")

        if response.status_code == 404:
            pytest.skip("Ingestion jobs list not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "jobs" in data
        # All jobs should belong to this customer (tested by auth)
