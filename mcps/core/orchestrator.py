"""
Orchestrator MCP - Central Brain of 0711 Platform

This MCP orchestrates all platform services:
- Initial customer deployment via Cradle
- Incremental updates via MCP Central
- Database access with authorization
- MCP Marketplace management
- Intelligence layer (change detection)
- Continuous learning (V2)

Author: 0711 Intelligence
Version: 1.0.0
"""
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
import asyncio
import httpx

from mcps.sdk.base_mcp import BaseMCP, MCPContext
from mcps.sdk.types import MCPMetadata, TaskInput, TaskOutput

logger = logging.getLogger(__name__)


class OrchestratorMCP(BaseMCP):
    """
    Central Orchestrator MCP

    Connects:
    - Cradle (GPU Processing for initial deployment)
    - MCP Central (Stateless services for updates)
    - Customer Docker Instances (Data persistence)
    - MCP Marketplace (Install, Connect, Query)
    """

    # Metadata
    metadata = MCPMetadata(
        id="orchestrator",
        name="0711 Orchestrator",
        version="1.0.0",
        category="platform",
        description="Central orchestration for all platform services",
        author="0711 Intelligence",
        tools=[
            "initialize_customer",
            "process_new_documents",
            "generate_embeddings",
            "extract_vision",
            "query_customer_database",
            "list_marketplace_mcps",
            "install_mcp",
            "connect_mcp",
            "query_mcp",
            "get_data_changes",
            "offer_service"
        ],
        automation_rate=95.0
    )

    def __init__(self):
        super().__init__()

        # Service clients (lazy loaded)
        self._user_registry = None
        self._db_gateway = None
        self._marketplace = None
        self._change_detector = None
        self._cradle_client = None
        self._installation_db = None

        logger.info("Orchestrator MCP initialized")

    @property
    def user_registry(self):
        """Lazy load user registry"""
        if self._user_registry is None:
            from orchestrator.auth.user_registry import UserRegistry
            self._user_registry = UserRegistry()
        return self._user_registry

    @property
    def db_gateway(self):
        """Lazy load database gateway"""
        if self._db_gateway is None:
            from orchestrator.database_gateway import SecureDatabaseGateway
            self._db_gateway = SecureDatabaseGateway()
        return self._db_gateway

    @property
    def marketplace(self):
        """Lazy load marketplace gateway"""
        if self._marketplace is None:
            from orchestrator.marketplace.marketplace_gateway import MarketplaceGateway
            self._marketplace = MarketplaceGateway()
        return self._marketplace

    @property
    def change_detector(self):
        """Lazy load change detector"""
        if self._change_detector is None:
            from orchestrator.intelligence.change_detector import DataChangeDetector
            self._change_detector = DataChangeDetector()
        return self._change_detector

    @property
    def cradle_client(self):
        """Lazy load cradle client"""
        if self._cradle_client is None:
            from orchestrator.cradle.cradle_client import CradleClient
            self._cradle_client = CradleClient()
        return self._cradle_client

    @property
    def installation_db(self):
        """Lazy load installation DB client"""
        if self._installation_db is None:
            from orchestrator.cradle.installation_db_client import InstallationDBClient
            self._installation_db = InstallationDBClient()
        return self._installation_db

    # =========================================================================
    # MAIN PROCESS METHOD (Required by BaseMCP)
    # =========================================================================

    async def process(self, task: TaskInput, ctx: MCPContext) -> TaskOutput:
        """
        Main processing method

        Routes tasks to appropriate handlers
        """
        task_type = task.task_type

        handlers = {
            "initialize_customer": self._handle_initialize_customer,
            "process_new_documents": self._handle_process_new_documents,
            "query_database": self._handle_query_database,
            "install_mcp": self._handle_install_mcp,
            "query_mcp": self._handle_query_mcp,
        }

        handler = handlers.get(task_type)
        if not handler:
            return TaskOutput(
                success=False,
                confidence=0.0,
                data={},
                errors=[f"Unknown task type: {task_type}"]
            )

        try:
            result = await handler(task.data, ctx)
            return TaskOutput(
                success=True,
                confidence=95.0,
                data=result,
                model_used="orchestrator-v1.0"
            )
        except Exception as e:
            logger.error(f"Task processing failed: {e}", exc_info=True)
            return TaskOutput(
                success=False,
                confidence=0.0,
                data={},
                errors=[str(e)]
            )

    # =========================================================================
    # INITIAL DEPLOYMENT TOOLS
    # =========================================================================

    async def initialize_customer(
        self,
        company_name: str,
        contact_email: str,
        data_sources: List[str],
        deployment_target: str = "on-premise",
        mcps: Optional[List[str]] = None,
        installation_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initialize customer deployment via Cradle

        Complete onboarding flow:
        1. Create 0711 User Account
        2. Upload data to Cradle staging
        3. Process with GPU (embeddings, vision, graph)
        4. Save installation parameters
        5. Build Docker image
        6. Deploy to target
        7. Archive initial image
        8. Cleanup staging

        Args:
            company_name: Company name
            contact_email: Primary contact email
            data_sources: List of data source paths
            deployment_target: 'on-premise', 'cloud', or 'hybrid'
            mcps: List of MCPs to enable
            installation_params: Processing configuration

        Returns:
            Deployment information
        """
        logger.info(f"Initializing customer: {company_name}")

        customer_id = company_name.lower().replace(" ", "-")
        mcps = mcps or ["ctax", "law"]
        installation_params = installation_params or {}

        try:
            # 1. Create 0711 User
            logger.info("Creating 0711 user account...")
            user = await self.user_registry.create_user(
                customer_id=customer_id,
                email=contact_email,
                full_name=f"{company_name} Admin",
                role="customer_admin",
                created_via="cradle_deployment"
            )
            user_id = user["id"]
            user_token = user["token"]

            logger.info(f"✓ User created: {user_id}")

            # 2. Upload data to Cradle staging
            logger.info("Uploading data to Cradle staging...")
            staging_path = await self.cradle_client.upload_to_staging(
                customer_id=customer_id,
                data_sources=data_sources
            )

            logger.info(f"✓ Data uploaded to {staging_path}")

            # 3. Process with GPU
            logger.info("Processing data with Cradle GPU services...")

            # Default installation params
            default_params = {
                "embedding_model": "intfloat/multilingual-e5-large",
                "embedding_batch_size": 128,
                "embedding_normalize": True,
                "vision_enabled": True,
                "vision_model": "microsoft/Florence-2-large",
                "chunking_strategy": "structure-aware",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "graph_extraction_enabled": True,
                "graph_entity_types": ["company", "person", "product", "location"],
                "graph_relationship_threshold": 0.7
            }

            # Merge with provided params
            processing_config = {**default_params, **installation_params}

            # Process data
            processing_result = await self.cradle_client.process_customer_data(
                customer_id=customer_id,
                staging_path=staging_path,
                config=processing_config
            )

            logger.info(f"✓ Processing complete: {processing_result['stats']}")

            # 4. Save installation parameters
            logger.info("Saving installation parameters...")
            config_saved = await self.installation_db.save_config(
                customer_id=customer_id,
                company_name=company_name,
                contact_email=contact_email,
                user_id=user_id,
                deployment_target=deployment_target,
                processing_config=processing_config,
                initial_stats=processing_result["stats"],
                enabled_mcps=mcps
            )

            logger.info("✓ Installation parameters saved")

            # 5. Build Docker image
            logger.info("Building Docker image...")
            image_result = await self.cradle_client.build_customer_image(
                customer_id=customer_id,
                data_path=processing_result["output_path"],
                version="1.0"
            )

            logger.info(f"✓ Docker image built: {image_result['image_name']}")

            # 6. Deploy to target
            logger.info(f"Deploying to {deployment_target}...")
            deployment_result = await self._deploy_customer(
                customer_id=customer_id,
                image_path=image_result["image_tar"],
                deployment_target=deployment_target
            )

            logger.info(f"✓ Deployment complete")

            # 7. Archive initial image
            logger.info("Archiving initial image...")
            archive_path = await self._archive_initial_image(
                customer_id=customer_id,
                image_tar=image_result["image_tar"],
                manifest=image_result["manifest"]
            )

            logger.info(f"✓ Initial image archived: {archive_path}")

            # 8. Cleanup staging
            logger.info("Cleaning up staging area...")
            await self.cradle_client.cleanup_staging(staging_path)

            logger.info("✓ Staging cleaned up")

            # Success!
            return {
                "success": True,
                "customer_id": customer_id,
                "user_id": user_id,
                "user_token": user_token,
                "deployment": deployment_result,
                "stats": processing_result["stats"],
                "image_archive": archive_path,
                "enabled_mcps": mcps
            }

        except Exception as e:
            logger.error(f"Customer initialization failed: {e}", exc_info=True)
            raise

    async def _handle_initialize_customer(self, data: Dict, ctx: MCPContext) -> Dict:
        """Handler for initialize_customer task"""
        return await self.initialize_customer(
            company_name=data["company_name"],
            contact_email=data["contact_email"],
            data_sources=data["data_sources"],
            deployment_target=data.get("deployment_target", "on-premise"),
            mcps=data.get("mcps"),
            installation_params=data.get("installation_params")
        )

    async def _deploy_customer(
        self,
        customer_id: str,
        image_path: Path,
        deployment_target: str
    ) -> Dict:
        """Deploy customer Docker image"""

        if deployment_target == "on-premise":
            # Load image and start containers
            deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")
            deployment_dir.mkdir(parents=True, exist_ok=True)

            # Load Docker image
            import subprocess
            subprocess.run(["docker", "load", "-i", str(image_path)], check=True)

            # Copy docker-compose.yml
            compose_source = image_path.parent / "docker-compose.yml"
            compose_dest = deployment_dir / "docker-compose.yml"

            import shutil
            shutil.copy(compose_source, compose_dest)

            # Copy .env
            env_source = image_path.parent / ".env"
            env_dest = deployment_dir / ".env"
            shutil.copy(env_source, env_dest)

            # Start containers
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=deployment_dir,
                check=True
            )

            return {
                "deployment_dir": str(deployment_dir),
                "status": "running",
                "endpoints": {
                    "neo4j": f"neo4j://localhost:7687",
                    "lakehouse": f"http://localhost:9302",
                    "minio": f"http://localhost:9000",
                    "console": f"http://localhost:4020"
                }
            }

        elif deployment_target == "cloud":
            # Would deploy to Kubernetes/Cloud
            raise NotImplementedError("Cloud deployment not yet implemented")

        else:
            raise ValueError(f"Unknown deployment target: {deployment_target}")

    async def _archive_initial_image(
        self,
        customer_id: str,
        image_tar: Path,
        manifest: Dict
    ) -> Path:
        """Archive initial Docker image (NEVER DELETE!)"""

        # Versions directory
        versions_dir = Path(f"/home/christoph.bertsch/0711/docker-images/versions/{customer_id}")
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Copy image
        import shutil
        archive_tar = versions_dir / "v1.0-init.tar"
        shutil.copy(image_tar, archive_tar)

        # Save manifest
        import json
        manifest_path = versions_dir / "v1.0-init.manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        logger.info(f"Initial image archived: {archive_tar} (NEVER DELETE!)")

        return archive_tar

    # =========================================================================
    # INCREMENTAL UPDATE TOOLS
    # =========================================================================

    async def process_new_documents(
        self,
        customer_id: str,
        user_token: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Process new documents using MCP Central services

        Flow:
        1. Customer uploads files to Docker (MinIO)
        2. Local file crawler + chunking
        3. Call MCP Central for embeddings
        4. Store in LanceDB
        5. Update stats

        Args:
            customer_id: Customer identifier
            user_token: User authentication token
            file_paths: List of file paths in customer Docker

        Returns:
            Processing results
        """
        logger.info(f"Processing {len(file_paths)} new documents for {customer_id}")

        try:
            # Verify user
            user = await self.user_registry.verify_token(user_token)
            if user["customer_id"] != customer_id:
                raise PermissionError("Token does not match customer")

            # Get installation config (for consistent processing)
            config = await self.installation_db.get_config(customer_id)
            if not config:
                raise ValueError(f"No configuration found for {customer_id}")

            # Process documents
            results = []

            for file_path in file_paths:
                logger.info(f"Processing: {file_path}")

                # 1. Extract text (local in customer Docker)
                # In production: Call customer Docker API
                text_content = await self._extract_file_content(customer_id, file_path)

                # 2. Chunk text
                chunks = await self._chunk_text(
                    text_content,
                    strategy=config["chunking_config"]["strategy"],
                    chunk_size=config["chunking_config"]["chunk_size"]
                )

                # 3. Generate embeddings (via MCP Central)
                embeddings = await self._generate_embeddings_via_central(
                    customer_id=customer_id,
                    texts=chunks
                )

                # 4. Store in customer lakehouse
                await self._store_in_lakehouse(
                    customer_id=customer_id,
                    file_path=file_path,
                    chunks=chunks,
                    embeddings=embeddings
                )

                results.append({
                    "file_path": file_path,
                    "chunks_created": len(chunks),
                    "embeddings_generated": len(embeddings),
                    "status": "success"
                })

            logger.info(f"✓ Processed {len(results)} documents")

            return {
                "success": True,
                "customer_id": customer_id,
                "processed_files": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Document processing failed: {e}", exc_info=True)
            raise

    async def _handle_process_new_documents(self, data: Dict, ctx: MCPContext) -> Dict:
        """Handler for process_new_documents task"""
        return await self.process_new_documents(
            customer_id=data["customer_id"],
            user_token=data["user_token"],
            file_paths=data["file_paths"]
        )

    async def _extract_file_content(self, customer_id: str, file_path: str) -> str:
        """Extract content from file in customer Docker"""
        # In production: Call customer Docker API
        # For now: Placeholder
        return f"Content of {file_path}"

    async def _chunk_text(self, text: str, strategy: str, chunk_size: int) -> List[str]:
        """Chunk text using specified strategy"""
        # Simple implementation
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks

    async def _generate_embeddings_via_central(
        self,
        customer_id: str,
        texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings via MCP Central"""

        mcp_central_url = "http://localhost:4090"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{mcp_central_url}/api/embeddings/generate",
                json={
                    "texts": texts,
                    "customer_id": customer_id
                }
            )
            response.raise_for_status()
            data = response.json()

            return data["embeddings"]

    async def _store_in_lakehouse(
        self,
        customer_id: str,
        file_path: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """Store chunks and embeddings in customer lakehouse"""
        # In production: Call customer lakehouse API
        logger.info(f"Storing {len(chunks)} chunks in {customer_id} lakehouse")
        pass

    async def generate_embeddings(
        self,
        customer_id: str,
        user_token: str,
        texts: List[str]
    ) -> Dict[str, Any]:
        """
        Generate embeddings via MCP Central

        Uses saved installation parameters for consistency
        """
        # Verify user
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        # Generate
        embeddings = await self._generate_embeddings_via_central(customer_id, texts)

        return {
            "success": True,
            "embeddings": embeddings,
            "total": len(embeddings),
            "model": "multilingual-e5-large"
        }

    async def extract_vision(
        self,
        customer_id: str,
        user_token: str,
        image_paths: List[str],
        task: str = "ocr"
    ) -> Dict[str, Any]:
        """
        Extract text/info from images via MCP Central Vision service

        Args:
            customer_id: Customer identifier
            user_token: User token
            image_paths: List of image paths
            task: Vision task ('ocr', 'caption', 'object_detection')
        """
        # Verify user
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        mcp_central_url = "http://localhost:4090"
        results = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            for image_path in image_paths:
                # Read image from customer Docker
                # In production: Call customer API
                # For now: placeholder

                response = await client.post(
                    f"{mcp_central_url}/api/vision/process",
                    json={
                        "image_base64": "...",  # Would be actual image
                        "task": task,
                        "customer_id": customer_id
                    }
                )
                response.raise_for_status()

                results.append({
                    "image_path": image_path,
                    "result": response.json()
                })

        return {
            "success": True,
            "results": results,
            "total": len(results)
        }

    # =========================================================================
    # DATABASE ACCESS TOOLS
    # =========================================================================

    async def query_customer_database(
        self,
        customer_id: str,
        user_token: str,
        database: str,
        query: str,
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Query customer database with authorization

        Args:
            customer_id: Customer identifier
            user_token: User token
            database: Database type ('neo4j', 'lakehouse', 'minio')
            query: Query string
            require_approval: Require human approval for writes

        Returns:
            Query results
        """
        return await self.db_gateway.execute_query(
            customer_id=customer_id,
            user_token=user_token,
            database=database,
            query=query,
            require_approval=require_approval
        )

    async def _handle_query_database(self, data: Dict, ctx: MCPContext) -> Dict:
        """Handler for query_database task"""
        return await self.query_customer_database(
            customer_id=data["customer_id"],
            user_token=data["user_token"],
            database=data["database"],
            query=data["query"],
            require_approval=data.get("require_approval", True)
        )

    # =========================================================================
    # MCP MARKETPLACE TOOLS
    # =========================================================================

    async def list_marketplace_mcps(
        self,
        user_token: str,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available MCPs in marketplace

        Returns MCPs based on customer tier and industry
        """
        return await self.marketplace.list_mcps(
            user_token=user_token,
            category=category,
            search=search
        )

    async def install_mcp(
        self,
        user_token: str,
        mcp_name: str,
        license_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Install MCP for customer

        Flow:
        1. Validate user & MCP
        2. Generate/validate license key
        3. Update customer.enabled_mcps
        4. Create installation record
        5. Deploy (if sidecar MCP)
        6. Notify user
        """
        return await self.marketplace.install_mcp(
            user_token=user_token,
            mcp_name=mcp_name,
            license_key=license_key
        )

    async def _handle_install_mcp(self, data: Dict, ctx: MCPContext) -> Dict:
        """Handler for install_mcp task"""
        return await self.install_mcp(
            user_token=data["user_token"],
            mcp_name=data["mcp_name"],
            license_key=data.get("license_key")
        )

    async def connect_mcp(
        self,
        user_token: str,
        mcp_name: str,
        direction: str,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Connect MCP as input or output

        Args:
            user_token: User token
            mcp_name: MCP name
            direction: 'input' or 'output'
            config: Connection configuration
        """
        return await self.marketplace.connect_mcp(
            user_token=user_token,
            mcp_name=mcp_name,
            direction=direction,
            config=config
        )

    async def query_mcp(
        self,
        user_token: str,
        mcp_name: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query MCP service

        Routes to:
        - Shared services (ETIM, MARKET)
        - Sidecar containers
        - External APIs
        """
        return await self.marketplace.query_mcp(
            user_token=user_token,
            mcp_name=mcp_name,
            query=query,
            context=context or {}
        )

    async def _handle_query_mcp(self, data: Dict, ctx: MCPContext) -> Dict:
        """Handler for query_mcp task"""
        return await self.query_mcp(
            user_token=data["user_token"],
            mcp_name=data["mcp_name"],
            query=data["query"],
            context=data.get("context")
        )

    # =========================================================================
    # INTELLIGENCE LAYER TOOLS
    # =========================================================================

    async def get_data_changes(
        self,
        customer_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Detect data changes since last check

        Returns change statistics and service offers
        """
        return await self.change_detector.detect_changes(
            customer_id=customer_id,
            user_token=user_token
        )

    async def offer_service(
        self,
        customer_id: str,
        user_token: str,
        service_type: str,
        details: Dict
    ) -> Dict[str, Any]:
        """
        Offer GPU service proactively

        Args:
            customer_id: Customer identifier
            user_token: User token
            service_type: 'embeddings', 'vision', 'training'
            details: Service details (cost, duration, benefits)
        """
        return await self.change_detector.offer_service(
            customer_id=customer_id,
            user_token=user_token,
            service_type=service_type,
            details=details
        )

    # =========================================================================
    # RESOURCE METHODS (Read-only data access)
    # =========================================================================

    async def get_customer_stats(self, customer_id: str, user_token: str) -> Dict:
        """Get customer statistics from Docker instance"""

        # Verify user
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        # Call customer Docker stats API
        docker_url = f"http://localhost:9302"  # Would be dynamic

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{docker_url}/stats")
            response.raise_for_status()
            return response.json()

    async def get_installation_config(self, customer_id: str) -> Dict:
        """Load installation configuration from Cradle DB"""
        return await self.installation_db.get_config(customer_id)

    async def get_installed_mcps(self, user_token: str) -> Dict:
        """List installed MCPs for customer"""
        return await self.marketplace.get_installed_mcps(user_token)

    async def list_customer_deployments(self) -> List[Dict]:
        """List all active customer deployments"""
        # Would query deployment registry
        deployments_dir = Path("/home/christoph.bertsch/0711/deployments")

        if not deployments_dir.exists():
            return []

        deployments = []
        for customer_dir in deployments_dir.iterdir():
            if customer_dir.is_dir() and customer_dir.name != "archives":
                deployments.append({
                    "customer_id": customer_dir.name,
                    "deployment_dir": str(customer_dir),
                    "status": "active"  # Would check Docker containers
                })

        return deployments


# Export
__all__ = ["OrchestratorMCP"]
