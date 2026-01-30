"""
License Manager

Generates and validates license keys for MCP installations
"""
import hashlib
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LicenseManager:
    """Manages MCP license keys"""

    @staticmethod
    def generate_license_key(customer_id: str, mcp_name: str) -> str:
        """
        Generate license key for MCP installation

        Format: 0711-{SHA256_HASH[:32]}

        Args:
            customer_id: Customer identifier
            mcp_name: MCP name

        Returns:
            License key
        """
        data = f"{customer_id}:{mcp_name}:{time.time()}"
        hash_obj = hashlib.sha256(data.encode())
        key = f"0711-{hash_obj.hexdigest()[:32].upper()}"

        logger.info(f"Generated license key for {mcp_name} ({customer_id})")

        return key

    @staticmethod
    def validate_license_key(license_key: str, mcp_id: str) -> bool:
        """
        Validate license key format

        Args:
            license_key: License key to validate
            mcp_id: MCP ID

        Returns:
            True if valid format
        """
        # Basic validation
        if not license_key.startswith("0711-"):
            return False

        if len(license_key) != 37:  # 0711- + 32 chars
            return False

        # Would check against database in production
        return True

    @staticmethod
    def is_license_expired(license_key: str, expires_at: Optional[str]) -> bool:
        """
        Check if license is expired

        Args:
            license_key: License key
            expires_at: Expiration timestamp (ISO format)

        Returns:
            True if expired
        """
        if not expires_at:
            # No expiration
            return False

        from datetime import datetime
        expiration = datetime.fromisoformat(expires_at)

        return datetime.now() > expiration
