"""
License service for generating and validating license keys
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class LicenseService:
    """License key generation and validation service"""

    @classmethod
    def generate_license_key(
        cls,
        customer_id: str,
        plan: str,
        duration_days: int = 365
    ) -> str:
        """
        Generate a license key for a customer

        Format: 0711-XXXX-XXXX-XXXX-XXXX
        Where XXXX are groups of 4 alphanumeric characters

        Args:
            customer_id: Customer UUID
            plan: Plan name (starter, professional, business, enterprise)
            duration_days: License duration in days

        Returns:
            License key string
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(16)

        # Create deterministic component from customer_id and plan
        deterministic = f"{customer_id}:{plan}".encode()
        hash_bytes = hashlib.sha256(deterministic).digest()[:4]

        # Combine random and deterministic parts
        combined = random_bytes + hash_bytes

        # Convert to base32 (readable characters)
        import base64
        encoded = base64.b32encode(combined).decode()

        # Format as 0711-XXXX-XXXX-XXXX-XXXX
        # Take 16 characters and split into 4 groups
        key_part = encoded[:16]
        formatted = f"0711-{key_part[0:4]}-{key_part[4:8]}-{key_part[8:12]}-{key_part[12:16]}"

        logger.info(f"Generated license key for customer {customer_id} ({plan})")
        return formatted

    @classmethod
    def calculate_expiration(
        cls,
        plan: str,
        start_date: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate license expiration date based on plan

        Args:
            plan: Plan name
            start_date: Start date (defaults to now)

        Returns:
            Expiration datetime
        """
        if start_date is None:
            start_date = datetime.utcnow()

        if plan == "starter":
            # Free plan: 30 days renewable
            return start_date + timedelta(days=30)
        elif plan in ["professional", "business", "enterprise"]:
            # Paid plans: 1 year
            return start_date + timedelta(days=365)
        else:
            raise ValueError(f"Unknown plan: {plan}")

    @classmethod
    def validate_license_format(cls, license_key: str) -> bool:
        """
        Validate license key format

        Args:
            license_key: License key to validate

        Returns:
            True if format is valid
        """
        # Check format: 0711-XXXX-XXXX-XXXX-XXXX
        if not license_key:
            return False

        parts = license_key.split("-")
        if len(parts) != 5:
            return False

        if parts[0] != "0711":
            return False

        # Check each part is 4 alphanumeric characters
        for part in parts[1:]:
            if len(part) != 4 or not part.isalnum():
                return False

        return True

    @classmethod
    def is_license_expired(cls, expiration_date: datetime) -> bool:
        """
        Check if a license is expired

        Args:
            expiration_date: License expiration date

        Returns:
            True if expired
        """
        return datetime.utcnow() > expiration_date

    @classmethod
    def days_until_expiration(cls, expiration_date: datetime) -> int:
        """
        Calculate days until license expiration

        Args:
            expiration_date: License expiration date

        Returns:
            Number of days (negative if expired)
        """
        delta = expiration_date - datetime.utcnow()
        return delta.days
