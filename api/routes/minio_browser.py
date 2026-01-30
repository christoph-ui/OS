"""
MinIO File Browser - Preview files before ingestion
"""
from fastapi import APIRouter, HTTPException
from minio import Minio
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/minio", tags=["minio"])


def get_minio():
    return Minio(
        endpoint="localhost:4050",
        access_key="0711admin",
        secret_key="0711secret",
        secure=False
    )


@router.get("/buckets")
async def list_buckets():
    """List all MinIO buckets"""
    try:
        client = get_minio()
        buckets = client.list_buckets()

        return {
            "success": True,
            "buckets": [
                {
                    "name": b.name,
                    "created": b.creation_date.isoformat() if b.creation_date else None
                } for b in buckets
            ]
        }
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse/{bucket_name}")
async def browse_bucket(bucket_name: str, prefix: str = ""):
    """
    Browse files in a MinIO bucket
    Shows what's available for ingestion
    """
    try:
        client = get_minio()

        # List objects
        objects = client.list_objects(
            bucket_name=bucket_name,
            prefix=prefix,
            recursive=True
        )

        files = []
        total_size = 0

        for obj in objects:
            files.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                "etag": obj.etag
            })
            total_size += obj.size

        return {
            "success": True,
            "bucket": bucket_name,
            "file_count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "files": files[:100],  # Limit to first 100 for preview
            "has_more": len(files) > 100
        }

    except Exception as e:
        logger.error(f"Error browsing bucket {bucket_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
