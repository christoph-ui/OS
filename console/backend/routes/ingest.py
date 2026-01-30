"""
Ingestion Routes

Trigger and monitor data ingestion.
"""

import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel

from ..auth.dependencies import require_auth
from ..auth.models import CustomerContext

logger = logging.getLogger(__name__)
router = APIRouter()


class IngestRequest(BaseModel):
    """Ingestion request"""
    path: str
    mcp: Optional[str] = None
    recursive: bool = True
    file_types: Optional[List[str]] = None


class IngestResponse(BaseModel):
    """Ingestion response"""
    job_id: str
    status: str
    path: str
    mcp: Optional[str]


class IngestStatus(BaseModel):
    """Ingestion job status"""
    job_id: str
    status: str  # pending, running, completed, failed
    files_processed: int
    files_total: int
    errors: List[str]
    current_file: Optional[str] = None
    current_phase: Optional[str] = None


# In-memory job tracking (would use Redis in production)
# Structure: {job_id: {"customer_id": str, "status": str, ...}}
_jobs = {}


@router.post("", response_model=IngestResponse)
async def start_ingestion(
    request: Request,
    ingest_request: IngestRequest,
    background_tasks: BackgroundTasks,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Start data ingestion from a folder.

    Requires authentication. Data is tagged with customer_id for isolation.

    The ingestion runs in the background. Use /ingest/{job_id}/status
    to check progress.

    Example:
        POST /api/ingest
        Headers: Authorization: Bearer <token>
        {
            "path": "/data/Buchhaltung",
            "mcp": "ctax",
            "recursive": true
        }
    """
    platform = request.app.state.platform

    # Check MCP access permission
    if ingest_request.mcp and not ctx.can_access_mcp(ingest_request.mcp):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to MCP: {ingest_request.mcp}"
        )

    # Validate path (allow MinIO bucket paths in format: /data/customer-xxx)
    path = Path(ingest_request.path)

    # Accept MinIO bucket paths or real filesystem paths
    is_minio_path = "customer-" in str(path) or str(path).startswith("/data/customer")

    if not is_minio_path and not path.exists():
        raise HTTPException(status_code=400, detail=f"Path not found: {path}")

    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())[:8]

    # Initialize job status with customer_id
    _jobs[job_id] = {
        "customer_id": ctx.customer_id,
        "status": "pending",
        "files_processed": 0,
        "files_total": 0,
        "errors": [],
        "current_file": None,
        "current_phase": None
    }

    # Run ingestion in background with customer context
    background_tasks.add_task(
        run_ingestion,
        job_id,
        platform,
        ingest_request,
        ctx.customer_id
    )

    return IngestResponse(
        job_id=job_id,
        status="pending",
        path=str(path),
        mcp=ingest_request.mcp
    )


async def run_ingestion(job_id: str, platform, request: IngestRequest, customer_id: str):
    """Background ingestion task with customer context"""
    import tempfile
    import shutil
    from minio import Minio

    try:
        _jobs[job_id]["status"] = "running"

        ingest_path = request.path
        cleanup_temp = False

        # If MinIO path, download files first
        if "customer-" in request.path or request.path.startswith("/data/customer-"):
            # Extract bucket name from path
            bucket_name = request.path.replace("/data/", "").strip("/")
            if not bucket_name.startswith("customer-"):
                bucket_name = f"customer-{customer_id}"

            logger.info(f"📦 Downloading files from MinIO bucket: {bucket_name}")

            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"ingestion_{customer_id}_")
            cleanup_temp = True

            try:
                # Connect to MinIO
                minio_client = Minio(
                    endpoint="localhost:4050",
                    access_key="0711admin",
                    secret_key="0711secret",
                    secure=False
                )

                # Download all files from bucket
                objects = minio_client.list_objects(bucket_name=bucket_name, recursive=True)
                downloaded_count = 0
                for obj in objects:
                    file_path = Path(temp_dir) / obj.object_name
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    minio_client.fget_object(
                        bucket_name=bucket_name,
                        object_name=obj.object_name,
                        file_path=str(file_path)
                    )
                    downloaded_count += 1
                    logger.info(f"  ✓ Downloaded ({downloaded_count}): {obj.object_name}")

                ingest_path = temp_dir
                logger.info(f"✅ Downloaded bucket to: {temp_dir}")

            except Exception as e:
                logger.error(f"MinIO download failed: {e}")
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["errors"].append(f"MinIO download failed: {str(e)}")
                if cleanup_temp:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                return

        if platform:
            # Progress callback to update job status in real-time
            def update_progress(phase: str, current_file: str = None, processed: int = 0, total: int = 0):
                _jobs[job_id]["current_phase"] = phase
                _jobs[job_id]["current_file"] = current_file
                _jobs[job_id]["files_processed"] = processed
                _jobs[job_id]["files_total"] = total

            # Run ingestion with customer_id for data isolation
            stats = platform.ingest(
                path=ingest_path,
                mcp=request.mcp,
                recursive=request.recursive,
                file_types=request.file_types,
                customer_id=customer_id,  # Tag data with customer
                progress_callback=update_progress  # Real-time updates
            )

            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["files_processed"] = stats.get("files_processed", 0)
            _jobs[job_id]["files_total"] = stats.get("files_total", 0)
            _jobs[job_id]["current_file"] = None
            _jobs[job_id]["current_phase"] = "Complete"
        else:
            # No platform available - mark as failed
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["errors"].append("Platform not initialized")

        # Cleanup temp directory if we downloaded from MinIO
        if cleanup_temp and Path(ingest_path).exists():
            shutil.rmtree(ingest_path, ignore_errors=True)
            logger.info(f"🧹 Cleaned up temp directory: {ingest_path}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["errors"].append(str(e))

        # Cleanup on error too
        if cleanup_temp and 'temp_dir' in locals() and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{job_id}/status", response_model=IngestStatus)
async def get_ingestion_status(
    job_id: str,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Get ingestion job status.

    Requires authentication. Only shows jobs belonging to the customer.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = _jobs[job_id]

    # Ensure customer can only see their own jobs
    if job.get("customer_id") != ctx.customer_id and not ctx.is_admin:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return IngestStatus(
        job_id=job_id,
        status=job["status"],
        files_processed=job["files_processed"],
        files_total=job["files_total"],
        errors=job["errors"]
    )


@router.get("/jobs")
async def list_ingestion_jobs(ctx: CustomerContext = Depends(require_auth)):
    """
    List ingestion jobs for the current customer.

    Requires authentication.
    """
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "files_processed": job["files_processed"]
            }
            for job_id, job in _jobs.items()
            if job.get("customer_id") == ctx.customer_id or ctx.is_admin
        ]
    }
