"""
File Upload Service
Handles certification and document uploads to MinIO for expert network
"""

from minio import Minio
from minio.error import S3Error
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import os
from io import BytesIO

from core.config import settings

class FileUploadService:
    """Service for uploading expert documents to MinIO"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.certifications_bucket = "expert-certifications"
        self.documents_bucket = "expert-documents"

        # Ensure buckets exist
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Create buckets if they don't exist"""
        try:
            for bucket in [self.certifications_bucket, self.documents_bucket]:
                if not self.client.bucket_exists(bucket_name=bucket):
                    self.client.make_bucket(bucket_name=bucket)
                    print(f"Created bucket: {bucket}")
        except S3Error as e:
            print(f"Error creating buckets: {e}")

    def upload_certification(
        self,
        expert_id: str,
        file_content: bytes,
        filename: str,
        content_type: str = "application/pdf"
    ) -> dict:
        """
        Upload expert certification to MinIO

        Args:
            expert_id: Expert's UUID
            file_content: File bytes
            filename: Original filename
            content_type: MIME type

        Returns:
            dict with file_url, filename, size
        """
        # Generate unique filename
        ext = Path(filename).suffix
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{expert_id}/{timestamp}_{filename}"

        try:
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.certifications_bucket,
                object_name=unique_filename,
                data=BytesIO(file_content),
                length=len(file_content),
                content_type=content_type
            )

            # Generate presigned URL (valid for 7 days)
            file_url = self.client.presigned_get_object(
                bucket_name=self.certifications_bucket,
                object_name=unique_filename,
                expires=timedelta(days=7)
            )

            return {
                "success": True,
                "file_url": file_url,
                "filename": filename,
                "unique_filename": unique_filename,
                "size": len(file_content),
                "bucket": self.certifications_bucket
            }

        except S3Error as e:
            print(f"Error uploading file: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def upload_id_document(
        self,
        expert_id: str,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> dict:
        """Upload ID document (passport, national ID)"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{expert_id}/id_{timestamp}_{filename}"

        try:
            self.client.put_object(
                bucket_name=self.documents_bucket,
                object_name=unique_filename,
                data=BytesIO(file_content),
                length=len(file_content),
                content_type=content_type
            )

            # Generate presigned URL (valid for 7 days)
            file_url = self.client.presigned_get_object(
                bucket_name=self.documents_bucket,
                object_name=unique_filename,
                expires=timedelta(days=7)
            )

            return {
                "success": True,
                "file_url": file_url,
                "filename": filename,
                "unique_filename": unique_filename,
                "size": len(file_content),
                "bucket": self.documents_bucket
            }

        except S3Error as e:
            print(f"Error uploading ID document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_expert_files(self, expert_id: str) -> List[dict]:
        """List all files for an expert"""
        files = []

        try:
            # Get certifications
            objects = self.client.list_objects(
                bucket_name=self.certifications_bucket,
                prefix=f"{expert_id}/",
                recursive=True
            )

            for obj in objects:
                files.append({
                    "filename": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "bucket": self.certifications_bucket,
                    "type": "certification"
                })

            # Get documents
            objects = self.client.list_objects(
                bucket_name=self.documents_bucket,
                prefix=f"{expert_id}/",
                recursive=True
            )

            for obj in objects:
                files.append({
                    "filename": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "bucket": self.documents_bucket,
                    "type": "document"
                })

        except S3Error as e:
            print(f"Error listing files: {e}")

        return files

    def delete_file(self, bucket: str, filename: str) -> bool:
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(bucket_name=bucket, object_name=filename)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_url(
        self,
        bucket: str,
        filename: str,
        expires_hours: int = 24
    ) -> Optional[str]:
        """Get presigned URL for a file"""
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=filename,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return None


# Singleton instance
file_upload_service = FileUploadService()
