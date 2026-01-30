"""
Customer Deployment Registry

Maps customer_id to their deployed containers for routing.
Loads from database and caches for performance.
"""

import logging
from typing import Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from core.paths import CustomerPaths

logger = logging.getLogger(__name__)


@dataclass
class CustomerDeployment:
    """Customer deployment information"""
    customer_id: str
    deployment_id: str
    status: str

    # Service URLs (customer-specific containers)
    vllm_url: str
    lakehouse_url: str
    embeddings_url: str

    # Paths (for local deployments)
    lakehouse_path: Optional[Path] = None
    lora_path: Optional[Path] = None

    # Metadata
    enabled_mcps: list = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.enabled_mcps is None:
            self.enabled_mcps = []
        if isinstance(self.lakehouse_path, str):
            self.lakehouse_path = Path(self.lakehouse_path)
        if isinstance(self.lora_path, str):
            self.lora_path = Path(self.lora_path)


class CustomerRegistry:
    """
    Registry of customer deployments.

    Provides:
    - Lookup customer → container URLs
    - Cache for performance (avoid DB queries on every request)
    - Support for both managed and self-hosted deployments

    Usage:
        registry = CustomerRegistry()
        await registry.initialize()

        deployment = registry.get_deployment("eaton")
        print(deployment.vllm_url)  # http://localhost:9300
    """

    def __init__(self):
        self._deployments: Dict[str, CustomerDeployment] = {}  # UUID → deployment
        self._by_name: Dict[str, str] = {}  # name → UUID mapping
        self._cache_ttl = timedelta(minutes=5)
        self._last_refresh: Optional[datetime] = None
        self._initialized = False

    async def initialize(self):
        """Initialize registry by loading deployments from database"""
        if self._initialized:
            return

        await self.refresh()
        self._initialized = True
        logger.info(f"Customer registry initialized with {len(self._deployments)} deployments")

    async def refresh(self):
        """Refresh deployments from database"""
        try:
            # Import here to avoid circular imports
            from sqlalchemy import create_engine, select
            from sqlalchemy.orm import Session
            from api.models.deployment import Deployment
            from api.config import settings

            # Create engine (use same DB as Control Plane)
            engine = create_engine(settings.database_url)

            with Session(engine) as session:
                # Query all active deployments with customer info
                from api.models.customer import Customer

                stmt = select(Deployment, Customer).join(
                    Customer, Deployment.customer_id == Customer.id
                ).where(
                    Deployment.status.in_(["active", "provisioning"])
                )
                results = session.execute(stmt).all()

                # Load into registry
                for deployment, customer in results:
                    customer_uuid = str(deployment.customer_id)

                    # Get customer name for lookups (normalize)
                    full_name = customer.company_name.lower().replace(" ", "-")

                    # Create short alias (first word only)
                    # "Eaton Industries GmbH" → alias="eaton"
                    short_alias = full_name.split("-")[0] if "-" in full_name else full_name

                    # Parse deployment metadata to get URLs
                    # Port allocation based on short alias (matches actual deployments)
                    base_port = self._get_base_port(short_alias)

                    customer_deployment = CustomerDeployment(
                        customer_id=short_alias,  # Use short alias
                        deployment_id=str(deployment.id),
                        status=deployment.status,
                        vllm_url=f"http://localhost:{base_port}",
                        lakehouse_url=f"http://localhost:{base_port + 2}",
                        embeddings_url=f"http://localhost:{base_port + 1}",
                        lakehouse_path=CustomerPaths.get_lakehouse_path(short_alias),
                        lora_path=CustomerPaths.get_lora_path(short_alias),
                        enabled_mcps=deployment.mcps_enabled or [],
                        created_at=deployment.created_at
                    )

                    # Store by UUID, full name, and short alias
                    self._deployments[customer_uuid] = customer_deployment
                    self._deployments[full_name] = customer_deployment
                    self._deployments[short_alias] = customer_deployment
                    self._by_name[full_name] = customer_uuid
                    self._by_name[short_alias] = customer_uuid

                    logger.debug(f"Loaded deployment for {short_alias} (full: {full_name}, UUID: {customer_uuid[:8]}...)")

            self._last_refresh = datetime.utcnow()
            logger.info(f"Refreshed {len(self._deployments)} customer deployments from database")

        except Exception as e:
            logger.error(f"Error refreshing customer registry: {e}", exc_info=True)

        # Always scan filesystem for additional deployments (supplements database)
        self._load_from_filesystem()

    def _load_from_filesystem(self):
        """Fallback: Load deployments from filesystem (for dev mode)"""
        logger.info("Loading deployments from filesystem (fallback mode)")

        # Check for known deployments
        deployments_path = Path("/home/christoph.bertsch/0711/deployments")
        if not deployments_path.exists():
            logger.warning(f"Deployments path not found: {deployments_path}")
            return

        # Scan for customer directories
        for customer_dir in deployments_path.iterdir():
            if not customer_dir.is_dir():
                continue

            customer_id = customer_dir.name

            # Check if docker-compose exists
            compose_file = customer_dir / "docker-compose.yml"
            if not compose_file.exists():
                continue

            # Parse actual ports from docker-compose.yml
            import yaml
            try:
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)

                # Extract ports from services
                services = compose_data.get('services', {})
                vllm_ports = services.get('vllm', {}).get('ports', [])
                lakehouse_ports = services.get('lakehouse', {}).get('ports', [])
                embeddings_ports = services.get('embeddings', {}).get('ports', [])

                # Parse port mappings (format: "9200:8000" or "- 9200:8000")
                def parse_port(port_entry):
                    if isinstance(port_entry, str):
                        return int(port_entry.split(':')[0])
                    return None

                vllm_port = parse_port(vllm_ports[0]) if vllm_ports else None
                lakehouse_port = parse_port(lakehouse_ports[0]) if lakehouse_ports else None
                embeddings_port = parse_port(embeddings_ports[0]) if embeddings_ports else None

                # Fallback to calculated port if not found
                if not vllm_port or not lakehouse_port or not embeddings_port:
                    base_port = self._get_base_port(customer_id)
                    vllm_port = vllm_port or base_port
                    embeddings_port = embeddings_port or (base_port + 1)
                    lakehouse_port = lakehouse_port or (base_port + 2)

            except Exception as e:
                logger.warning(f"Failed to parse ports from {compose_file}: {e}")
                # Fallback to calculated ports
                base_port = self._get_base_port(customer_id)
                vllm_port = base_port
                embeddings_port = base_port + 1
                lakehouse_port = base_port + 2

            deployment = CustomerDeployment(
                customer_id=customer_id,
                deployment_id=f"{customer_id}-local",
                status="active",
                vllm_url=f"http://localhost:{vllm_port}",
                lakehouse_url=f"http://localhost:{lakehouse_port}",
                embeddings_url=f"http://localhost:{embeddings_port}",
                lakehouse_path=CustomerPaths.get_lakehouse_path(customer_id),
                lora_path=CustomerPaths.get_lora_path(customer_id),
                enabled_mcps=["ctax", "law", "etim"],  # Default
            )

            self._deployments[customer_id] = deployment
            logger.info(f"Loaded deployment for {customer_id} from filesystem (vLLM:{vllm_port}, Lakehouse:{lakehouse_port})")

    def _get_base_port(self, customer_id: str) -> int:
        """
        Get base port for customer using same algorithm as deployment_orchestrator.

        Each customer gets 100-port block:
        - EATON: hash("eaton") % 50 * 100 + 5000 = 9300
        - e-ProCat: Different hash
        """
        # Known customer port mappings (match actual deployments)
        known_ports = {
            "eaton": 9300,
            "e-procat": 9400,
        }

        if customer_id.lower() in known_ports:
            return known_ports[customer_id.lower()]

        # Hash-based allocation for unknown customers
        base_port = 5000 + (hash(customer_id) % 50) * 100
        return base_port

    def get_deployment(self, customer_id: str) -> Optional[CustomerDeployment]:
        """
        Get deployment for customer.

        Args:
            customer_id: Customer ID

        Returns:
            CustomerDeployment or None if not found
        """
        # Check cache expiration
        if self._last_refresh and datetime.utcnow() - self._last_refresh > self._cache_ttl:
            # Refresh in background (don't block request)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.refresh())
                else:
                    asyncio.run(self.refresh())
            except:
                pass  # Ignore refresh errors, use cached data

        deployment = self._deployments.get(customer_id)

        if not deployment:
            logger.warning(f"No deployment found for customer: {customer_id}")

        return deployment

    def list_deployments(self) -> list[CustomerDeployment]:
        """List all deployments"""
        return list(self._deployments.values())

    def has_deployment(self, customer_id: str) -> bool:
        """Check if customer has deployment"""
        return customer_id in self._deployments

    def get_lakehouse_url(self, customer_id: str) -> Optional[str]:
        """Get lakehouse URL for customer"""
        deployment = self.get_deployment(customer_id)
        return deployment.lakehouse_url if deployment else None

    def get_vllm_url(self, customer_id: str) -> Optional[str]:
        """Get vLLM URL for customer"""
        deployment = self.get_deployment(customer_id)
        return deployment.vllm_url if deployment else None

    def get_embeddings_url(self, customer_id: str) -> Optional[str]:
        """Get embeddings URL for customer"""
        deployment = self.get_deployment(customer_id)
        return deployment.embeddings_url if deployment else None


# Global registry instance
_registry: Optional[CustomerRegistry] = None


def get_registry() -> CustomerRegistry:
    """Get global customer registry instance"""
    global _registry
    if _registry is None:
        _registry = CustomerRegistry()
    return _registry


async def initialize_registry():
    """Initialize global registry"""
    registry = get_registry()
    await registry.initialize()
    return registry
