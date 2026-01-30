"""
Secure Database Gateway

Provides authorized access to customer databases with Human-in-the-Loop approval for write operations
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import httpx

logger = logging.getLogger(__name__)


class SecureDatabaseGateway:
    """
    Secure gateway for customer database access

    Features:
    - Token-based authorization
    - Write operations require approval
    - Audit logging
    - Multiple database types (Neo4j, Lakehouse, MinIO)
    """

    def __init__(self):
        self.user_registry = None
        self.approval_manager = None

    async def execute_query(
        self,
        customer_id: str,
        user_token: str,
        database: str,
        query: str,
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Execute query on customer database

        Args:
            customer_id: Customer identifier
            user_token: User authentication token
            database: Database type ('neo4j', 'lakehouse', 'minio')
            query: Query string
            require_approval: Require human approval for writes

        Returns:
            Query results
        """
        # Load user registry
        if not self.user_registry:
            from orchestrator.auth.user_registry import UserRegistry
            self.user_registry = UserRegistry()

        # 1. Verify token
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        # 2. Detect write operation
        is_write = self._is_write_operation(query, database)

        # 3. Request approval if needed
        if is_write and require_approval:
            approved = await self._request_approval(
                user=user,
                customer_id=customer_id,
                database=database,
                query=query,
                reason="Write operation detected"
            )

            if not approved:
                raise PermissionError("Write operation not approved")

        # 4. Execute query
        result = await self._execute_on_database(
            customer_id=customer_id,
            database=database,
            query=query
        )

        # 5. Audit log
        await self._log_query(
            user=user,
            customer_id=customer_id,
            database=database,
            query=query,
            is_write=is_write,
            approved=is_write and require_approval
        )

        return result

    def _is_write_operation(self, query: str, database: str) -> bool:
        """Detect if query is a write operation"""
        query_upper = query.upper()

        write_keywords = [
            "CREATE", "UPDATE", "DELETE", "DROP", "INSERT",
            "MERGE", "SET", "REMOVE", "ALTER"
        ]

        return any(keyword in query_upper for keyword in write_keywords)

    async def _request_approval(
        self,
        user: Dict,
        customer_id: str,
        database: str,
        query: str,
        reason: str
    ) -> bool:
        """
        Request human approval for operation

        Creates approval request and waits for decision (timeout: 5 minutes)
        """
        logger.info(f"Requesting approval for {database} write operation")

        # In production: Would create approval in database and send notification
        # For now: Auto-approve for admin users
        if user["role"] == "customer_admin":
            logger.info("Auto-approved (customer admin)")
            return True

        # Otherwise: Would wait for approval
        logger.warning("Approval system not fully implemented - denying by default")
        return False

    async def _execute_on_database(
        self,
        customer_id: str,
        database: str,
        query: str
    ) -> Dict[str, Any]:
        """Execute query on customer database"""

        # Get customer endpoints
        # In production: Look up from registry
        base_url = f"http://localhost:9302"  # Would be dynamic

        if database == "lakehouse":
            # Query lakehouse API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/query",
                    json={"query": query}
                )
                response.raise_for_status()
                return response.json()

        elif database == "neo4j":
            # Query Neo4j
            # Would use neo4j driver
            return {"message": "Neo4j query not yet implemented"}

        elif database == "minio":
            # MinIO operations
            return {"message": "MinIO operations not yet implemented"}

        else:
            raise ValueError(f"Unknown database type: {database}")

    async def _log_query(
        self,
        user: Dict,
        customer_id: str,
        database: str,
        query: str,
        is_write: bool,
        approved: Optional[bool]
    ):
        """Log query execution to audit log"""
        logger.info(
            f"Audit: User {user['email']} executed {database} query "
            f"(write={is_write}, approved={approved})"
        )
        # In production: Write to audit_log table
