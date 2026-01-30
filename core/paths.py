"""
Customer Data Paths Resolver

CRITICAL: Centralized path management to prevent /tmp disasters.

RULES:
- NEVER use /tmp for persistent data (embeddings, Delta tables, LoRAs)
- ALWAYS use Docker volumes for managed deployments
- ALWAYS use /var/lib/0711 for self-hosted deployments
- Use this module EVERYWHERE - no hardcoded paths allowed

History:
- 2026-01-11: Created to fix /tmp/lakehouse disaster (data lost on reboot)
"""

from pathlib import Path
from typing import Literal, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Deployment types
DeploymentType = Literal["managed", "self_hosted", "development"]


class CustomerPaths:
    """
    Centralized path resolver for customer data.

    Ensures all persistent data uses proper storage:
    - Managed (Docker): Uses Docker volumes mounted at /data/*
    - Self-hosted: Uses /var/lib/0711/* (persistent across reboots)
    - Development: Uses local ./data/* for testing

    NEVER returns /tmp paths for persistent data.
    """

    # Base paths by deployment type
    BASE_PATHS = {
        "managed": {
            "lakehouse": Path("/data/lakehouse"),
            "loras": Path("/data/loras"),
            "uploads": Path("/data/uploads"),
        },
        "self_hosted": {
            "lakehouse": Path(os.getenv("LAKEHOUSE_BASE", "/var/lib/0711/lakehouse")),
            "loras": Path(os.getenv("LORA_BASE", "/var/lib/0711/loras")),
            "uploads": Path(os.getenv("UPLOAD_BASE", "/var/lib/0711/uploads")),
        },
        "development": {
            "lakehouse": Path(os.getenv("LAKEHOUSE_BASE", "./data/lakehouse")),
            "loras": Path(os.getenv("LORA_BASE", "./data/loras")),
            "uploads": Path(os.getenv("UPLOAD_BASE", "./data/uploads")),
        }
    }

    @classmethod
    def get_deployment_type(cls) -> DeploymentType:
        """
        Detect deployment type from environment.

        Returns:
            Deployment type (managed, self_hosted, or development)
        """
        deployment_type = os.getenv("DEPLOYMENT_TYPE", "").lower()

        if deployment_type in ["managed", "self_hosted", "development"]:
            return deployment_type

        # Auto-detect based on environment
        if os.path.exists("/.dockerenv"):
            return "managed"
        elif os.path.exists("/var/lib/0711"):
            return "self_hosted"
        else:
            return "development"

    @classmethod
    def get_lakehouse_path(
        cls,
        customer_id: str,
        deployment_type: Optional[DeploymentType] = None
    ) -> Path:
        """
        Get persistent lakehouse path for customer.

        Lakehouse stores:
        - Delta Lake tables (documents, chunks)
        - LanceDB vector embeddings
        - Metadata and indices

        Args:
            customer_id: Customer identifier
            deployment_type: Override deployment type (default: auto-detect)

        Returns:
            Absolute path to customer lakehouse

        Example:
            >>> CustomerPaths.get_lakehouse_path("eaton")
            Path("/data/lakehouse")  # Inside container with Docker volume

        Note:
            For managed deployments, returns container-internal path.
            Docker volumes handle external persistence.
        """
        if deployment_type is None:
            deployment_type = cls.get_deployment_type()

        base = cls.BASE_PATHS[deployment_type]["lakehouse"]

        # For managed deployments, lakehouse is per-container (Docker volume)
        # For self-hosted/dev, lakehouse is per-customer subdirectory
        if deployment_type == "managed":
            return base
        else:
            customer_path = base / customer_id
            customer_path.mkdir(parents=True, exist_ok=True)
            return customer_path

    @classmethod
    def get_lora_path(
        cls,
        customer_id: str,
        deployment_type: Optional[DeploymentType] = None
    ) -> Path:
        """
        Get persistent LoRA adapters path for customer.

        LoRA path stores fine-tuned model adapters.

        Args:
            customer_id: Customer identifier
            deployment_type: Override deployment type

        Returns:
            Absolute path to customer LoRA adapters
        """
        if deployment_type is None:
            deployment_type = cls.get_deployment_type()

        base = cls.BASE_PATHS[deployment_type]["loras"]

        if deployment_type == "managed":
            return base
        else:
            customer_path = base / customer_id
            customer_path.mkdir(parents=True, exist_ok=True)
            return customer_path

    @classmethod
    def get_upload_path(
        cls,
        customer_id: str,
        deployment_type: Optional[DeploymentType] = None
    ) -> Path:
        """
        Get upload staging path for customer.

        This is for temporary file storage during ingestion.
        Can use /tmp since it's truly ephemeral.

        Args:
            customer_id: Customer identifier
            deployment_type: Override deployment type

        Returns:
            Path to upload staging area
        """
        if deployment_type is None:
            deployment_type = cls.get_deployment_type()

        base = cls.BASE_PATHS[deployment_type]["uploads"]

        upload_path = base / customer_id
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    @classmethod
    def get_temp_path(cls, customer_id: str, prefix: str = "temp") -> Path:
        """
        Get temporary path for ephemeral data.

        THIS IS THE ONLY METHOD THAT CAN RETURN /tmp PATHS.
        Use only for truly temporary data that can be lost.

        Args:
            customer_id: Customer identifier
            prefix: Prefix for temp directory name

        Returns:
            Temporary path (WILL BE DELETED on reboot)
        """
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}_{customer_id}_"))
        logger.debug(f"Created temp directory (ephemeral): {temp_dir}")
        return temp_dir

    @classmethod
    def validate_path_safety(cls, path: Path) -> bool:
        """
        Validate that path is safe for persistent data.

        Args:
            path: Path to validate

        Returns:
            True if safe, False if using /tmp
        """
        path_str = str(path.resolve())

        if path_str.startswith("/tmp/"):
            logger.error(
                f"UNSAFE PATH DETECTED: {path} uses /tmp for persistent data! "
                "This will be lost on reboot. Use CustomerPaths.get_lakehouse_path() instead."
            )
            return False

        return True

    @classmethod
    def get_all_customer_paths(cls, customer_id: str) -> dict:
        """
        Get all paths for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            Dictionary with all path types
        """
        deployment_type = cls.get_deployment_type()

        return {
            "deployment_type": deployment_type,
            "customer_id": customer_id,
            "lakehouse": cls.get_lakehouse_path(customer_id, deployment_type),
            "loras": cls.get_lora_path(customer_id, deployment_type),
            "uploads": cls.get_upload_path(customer_id, deployment_type),
        }


# Convenience function for backward compatibility
def get_customer_lakehouse_path(customer_id: str) -> Path:
    """
    Get lakehouse path for customer (backward compatibility).

    Deprecated: Use CustomerPaths.get_lakehouse_path() instead.
    """
    return CustomerPaths.get_lakehouse_path(customer_id)


__all__ = ["CustomerPaths", "DeploymentType", "get_customer_lakehouse_path"]
