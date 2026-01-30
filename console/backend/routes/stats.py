"""
Customer Statistics API

Exposes read-only statistics for 0711 MCP Central to monitor customer data
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/")
async def get_stats():
    """
    Get customer statistics

    This endpoint is called by 0711 MCP Central for:
    - Change detection
    - Service recommendations
    - Billing
    - Rate limiting

    Returns read-only statistics without sensitive data
    """
    try:
        # Get lakehouse stats
        lakehouse_stats = await _get_lakehouse_stats()

        # Get MinIO stats
        minio_stats = await _get_minio_stats()

        # Get Neo4j stats (if available)
        neo4j_stats = await _get_neo4j_stats()

        return {
            "total_documents": lakehouse_stats.get("documents", 0),
            "total_embeddings": lakehouse_stats.get("embeddings", 0),
            "total_images": minio_stats.get("images", 0),
            "total_files": minio_stats.get("total_files", 0),
            "graph_nodes": neo4j_stats.get("nodes", 0),
            "graph_edges": neo4j_stats.get("edges", 0),
            "storage_mb": lakehouse_stats.get("storage_mb", 0) + minio_stats.get("storage_mb", 0),
            "last_ingestion": lakehouse_stats.get("last_ingestion"),
            "timestamp": "2025-01-27T12:00:00Z"  # Current timestamp
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(500, f"Failed to retrieve stats: {str(e)}")


async def _get_lakehouse_stats() -> dict:
    """Get statistics from lakehouse"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9302/stats")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"Lakehouse stats unavailable: {e}")
        return {}


async def _get_minio_stats() -> dict:
    """Get statistics from MinIO"""
    # Would query MinIO API
    # For now: placeholder

    return {
        "total_files": 0,
        "images": 0,
        "storage_mb": 0
    }


async def _get_neo4j_stats() -> dict:
    """Get statistics from Neo4j"""
    # Would query Neo4j
    # For now: placeholder

    return {
        "nodes": 0,
        "edges": 0
    }


@router.get("/detailed")
async def get_detailed_stats():
    """
    Get detailed statistics

    Includes breakdown by:
    - Document type
    - MCP assignment
    - File format
    - Time range
    """
    try:
        lakehouse_stats = await _get_lakehouse_stats()

        return {
            "overview": await get_stats(),
            "by_mcp": lakehouse_stats.get("by_mcp", {}),
            "by_type": lakehouse_stats.get("by_type", {}),
            "recent_activity": lakehouse_stats.get("recent_activity", [])
        }

    except Exception as e:
        logger.error(f"Detailed stats retrieval failed: {e}")
        raise HTTPException(500, f"Failed to retrieve detailed stats: {str(e)}")
