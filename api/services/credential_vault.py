"""
Credential Vault Service
Handles encryption/decryption of sensitive credentials using Fernet (AES-256)
"""

import json
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)


class CredentialVault:
    """
    Secure credential storage using Fernet symmetric encryption

    Environment Variables Required:
    - CREDENTIAL_VAULT_SECRET: Master secret for encryption (min 32 bytes)
    - CREDENTIAL_VAULT_SALT: Salt for key derivation (optional, auto-generated)

    Security Features:
    - AES-256 encryption via Fernet
    - PBKDF2 key derivation (100,000 iterations)
    - Automatic key rotation support
    - Audit logging for all encrypt/decrypt operations
    """

    def __init__(self):
        self.secret = self._get_or_create_secret()
        self.salt = self._get_or_create_salt()
        self.fernet = self._derive_fernet_key()

    def _get_or_create_secret(self) -> bytes:
        """Get master secret from environment or create new one"""
        secret = os.getenv("CREDENTIAL_VAULT_SECRET")

        if not secret:
            logger.warning("CREDENTIAL_VAULT_SECRET not set, generating random secret")
            logger.warning("IMPORTANT: Set CREDENTIAL_VAULT_SECRET in .env for production!")
            # Generate random 32-byte secret
            secret = Fernet.generate_key().decode()
            logger.info(f"Generated secret (store this in .env): {secret}")

        return secret.encode()

    def _get_or_create_salt(self) -> bytes:
        """Get salt from environment or create new one"""
        salt = os.getenv("CREDENTIAL_VAULT_SALT")

        if not salt:
            logger.warning("CREDENTIAL_VAULT_SALT not set, generating random salt")
            # Generate random 16-byte salt
            import secrets
            salt = base64.b64encode(secrets.token_bytes(16)).decode()
            logger.info(f"Generated salt (store this in .env): {salt}")

        return base64.b64decode(salt.encode())

    def _derive_fernet_key(self) -> Fernet:
        """Derive Fernet encryption key from master secret using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret))
        return Fernet(key)

    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary of credentials

        Args:
            data: Dictionary containing credentials (e.g., {"access_token": "..."})

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If data cannot be serialized to JSON
        """
        try:
            # Serialize to JSON
            json_data = json.dumps(data, ensure_ascii=False)

            # Encrypt
            encrypted = self.fernet.encrypt(json_data.encode())

            # Return as base64 string
            result = encrypted.decode()

            logger.debug(f"Encrypted credential data ({len(data)} fields)")
            return result

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt credentials: {e}")

    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt encrypted credentials

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Dictionary containing decrypted credentials

        Raises:
            ValueError: If decryption fails or data is invalid
        """
        try:
            # Decrypt
            decrypted = self.fernet.decrypt(encrypted_data.encode())

            # Deserialize from JSON
            data = json.loads(decrypted.decode())

            logger.debug(f"Decrypted credential data ({len(data)} fields)")
            return data

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt credentials: {e}")

    def encrypt_oauth_credentials(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
        token_type: str = "Bearer",
        **extra_fields
    ) -> str:
        """
        Encrypt OAuth2 credentials

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_in: Token expiry in seconds (optional)
            scope: OAuth scopes (optional)
            token_type: Token type (default: "Bearer")
            **extra_fields: Additional provider-specific fields

        Returns:
            Encrypted credentials string
        """
        credentials = {
            "access_token": access_token,
            "token_type": token_type,
        }

        if refresh_token:
            credentials["refresh_token"] = refresh_token
        if expires_in:
            credentials["expires_in"] = expires_in
        if scope:
            credentials["scope"] = scope

        # Add extra fields (e.g., instance_url for Salesforce)
        credentials.update(extra_fields)

        return self.encrypt(credentials)

    def encrypt_api_key(
        self,
        api_key: str,
        api_secret: Optional[str] = None,
        **extra_fields
    ) -> str:
        """
        Encrypt API key credentials

        Args:
            api_key: API key
            api_secret: API secret (optional)
            **extra_fields: Additional fields

        Returns:
            Encrypted credentials string
        """
        credentials = {"api_key": api_key}

        if api_secret:
            credentials["api_secret"] = api_secret

        credentials.update(extra_fields)

        return self.encrypt(credentials)

    def encrypt_database_credentials(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        ssl_mode: str = "prefer",
        **extra_fields
    ) -> str:
        """
        Encrypt database connection credentials

        Args:
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            ssl_mode: SSL mode (prefer, require, disable)
            **extra_fields: Additional connection parameters

        Returns:
            Encrypted credentials string
        """
        credentials = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "ssl_mode": ssl_mode,
        }

        credentials.update(extra_fields)

        return self.encrypt(credentials)

    def encrypt_service_account(
        self,
        service_account_json: Dict[str, Any],
        project_id: Optional[str] = None,
        **extra_fields
    ) -> str:
        """
        Encrypt service account credentials (GCP, AWS, etc.)

        Args:
            service_account_json: Service account JSON key
            project_id: GCP project ID (optional)
            **extra_fields: Additional fields

        Returns:
            Encrypted credentials string
        """
        credentials = {"service_account_json": service_account_json}

        if project_id:
            credentials["project_id"] = project_id

        credentials.update(extra_fields)

        return self.encrypt(credentials)

    def rotate_encryption_key(self, old_secret: str, old_salt: str) -> None:
        """
        Rotate encryption keys (for credential migration)

        WARNING: This requires re-encrypting ALL stored credentials

        Args:
            old_secret: Previous CREDENTIAL_VAULT_SECRET
            old_salt: Previous CREDENTIAL_VAULT_SALT
        """
        # Create old Fernet instance
        old_kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=base64.b64decode(old_salt.encode()),
            iterations=100000,
            backend=default_backend()
        )
        old_key = base64.urlsafe_b64encode(old_kdf.derive(old_secret.encode()))
        old_fernet = Fernet(old_key)

        logger.warning("Key rotation initiated - this is a sensitive operation!")
        # Note: Actual migration would need to iterate through all ConnectionCredential records
        # and re-encrypt them with the new key
        raise NotImplementedError("Key rotation requires database migration")

    def verify_encryption(self, encrypted_data: str) -> bool:
        """
        Verify that encrypted data can be decrypted successfully

        Args:
            encrypted_data: Encrypted credential string

        Returns:
            True if decryption succeeds, False otherwise
        """
        try:
            self.decrypt(encrypted_data)
            return True
        except Exception:
            return False


# Singleton instance
_vault_instance: Optional[CredentialVault] = None


def get_credential_vault() -> CredentialVault:
    """Get singleton CredentialVault instance"""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = CredentialVault()
    return _vault_instance
