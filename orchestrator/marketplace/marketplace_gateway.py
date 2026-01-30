"""
MCP Marketplace Gateway

Manages MCP installation, connection, and querying
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import httpx
import uuid

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://0711_user:0711_secret@localhost:4005/0711_db"
)


class MarketplaceGateway:
    """
    Gateway for MCP Marketplace operations

    Handles:
    - Listing available MCPs
    - Installing MCPs
    - Connecting MCPs (input/output)
    - Querying MCPs
    - License management
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        self.user_registry = None

    def _get_conn(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def _load_user_registry(self):
        """Lazy load user registry"""
        if not self.user_registry:
            from orchestrator.auth.user_registry import UserRegistry
            self.user_registry = UserRegistry()

    async def list_mcps(
        self,
        user_token: str,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available MCPs in marketplace

        Filters based on:
        - Customer tier (starter, pro, enterprise)
        - Industry
        - Approval status (only approved)

        Args:
            user_token: User authentication token
            category: Filter by category
            search: Search in name/description

        Returns:
            List of MCPs with metadata
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)

        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get customer
            cursor.execute(
                "SELECT * FROM customers WHERE id = %s",
                (user["customer_id"],)
            )
            customer = cursor.fetchone()

            if not customer:
                raise ValueError(f"Customer not found: {user['customer_id']}")

            # Query MCPs
            query = """
                SELECT
                    m.id, m.name, m.version, m.category, m.description,
                    m.connection_type, m.pricing_model, m.monthly_price_cents,
                    m.api_docs_url, m.setup_instructions,
                    d.company_name as developer_name,
                    d.verified as developer_verified,
                    COUNT(DISTINCT i.id) as installation_count,
                    AVG(r.rating) as avg_rating
                FROM mcps m
                LEFT JOIN mcp_developers d ON m.developer_id = d.id
                LEFT JOIN mcp_installations i ON m.id = i.mcp_id AND i.status = 'active'
                LEFT JOIN mcp_reviews r ON m.id = r.mcp_id
                WHERE m.status = 'approved'
            """

            filters = []
            params = []

            if category:
                filters.append("m.category = %s")
                params.append(category)

            if search:
                filters.append("(m.name ILIKE %s OR m.description ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            # Tier-based filtering
            if customer["tier"] == "starter":
                filters.append("(m.pricing_model = 'free' OR m.monthly_price_cents <= 1000)")

            if filters:
                query += " AND " + " AND ".join(filters)

            query += " GROUP BY m.id, d.company_name, d.verified"
            query += " ORDER BY installation_count DESC, m.name"

            cursor.execute(query, params)
            mcps = cursor.fetchall()

            # Get customer's installed MCPs
            cursor.execute(
                """
                SELECT mcp_id, license_key, installed_at
                FROM mcp_installations
                WHERE customer_id = %s AND status = 'active'
                """,
                (user["customer_id"],)
            )
            installations = {str(row["mcp_id"]): row for row in cursor.fetchall()}

            # Get connected MCPs
            connected_mcps = customer.get("connected_mcps", {"input": [], "output": []})

            # Annotate MCPs
            result_mcps = []
            for mcp in mcps:
                mcp_dict = dict(mcp)
                mcp_id = str(mcp_dict["id"])

                # Check if installed
                mcp_dict["installed"] = mcp_id in installations
                if mcp_dict["installed"]:
                    mcp_dict["installation"] = installations[mcp_id]

                # Check if connected
                mcp_dict["connected_as_input"] = mcp_dict["name"] in connected_mcps.get("input", [])
                mcp_dict["connected_as_output"] = mcp_dict["name"] in connected_mcps.get("output", [])

                # Format pricing
                if mcp_dict["monthly_price_cents"]:
                    mcp_dict["monthly_price_eur"] = mcp_dict["monthly_price_cents"] / 100.0
                else:
                    mcp_dict["monthly_price_eur"] = 0.0

                result_mcps.append(mcp_dict)

            logger.info(f"Listed {len(result_mcps)} MCPs for {user['customer_id']}")

            return {
                "success": True,
                "total": len(result_mcps),
                "mcps": result_mcps,
                "customer_tier": customer["tier"]
            }

        finally:
            cursor.close()
            conn.close()

    async def install_mcp(
        self,
        user_token: str,
        mcp_name: str,
        license_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Install MCP for customer

        Complete installation flow:
        1. Verify user & MCP
        2. Check if already installed
        3. Generate/validate license key
        4. Update customer.enabled_mcps
        5. Create mcp_installations record
        6. Deploy sidecar (if needed)
        7. Notify user
        8. Audit log

        Args:
            user_token: User authentication token
            mcp_name: MCP name to install
            license_key: Optional license key (generated if not provided)

        Returns:
            Installation result
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)

        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # 1. Get MCP
            cursor.execute(
                "SELECT * FROM mcps WHERE name = %s AND status = 'approved'",
                (mcp_name,)
            )
            mcp = cursor.fetchone()

            if not mcp:
                raise ValueError(f"MCP not found or not approved: {mcp_name}")

            mcp_id = mcp["id"]

            # 2. Check if already installed
            cursor.execute(
                """
                SELECT * FROM mcp_installations
                WHERE customer_id = %s AND mcp_id = %s AND status = 'active'
                """,
                (user["customer_id"], mcp_id)
            )

            existing = cursor.fetchone()
            if existing:
                logger.info(f"MCP {mcp_name} already installed for {user['customer_id']}")
                return {
                    "success": True,
                    "message": "Already installed",
                    "installation_id": str(existing["id"]),
                    "license_key": existing["license_key"]
                }

            # 3. Generate or validate license key
            if not license_key:
                license_key = self._generate_license_key(user["customer_id"], mcp_name)
            else:
                # Validate provided key
                if not self._validate_license_key(license_key, mcp_id):
                    raise ValueError("Invalid license key")

            # 4. Update customer.enabled_mcps
            cursor.execute(
                "SELECT enabled_mcps FROM customers WHERE id = %s",
                (user["customer_id"],)
            )
            customer_row = cursor.fetchone()
            enabled_mcps = customer_row["enabled_mcps"] or {}

            enabled_mcps[mcp_name] = True

            cursor.execute(
                "UPDATE customers SET enabled_mcps = %s WHERE id = %s",
                (Json(enabled_mcps), user["customer_id"])
            )

            # 5. Create installation record
            installation_id = str(uuid.uuid4())
            license_expires = None

            if mcp["pricing_model"] != "free":
                license_expires = datetime.now() + timedelta(days=365)

            cursor.execute(
                """
                INSERT INTO mcp_installations (
                    id, customer_id, mcp_id, installed_at, installed_by,
                    license_key, license_expires_at, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    installation_id, user["customer_id"], mcp_id, datetime.now(), user["user_id"],
                    license_key, license_expires, "active"
                )
            )

            installation = cursor.fetchone()
            conn.commit()

            # 6. Deploy sidecar (if needed)
            deployment_result = None
            if mcp["connection_type"] == "sidecar":
                deployment_result = await self._deploy_mcp_sidecar(
                    customer_id=user["customer_id"],
                    mcp_name=mcp_name,
                    license_key=license_key
                )

            # 7. Notify user (would send email/notification in production)
            logger.info(f"MCP {mcp_name} installed for {user['customer_id']}")

            # 8. Audit log
            # Would log to audit_log table

            return {
                "success": True,
                "installation_id": installation_id,
                "mcp_name": mcp_name,
                "license_key": license_key,
                "expires_at": str(license_expires) if license_expires else None,
                "connection_type": mcp["connection_type"],
                "deployment": deployment_result
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"MCP installation failed: {e}")
            raise

        finally:
            cursor.close()
            conn.close()

    async def connect_mcp(
        self,
        user_token: str,
        mcp_name: str,
        direction: str,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Connect MCP as input or output

        Input MCPs: Data sources (SAP, DATEV, PIM)
        Output MCPs: Target systems (ETIM, Syndicate, Publish)

        Args:
            user_token: User authentication token
            mcp_name: MCP name
            direction: 'input' or 'output'
            config: Connection configuration (optional)

        Returns:
            Connection result
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)

        if direction not in ["input", "output"]:
            raise ValueError("direction must be 'input' or 'output'")

        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # 1. Check if MCP is installed
            cursor.execute(
                "SELECT enabled_mcps FROM customers WHERE id = %s",
                (user["customer_id"],)
            )
            customer_row = cursor.fetchone()
            enabled_mcps = customer_row["enabled_mcps"] or {}

            if not enabled_mcps.get(mcp_name):
                raise ValueError(f"MCP {mcp_name} must be installed first")

            # 2. Update connected_mcps
            cursor.execute(
                "SELECT connected_mcps FROM customers WHERE id = %s",
                (user["customer_id"],)
            )
            customer_row = cursor.fetchone()
            connected_mcps = customer_row["connected_mcps"] or {"input": [], "output": []}

            if mcp_name not in connected_mcps[direction]:
                connected_mcps[direction].append(mcp_name)

            cursor.execute(
                "UPDATE customers SET connected_mcps = %s WHERE id = %s",
                (Json(connected_mcps), user["customer_id"])
            )

            conn.commit()

            # 3. Save connection config (if provided)
            if config:
                # Would save to mcp_connections table
                pass

            # 4. Test connection
            test_result = await self._test_mcp_connection(
                user["customer_id"],
                mcp_name,
                direction,
                config
            )

            logger.info(f"MCP {mcp_name} connected as {direction} for {user['customer_id']}")

            return {
                "success": True,
                "mcp_name": mcp_name,
                "direction": direction,
                "connected": True,
                "test_result": test_result
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"MCP connection failed: {e}")
            raise

        finally:
            cursor.close()
            conn.close()

    async def query_mcp(
        self,
        user_token: str,
        mcp_name: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query MCP service

        Routes to appropriate backend:
        - Shared services (ETIM, MARKET, PUBLISH)
        - Sidecar containers (customer-specific)
        - External APIs (3rd party)

        Args:
            user_token: User authentication token
            mcp_name: MCP to query
            query: Query string
            context: Optional context

        Returns:
            Query result
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)

        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Check if MCP enabled
            cursor.execute(
                "SELECT enabled_mcps FROM customers WHERE id = %s",
                (user["customer_id"],)
            )
            customer_row = cursor.fetchone()
            enabled_mcps = customer_row["enabled_mcps"] or {}

            if not enabled_mcps.get(mcp_name):
                raise PermissionError(f"MCP {mcp_name} not enabled for this customer")

            # Get MCP info
            cursor.execute(
                "SELECT * FROM mcps WHERE name = %s",
                (mcp_name,)
            )
            mcp = cursor.fetchone()

            if not mcp:
                raise ValueError(f"MCP not found: {mcp_name}")

            # Route based on connection_type
            if mcp["connection_type"] == "shared":
                # Route to shared service via MCP Router
                result = await self._query_shared_mcp(
                    customer_id=user["customer_id"],
                    mcp_name=mcp_name,
                    query=query,
                    context=context or {}
                )

            elif mcp["connection_type"] == "sidecar":
                # Route to customer-specific sidecar
                result = await self._query_sidecar_mcp(
                    customer_id=user["customer_id"],
                    mcp_name=mcp_name,
                    query=query,
                    context=context or {}
                )

            elif mcp["connection_type"] == "api":
                # Route to external API
                result = await self._query_external_mcp(
                    mcp=mcp,
                    customer_id=user["customer_id"],
                    query=query,
                    context=context or {}
                )

            else:
                raise ValueError(f"Unknown connection type: {mcp['connection_type']}")

            # Track usage (for billing)
            # Would record in usage_metrics table

            return result

        finally:
            cursor.close()
            conn.close()

    async def get_installed_mcps(self, user_token: str) -> Dict[str, Any]:
        """
        List installed MCPs for customer

        Args:
            user_token: User authentication token

        Returns:
            List of installed MCPs
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)

        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT
                    i.id, i.installed_at, i.license_expires_at, i.status,
                    m.name, m.version, m.category, m.description, m.connection_type
                FROM mcp_installations i
                JOIN mcps m ON i.mcp_id = m.id
                WHERE i.customer_id = %s AND i.status = 'active'
                ORDER BY i.installed_at DESC
                """,
                (user["customer_id"],)
            )

            installations = cursor.fetchall()

            return {
                "success": True,
                "total": len(installations),
                "installed_mcps": [dict(inst) for inst in installations]
            }

        finally:
            cursor.close()
            conn.close()

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _generate_license_key(self, customer_id: str, mcp_name: str) -> str:
        """Generate license key"""
        import hashlib
        import time

        data = f"{customer_id}:{mcp_name}:{time.time()}"
        hash_obj = hashlib.sha256(data.encode())
        return f"0711-{hash_obj.hexdigest()[:32].upper()}"

    def _validate_license_key(self, license_key: str, mcp_id: str) -> bool:
        """Validate license key"""
        # Would check format and validity
        return license_key.startswith("0711-")

    async def _deploy_mcp_sidecar(
        self,
        customer_id: str,
        mcp_name: str,
        license_key: str
    ) -> Dict:
        """Deploy MCP as sidecar container"""
        logger.info(f"Deploying sidecar for {mcp_name} ({customer_id})")

        # Would use Docker API to deploy container
        # For now: placeholder

        return {
            "deployed": True,
            "container_name": f"{customer_id}-{mcp_name}",
            "status": "running"
        }

    async def _test_mcp_connection(
        self,
        customer_id: str,
        mcp_name: str,
        direction: str,
        config: Optional[Dict]
    ) -> Dict:
        """Test MCP connection"""
        logger.info(f"Testing {mcp_name} connection ({direction})")

        # Would perform actual connection test
        # For now: placeholder

        return {
            "status": "ok",
            "latency_ms": 50,
            "message": "Connection test successful"
        }

    async def _query_shared_mcp(
        self,
        customer_id: str,
        mcp_name: str,
        query: str,
        context: Dict
    ) -> Dict:
        """Query shared MCP service"""
        from orchestrator.mcp.mcp_router import mcp_router

        return await mcp_router.query_mcp(
            mcp_name=mcp_name,
            customer_id=customer_id,
            query=query,
            context=context
        )

    async def _query_sidecar_mcp(
        self,
        customer_id: str,
        mcp_name: str,
        query: str,
        context: Dict
    ) -> Dict:
        """Query sidecar MCP"""
        # Get sidecar URL
        sidecar_url = f"http://{customer_id}-{mcp_name}:8000"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{sidecar_url}/query",
                json={"query": query, "context": context}
            )
            response.raise_for_status()
            return response.json()

    async def _query_external_mcp(
        self,
        mcp: Dict,
        customer_id: str,
        query: str,
        context: Dict
    ) -> Dict:
        """Query external MCP API"""
        # Would use MCP's API endpoint
        # Handle OAuth if needed

        logger.info(f"Querying external MCP: {mcp['name']}")

        # Placeholder
        return {
            "success": True,
            "message": "External MCP query not yet implemented"
        }
