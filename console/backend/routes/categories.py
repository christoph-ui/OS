"""
Dynamic Data Categories API

Returns customer-specific categories discovered by AI (multi-tenant safe)
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..auth.dependencies import require_auth
from ..auth.models import CustomerContext

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/data/categories")
async def get_customer_categories(
    customer: CustomerContext = Depends(require_auth)
):
    """
    Get dynamic categories for customer (MULTI-TENANT SAFE)

    Returns categories discovered from their actual data,
    queried from database per customer_id.
    """
    from core import Platform

    platform = Platform()
    db = platform.db_session

    try:
        # Query customer categories from DATABASE (not hardcoded lakehouse!)
        query = text("""
            SELECT
                category_key,
                category_name,
                description,
                icon,
                color,
                document_count,
                total_size_bytes,
                sort_order,
                last_updated_at
            FROM customer_data_categories
            WHERE customer_id = :customer_id
              AND is_active = true
            ORDER BY sort_order ASC, document_count DESC
        """)

        result = db.execute(query, {"customer_id": customer.customer_id})
        rows = result.fetchall()

        if not rows:
            # No categories discovered yet - return empty or trigger discovery
            return {
                "categories": [],
                "total": 0,
                "message": "No categories discovered yet. Upload data to auto-discover categories."
            }

        categories = [
            {
                "key": row[0],
                "name": row[1],
                "description": row[2],
                "icon": row[3] or "📄",
                "color": row[4] or "#b0aea5",
                "document_count": row[5] or 0,
                "size_bytes": row[6] or 0,
                "size_mb": round((row[6] or 0) / 1024 / 1024, 2) if row[6] else 0,
                "last_updated": row[8].isoformat() if row[8] else None
            }
            for row in rows
        ]

        return {
            "categories": categories,
            "total": len(categories)
        }

    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/data/categories/discover")
async def discover_categories(
    customer: CustomerContext = Depends(require_auth)
):
    """
    Trigger AI category discovery for customer

    Analyzes all customer data and discovers natural categories
    """
    from api.services.category_discovery_service import get_category_discovery_service
    from core.config import PlatformConfig
    import os

    # Get Anthropic API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Anthropic API key not configured"
        )

    discovery_service = get_category_discovery_service(api_key)

    if not discovery_service:
        raise HTTPException(
            status_code=500,
            detail="Category discovery service not available"
        )

    try:
        # Get sample files from MinIO
        from minio import Minio
        import os

        minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:4050"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "0711admin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "0711secret"),
            secure=False
        )

        bucket_name = f"customer-{customer.customer_id}"

        # List files
        sample_files = []
        try:
            objects = minio_client.list_objects(bucket_name, recursive=True)
            for obj in list(objects)[:100]:  # Sample first 100
                sample_files.append({
                    "filename": obj.object_name,
                    "size": obj.size,
                    "path": f"s3://{bucket_name}/{obj.object_name}"
                })
        except Exception as e:
            logger.warning(f"Could not list MinIO objects: {e}")

        if not sample_files:
            return {
                "success": False,
                "message": "No files found to analyze"
            }

        # Discover categories
        categories = await discovery_service.discover_categories(
            customer_id=customer.customer_id,
            sample_files=sample_files
        )

        # Save to database
        from core import Platform
        platform = Platform()
        db = platform.db_session

        for cat in categories:
            insert_query = text("""
                INSERT INTO customer_data_categories (
                    customer_id, category_key, category_name,
                    description, icon, color,
                    document_count, discovered_by, sort_order
                )
                VALUES (
                    :customer_id, :category_key, :category_name,
                    :description, :icon, :color,
                    :document_count, 'claude', :sort_order
                )
                ON CONFLICT (customer_id, category_key)
                DO UPDATE SET
                    category_name = EXCLUDED.category_name,
                    description = EXCLUDED.description,
                    document_count = EXCLUDED.document_count,
                    updated_at = NOW()
            """)

            estimated_docs = int(len(sample_files) * cat.get('estimated_percentage', 10) / 100)

            db.execute(insert_query, {
                "customer_id": customer.customer_id,
                "category_key": cat['category_key'],
                "category_name": cat['category_name'],
                "description": cat.get('description', ''),
                "icon": cat.get('icon', '📄'),
                "color": cat.get('color', '#b0aea5'),
                "document_count": estimated_docs,
                "sort_order": categories.index(cat)
            })

        db.commit()

        return {
            "success": True,
            "categories_discovered": len(categories),
            "categories": categories
        }

    except Exception as e:
        logger.error(f"Category discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
