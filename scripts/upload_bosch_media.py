"""
Upload Bosch Media Files to MinIO

Uploads 25,448 files from /Bosch/0711/ to MinIO bucket
"""

import os
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_HOST = "localhost:4050"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "bosch-thermotechnik"

# Source directories
BOSCH_SOURCE = Path("/home/christoph.bertsch/0711/Bosch/0711")
IMAGES_DIR = BOSCH_SOURCE / "extracted_images"
DOCS_DIR = BOSCH_SOURCE / "extracted_documents"

def upload_directory(client, bucket, source_dir, target_prefix):
    """Upload directory recursively"""

    if not source_dir.exists():
        logger.warning(f"Directory not found: {source_dir}")
        return 0

    uploaded = 0
    errors = 0

    for file_path in source_dir.rglob('*'):
        if file_path.is_file():
            # Create MinIO object path
            relative_path = file_path.relative_to(source_dir)
            object_name = f"{target_prefix}/{relative_path}"

            try:
                client.fput_object(
                    bucket,
                    object_name,
                    str(file_path)
                )
                uploaded += 1

                if uploaded % 100 == 0:
                    logger.info(f"  Uploaded {uploaded} files...")

            except S3Error as e:
                logger.error(f"Error uploading {file_path.name}: {e}")
                errors += 1

    logger.info(f"✓ Uploaded {uploaded} files from {source_dir.name} (errors: {errors})")
    return uploaded

def main():
    logger.info("=" * 70)
    logger.info("BOSCH MEDIA UPLOAD TO MINIO")
    logger.info("=" * 70)
    logger.info(f"MinIO: {MINIO_HOST}")
    logger.info(f"Bucket: {BUCKET_NAME}")
    logger.info(f"Source: {BOSCH_SOURCE}")
    logger.info("")

    # Connect to MinIO
    client = Minio(
        endpoint=MINIO_HOST,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    # Create bucket if not exists
    try:
        # Try to create bucket (will fail if exists, which is fine)
        client.make_bucket(bucket_name=BUCKET_NAME)
        logger.info(f"✓ Created bucket: {BUCKET_NAME}")
    except S3Error as e:
        if "BucketAlreadyOwnedByYou" in str(e) or "already" in str(e).lower():
            logger.info(f"✓ Bucket already exists: {BUCKET_NAME}")
        else:
            logger.error(f"Error with bucket: {e}")
            return

    logger.info("")
    total_uploaded = 0

    # Upload images
    logger.info("Uploading images...")
    if IMAGES_DIR.exists():
        count = upload_directory(client, BUCKET_NAME, IMAGES_DIR, "raw/images")
        total_uploaded += count

    logger.info("")

    # Upload documents
    logger.info("Uploading documents...")
    if DOCS_DIR.exists():
        count = upload_directory(client, BUCKET_NAME, DOCS_DIR, "raw/documents")
        total_uploaded += count

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"✅ UPLOAD COMPLETE: {total_uploaded} files")
    logger.info("=" * 70)
    logger.info(f"Bucket: {BUCKET_NAME}")
    logger.info(f"Access: http://localhost:4050/minio/{BUCKET_NAME}/")
    logger.info("=" * 70)

if __name__ == '__main__':
    main()
