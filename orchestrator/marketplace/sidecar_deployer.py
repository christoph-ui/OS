"""
Sidecar Deployer

Deploys MCP sidecars as Docker containers alongside customer deployment
"""
import logging
from typing import Dict, Any
import subprocess
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class SidecarDeployer:
    """Deploys MCP sidecars"""

    async def deploy_sidecar(
        self,
        customer_id: str,
        mcp_name: str,
        mcp_config: Dict[str, Any],
        license_key: str
    ) -> Dict[str, Any]:
        """
        Deploy MCP as sidecar container

        Creates a new container in customer's Docker network

        Args:
            customer_id: Customer identifier
            mcp_name: MCP name
            mcp_config: MCP configuration
            license_key: License key

        Returns:
            Deployment result
        """
        logger.info(f"Deploying sidecar: {mcp_name} for {customer_id}")

        container_name = f"{customer_id}-{mcp_name}"

        # Get deployment directory
        deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")

        if not deployment_dir.exists():
            raise ValueError(f"Customer deployment not found: {customer_id}")

        # Read existing docker-compose.yml
        compose_file = deployment_dir / "docker-compose.yml"

        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)

        # Add sidecar service
        sidecar_service = {
            "image": mcp_config.get("docker_image", f"0711/{mcp_name}:latest"),
            "container_name": container_name,
            "environment": [
                f"LICENSE_KEY={license_key}",
                f"CUSTOMER_ID={customer_id}",
                f"MCP_NAME={mcp_name}"
            ],
            "networks": [f"{customer_id}-network"],
            "restart": "unless-stopped"
        }

        # Add volumes if specified
        if "volumes" in mcp_config:
            sidecar_service["volumes"] = mcp_config["volumes"]

        # Add ports if specified
        if "ports" in mcp_config:
            sidecar_service["ports"] = mcp_config["ports"]

        # Add to compose
        compose["services"][mcp_name] = sidecar_service

        # Write updated compose
        with open(compose_file, 'w') as f:
            yaml.dump(compose, f, default_flow_style=False)

        # Start sidecar
        try:
            subprocess.run(
                ["docker-compose", "up", "-d", mcp_name],
                cwd=deployment_dir,
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"✓ Sidecar deployed: {container_name}")

            return {
                "success": True,
                "container_name": container_name,
                "status": "running"
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Sidecar deployment failed: {e.stderr}")
            raise

    async def remove_sidecar(
        self,
        customer_id: str,
        mcp_name: str
    ) -> bool:
        """
        Remove sidecar container

        Args:
            customer_id: Customer identifier
            mcp_name: MCP name

        Returns:
            True if removed successfully
        """
        logger.info(f"Removing sidecar: {mcp_name} for {customer_id}")

        deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")
        container_name = f"{customer_id}-{mcp_name}"

        try:
            # Stop and remove container
            subprocess.run(
                ["docker-compose", "stop", mcp_name],
                cwd=deployment_dir,
                check=True
            )

            subprocess.run(
                ["docker-compose", "rm", "-f", mcp_name],
                cwd=deployment_dir,
                check=True
            )

            # Update docker-compose.yml
            compose_file = deployment_dir / "docker-compose.yml"

            with open(compose_file, 'r') as f:
                compose = yaml.safe_load(f)

            # Remove service
            if mcp_name in compose["services"]:
                del compose["services"][mcp_name]

                with open(compose_file, 'w') as f:
                    yaml.dump(compose, f, default_flow_style=False)

            logger.info(f"✓ Sidecar removed: {container_name}")

            return True

        except Exception as e:
            logger.error(f"Sidecar removal failed: {e}")
            return False
