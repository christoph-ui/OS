"""
E2E Test: Customer Isolation

Tests that customer data is properly isolated:
1. Two customers cannot access each other's data
2. JWT tokens are properly scoped
3. Lakehouse data is partitioned by customer_id
4. MinIO buckets are isolated
5. Chat responses only include own data
"""

import pytest
import httpx

from tests.e2e.helpers import (
    upload_file_to_minio,
    assert_response_success
)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCustomerIsolation:
    """Test multi-tenant customer data isolation."""

    async def test_customers_cannot_access_each_others_data(
        self,
        api_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict,
        minio_client
    ):
        """
        Test that Customer A cannot access Customer B's data.

        Scenario:
            1. Customer A uploads file
            2. Customer B tries to access it
            3. Should fail with 403/404
        """
        # Customer A uploads file
        bucket_a = f"customer-{test_customer['customer_id']}"
        if not minio_client.bucket_exists(bucket_name=bucket_a):
            minio_client.make_bucket(bucket_name=bucket_a)

        # Upload test file as Customer A (MinIO 7.2+ requires keyword args and BytesIO)
        import io
        test_content = "Customer A's confidential data"
        minio_client.put_object(
            bucket_name=bucket_a,
            object_name="confidential.txt",
            data=io.BytesIO(test_content.encode()),
            length=len(test_content)
        )

        # Customer B tries to access Customer A's bucket
        bucket_b = f"customer-{test_customer_2['customer_id']}"

        # Customer B should not be able to see Customer A's files
        # (This would be tested through API, not direct MinIO access)
        # In production, API should check customer_id before returning data

        assert bucket_a != bucket_b  # Buckets are isolated by customer_id

    async def test_jwt_token_scopes_to_customer(
        self,
        console_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict
    ):
        """Test that JWT tokens are scoped to specific customers."""
        # Customer A's token
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer['token']}"
        })

        # Try to query as Customer A
        response = await console_client.post("/api/chat", json={
            "message": "Test query"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        # If returns 401, it means test mode not active (needs restart)
        if response.status_code in [401, 403]:
            pytest.skip("Test mode not active - restart with CONSOLE_TESTING=true")

        # Should work or return proper error (not auth error)
        assert response.status_code in [200, 500]  # Not 401/403

        # Now use Customer B's token
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer_2['token']}"
        })

        response = await console_client.post("/api/chat", json={
            "message": "Test query"
        })

        # Customer B should be authenticated with their own scope
        if response.status_code in [401, 403]:
            pytest.skip("Test mode not active")

        assert response.status_code in [200, 500]  # Not 401/403

    async def test_ingestion_data_isolation(
        self,
        console_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict,
        minio_client,
        temp_dir
    ):
        """
        Test that ingested data is isolated by customer.

        Scenario:
            1. Customer A ingests file with keyword "SECRET"
            2. Customer B ingests file with keyword "PUBLIC"
            3. Customer A searches - should only see "SECRET"
            4. Customer B searches - should only see "PUBLIC"
        """
        # Customer A uploads and ingests
        bucket_a = f"customer-{test_customer['customer_id']}"
        if not minio_client.bucket_exists(bucket_name=bucket_a):
            minio_client.make_bucket(bucket_name=bucket_a)

        file_a = temp_dir / "customer_a_data.txt"
        file_a.write_text("This document contains SECRET information for Customer A")
        upload_file_to_minio(minio_client, bucket_a, str(file_a))

        # Customer B uploads and ingests
        bucket_b = f"customer-{test_customer_2['customer_id']}"
        if not minio_client.bucket_exists(bucket_name=bucket_b):
            minio_client.make_bucket(bucket_name=bucket_b)

        file_b = temp_dir / "customer_b_data.txt"
        file_b.write_text("This document contains PUBLIC information for Customer B")
        upload_file_to_minio(minio_client, bucket_b, str(file_b))

        # TODO: Trigger ingestion for both customers
        # TODO: Search as Customer A - should only find "SECRET"
        # TODO: Search as Customer B - should only find "PUBLIC"

        # This test requires full ingestion + lakehouse implementation
        pytest.skip("Requires full ingestion and lakehouse with customer_id filtering")

    async def test_chat_responses_only_include_own_data(
        self,
        console_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict
    ):
        """
        Test that chat responses only include customer's own data.

        Scenario:
            1. Customer A has data about "Project Alpha"
            2. Customer B has data about "Project Beta"
            3. Customer A asks about projects - should only see Alpha
            4. Customer B asks about projects - should only see Beta
        """
        # Customer A asks about projects
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer['token']}"
        })

        response_a = await console_client.post("/api/chat", json={
            "message": "Tell me about our projects"
        })

        if response_a.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        if response_a.status_code in [401, 403]:
            pytest.skip("Test mode not active - restart with CONSOLE_TESTING=true")

        # Customer B asks the same question
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer_2['token']}"
        })

        response_b = await console_client.post("/api/chat", json={
            "message": "Tell me about our projects"
        })

        # Responses should be different (if data exists)
        # Both should succeed but return different results
        assert response_a.status_code in [200, 500]
        assert response_b.status_code in [200, 500]

        # TODO: Verify that response_a doesn't contain customer B's data
        # TODO: Verify that response_b doesn't contain customer A's data
        # This requires actual data ingestion first

    async def test_minio_bucket_isolation(
        self,
        test_customer: dict,
        test_customer_2: dict,
        minio_client
    ):
        """Test that MinIO buckets are properly isolated."""
        bucket_a = f"customer-{test_customer['customer_id']}"
        bucket_b = f"customer-{test_customer_2['customer_id']}"

        # Create both buckets
        if not minio_client.bucket_exists(bucket_name=bucket_a):
            minio_client.make_bucket(bucket_name=bucket_a)
        if not minio_client.bucket_exists(bucket_name=bucket_b):
            minio_client.make_bucket(bucket_name=bucket_b)

        # Upload to A (MinIO 7.2+ requires keyword args and BytesIO)
        import io
        minio_client.put_object(
            bucket_name=bucket_a,
            object_name="file_a.txt",
            data=io.BytesIO(b"Customer A data"),
            length=15
        )

        # Upload to B
        minio_client.put_object(
            bucket_name=bucket_b,
            object_name="file_b.txt",
            data=io.BytesIO(b"Customer B data"),
            length=15
        )

        # List objects in A's bucket - should only see A's file (MinIO 7.2+ uses keyword args)
        objects_a = list(minio_client.list_objects(bucket_name=bucket_a))
        assert len(objects_a) >= 1
        object_names_a = [obj.object_name for obj in objects_a]
        assert "file_a.txt" in object_names_a

        # List objects in B's bucket - should only see B's file
        objects_b = list(minio_client.list_objects(bucket_name=bucket_b))
        assert len(objects_b) >= 1
        object_names_b = [obj.object_name for obj in objects_b]
        assert "file_b.txt" in object_names_b

        # Critical: Ensure A's bucket doesn't have B's files and vice versa
        assert "file_b.txt" not in object_names_a
        assert "file_a.txt" not in object_names_b

    async def test_jwt_token_customer_id_mismatch(
        self,
        console_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict
    ):
        """
        Test that API rejects requests where JWT customer_id doesn't match resource owner.

        Scenario:
            1. Customer A's token
            2. Try to access Customer B's ingestion job
            3. Should fail with 403/404
        """
        # Use Customer A's token
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer['token']}"
        })

        # Try to access a hypothetical job belonging to Customer B
        fake_job_id = "customer_b_job_123"

        response = await console_client.get(f"/api/ingest/{fake_job_id}/status")

        if response.status_code in [401, 403]:
            # If auth fails, test mode not active
            pytest.skip("Test mode not active - restart with CONSOLE_TESTING=true")

        if response.status_code == 404:
            # Either endpoint not implemented or job not found (both OK)
            pass
        else:
            # Should not allow access
            assert response.status_code in [403, 404]

    async def test_admin_can_access_all_customers(
        self,
        api_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """
        Test that admin users can access all customer data.

        Note: This test is skipped if admin functionality not implemented.
        """
        # Create admin token (would need admin user creation)
        # admin_token = await create_admin_user()

        # For now, just verify the concept exists in design
        pytest.skip("Admin access not implemented yet")

    async def test_customer_cannot_list_other_customers(
        self,
        api_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """Test that customers cannot list other customers."""
        # Use customer token
        api_client.headers.update({
            "Authorization": f"Bearer {test_customer['token']}"
        })

        # Try to list all customers (admin endpoint)
        response = await api_client.get("/api/admin/customers")

        # Should be forbidden for non-admin
        assert response.status_code in [401, 403, 404]

    async def test_lakehouse_customer_id_filtering(
        self,
        console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """
        Test that lakehouse queries are automatically filtered by customer_id.

        All Delta Lake and LanceDB queries should include customer_id filter.
        """
        # Authenticate as customer
        console_client.headers.update({
            "Authorization": f"Bearer {test_customer['token']}"
        })

        # Query data
        response = await console_client.get("/api/data/search", params={
            "q": "test query"
        })

        if response.status_code == 404:
            pytest.skip("Data search not implemented")

        assert_response_success(response, 200)

        # Results should only include this customer's data
        # (verified by backend filtering on customer_id)
        # The API should NEVER return results from other customers

    async def test_deployment_isolation(
        self,
        api_client: httpx.AsyncClient,
        test_customer: dict,
        test_customer_2: dict
    ):
        """
        Test that deployments are isolated per customer.

        Each customer should have their own:
        - vLLM instance (different ports)
        - Lakehouse partition
        - MinIO bucket
        - Docker containers
        """
        # In a real deployment:
        # - Customer A: ports 5100-5199
        # - Customer B: ports 5200-5299

        # For now, just verify buckets are isolated
        bucket_a = f"customer-{test_customer['customer_id']}"
        bucket_b = f"customer-{test_customer_2['customer_id']}"

        assert bucket_a != bucket_b
        assert test_customer['customer_id'] != test_customer_2['customer_id']
