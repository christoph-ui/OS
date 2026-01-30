"""
MinIO service for S3-compatible object storage
Handles model storage and retrieval
"""

import logging
from typing import Optional, BinaryIO
from datetime import timedelta
import hashlib

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO object storage service"""

    def __init__(self):
        """Initialize MinIO client"""
        if not MINIO_AVAILABLE:
            logger.warning("MinIO client not available - install minio package")
            self.client = None
            return

        # Parse MinIO URL
        minio_url = getattr(settings, 'minio_url', "http://minio:9000")
        minio_host = minio_url.replace("http://", "").replace("https://", "")

        # Get credentials
        access_key = getattr(settings, 'minio_access_key', '0711_admin')
        secret_key = getattr(settings, 'minio_secret_key', '0711_minio_password')

        # Initialize client
        try:
            self.client = Minio(
                endpoint=minio_host,
                access_key=access_key,
                secret_key=secret_key,
                secure=False  # Use HTTPS in production
            )

            # Default bucket for models
            self.models_bucket = "0711-models"

            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name=self.models_bucket):
                self.client.make_bucket(bucket_name=self.models_bucket)
                logger.info(f"Created MinIO bucket: {self.models_bucket}")
        except Exception as e:
            logger.warning(f"Could not initialize MinIO client: {e}")
            self.client = None

    def upload_model(
        self,
        model_name: str,
        file_data: BinaryIO,
        content_length: int,
        content_type: str = "application/octet-stream"
    ) -> dict:
        """
        Upload a model file to MinIO

        Args:
            model_name: Name/path for the model in storage
            file_data: File data stream
            content_length: Size of file in bytes
            content_type: MIME type

        Returns:
            Dict with upload details (bucket, path, size, hash)
        """
        try:
            # Calculate SHA256 hash
            file_data.seek(0)
            sha256_hash = hashlib.sha256(file_data.read()).hexdigest()
            file_data.seek(0)

            # Upload to MinIO
            object_path = f"models/{model_name}"

            self.client.put_object(
                self.models_bucket,
                object_path,
                file_data,
                content_length,
                content_type=content_type
            )

            logger.info(f"Uploaded model {model_name} to MinIO")

            return {
                "bucket": self.models_bucket,
                "path": object_path,
                "size_bytes": content_length,
                "hash": sha256_hash,
                "url": f"minio://{self.models_bucket}/{object_path}"
            }

        except S3Error as e:
            logger.error(f"Failed to upload model {model_name}: {e}")
            raise

    def get_model_download_url(
        self,
        object_path: str,
        expires_seconds: int = 3600
    ) -> str:
        """
        Generate a presigned download URL for a model

        Args:
            object_path: Path to object in bucket
            expires_seconds: URL expiration time

        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.models_bucket,
                object_path,
                expires=timedelta(seconds=expires_seconds)
            )
            return url

        except S3Error as e:
            logger.error(f"Failed to generate download URL for {object_path}: {e}")
            raise

    def delete_model(self, object_path: str) -> bool:
        """
        Delete a model from storage

        Args:
            object_path: Path to object in bucket

        Returns:
            True if deleted successfully
        """
        try:
            self.client.remove_object(self.models_bucket, object_path)
            logger.info(f"Deleted model: {object_path}")
            return True

        except S3Error as e:
            logger.error(f"Failed to delete model {object_path}: {e}")
            return False

    def model_exists(self, object_path: str) -> bool:
        """
        Check if a model exists in storage

        Args:
            object_path: Path to object in bucket

        Returns:
            True if exists
        """
        try:
            self.client.stat_object(self.models_bucket, object_path)
            return True
        except S3Error:
            return False

    def get_model_info(self, object_path: str) -> Optional[dict]:
        """
        Get metadata about a stored model

        Args:
            object_path: Path to object in bucket

        Returns:
            Dict with model metadata or None
        """
        try:
            stat = self.client.stat_object(self.models_bucket, object_path)
            return {
                "bucket": self.models_bucket,
                "path": object_path,
                "size_bytes": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type
            }
        except S3Error as e:
            logger.error(f"Failed to get model info for {object_path}: {e}")
            return None


# Create singleton instance
try:
    minio_service = MinIOService()
except Exception as e:
    logger.warning(f"Could not initialize MinIO service: {e}")
    minio_service = None
