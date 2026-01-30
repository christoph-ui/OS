"""
Ingestion API - Trigger data processing pipeline
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])

# In-memory progress storage (use Redis in production)
ingestion_progress: Dict[str, dict] = {}


class IngestionRequest(BaseModel):
    customer_id: str
    minio_bucket: str
    target_mcp: str = "general"


async def run_ingestion_pipeline(request: IngestionRequest):
    """Background task to run REAL ingestion from MinIO"""
    from ingestion.orchestrator import IngestionOrchestrator, IngestionProgress, FolderConfig
    from minio import Minio
    from pathlib import Path
    import tempfile
    import shutil

    try:
        # Initialize progress
        ingestion_progress[request.customer_id] = {
            "status": "downloading",
            "progress": 5,
            "message": "Downloading files from MinIO"
        }

        # Download files from MinIO to temp directory
        minio = Minio(
            endpoint="localhost:4050",
            access_key="0711admin",
            secret_key="0711secret",
            secure=False
        )

        temp_dir = Path(tempfile.mkdtemp(prefix=f"ingestion_{request.customer_id}_"))
        logger.info(f"Created temp dir: {temp_dir}")

        # Download all files from bucket
        objects = list(minio.list_objects(bucket_name=request.minio_bucket, recursive=True))
        total_files = len(objects)

        logger.info(f"Downloading {total_files} files from {request.minio_bucket}")

        for idx, obj in enumerate(objects):
            file_path = temp_dir / obj.object_name.replace("/", "_")
            minio.fget_object(
                bucket_name=request.minio_bucket,
                object_name=obj.object_name,
                file_path=str(file_path)
            )

            progress = int(5 + (idx / total_files) * 15)  # 5-20%
            ingestion_progress[request.customer_id] = {
                "status": "downloading",
                "progress": progress,
                "message": f"Downloaded {idx+1}/{total_files} files",
                "current_file": obj.object_name
            }

        logger.info(f"✓ Downloaded {total_files} files to {temp_dir}")

        # Create orchestrator with Claude API key for classification
        from api.config import settings

        orchestrator = IngestionOrchestrator(
            lakehouse_path=Path(f"/tmp/lakehouse/{request.customer_id}"),
            vllm_url="http://localhost:8001",
            claude_api_key=settings.anthropic_api_key,
            batch_size=128,  # Larger batches for GPU
            max_workers=16   # More parallel workers
        )

        # Register progress callback
        def update_progress(progress: IngestionProgress):
            # Map ingestion progress to 20-100%
            adjusted_progress = 20 + int(progress.progress_percent * 0.8)
            ingestion_progress[request.customer_id] = {
                **progress.to_dict(),
                "progress": adjusted_progress
            }

        orchestrator.on_progress(update_progress)

        # Run REAL ingestion
        logger.info(f"🚀 Starting REAL ingestion for {request.customer_id}")

        folder_config = FolderConfig(
            path=temp_dir,
            mcp_assignment=request.target_mcp,
            recursive=True
        )

        result = await orchestrator.ingest([folder_config])

        logger.info(f"✓ Ingestion complete: {result.processed_files} files processed")

        ingestion_progress[request.customer_id] = {
            "status": "complete",
            "progress": 100,
            "message": f"Ingestion complete! Processed {result.processed_files} files",
            "total_files": result.total_files,
            "processed_files": result.processed_files,
            "failed_files": result.failed_files
        }

        # Cleanup temp directory
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temp dir: {temp_dir}")

    except Exception as e:
        logger.error(f"Ingestion failed for {request.customer_id}: {e}", exc_info=True)
        ingestion_progress[request.customer_id] = {
            "status": "failed",
            "error": str(e),
            "progress": 0
        }


@router.post("/start")
async def start_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger ingestion pipeline for customer's MinIO bucket

    Processes: Extract → Classify → Chunk → Embed → Load to Lakehouse
    """
    logger.info(f"🚀 Starting ingestion for customer: {request.customer_id}")
    logger.info(f"   MinIO bucket: {request.minio_bucket}")
    logger.info(f"   Target MCP: {request.target_mcp}")

    # Start ingestion in background
    background_tasks.add_task(run_ingestion_pipeline, request)

    # Initialize progress
    ingestion_progress[request.customer_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Ingestion queued"
    }

    return {
        "success": True,
        "customer_id": request.customer_id,
        "status": "started",
        "message": f"Ingestion started for {request.minio_bucket}",
        "estimated_time_minutes": 10
    }


@router.get("/status/{customer_id}")
async def get_ingestion_status(customer_id: str):
    """
    Get ingestion progress for customer
    """
    # Check if we have progress for this customer
    if customer_id not in ingestion_progress:
        return {
            "success": True,
            "customer_id": customer_id,
            "status": "not_started",
            "progress": 0,
            "message": "Ingestion not yet started"
        }

    progress = ingestion_progress[customer_id]

    return {
        "success": True,
        "customer_id": customer_id,
        **progress
    }
