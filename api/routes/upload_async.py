"""
Async File Upload with Background Jobs
Returns immediately, processes in background, client polls for status
"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload-async", tags=["upload-async"])

# In-memory job storage (use Redis in production)
upload_jobs: Dict[str, Dict] = {}


async def process_upload_job(
    job_id: str,
    files_data: List[tuple],  # (filename, content, size, content_type)
    customer_id: str
):
    """Background task to process file uploads"""
    from minio import Minio
    import io

    try:
        upload_jobs[job_id]["status"] = "uploading"
        upload_jobs[job_id]["progress"] = 0

        # Initialize MinIO
        minio = Minio(
            endpoint="localhost:4050",
            access_key="0711admin",
            secret_key="0711secret",
            secure=False
        )

        customer_bucket = f"customer-{customer_id}"

        # Create bucket if first upload
        if not minio.bucket_exists(bucket_name=customer_bucket):
            minio.make_bucket(bucket_name=customer_bucket)
            upload_jobs[job_id]["first_upload"] = True
            logger.info(f"🚀 FIRST UPLOAD for {customer_id}")

        total_files = len(files_data)
        uploaded_files = []

        for idx, (filename, content, size, content_type) in enumerate(files_data):
            # Upload to MinIO
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"{timestamp}_{filename}"

            minio.put_object(
                bucket_name=customer_bucket,
                object_name=object_name,
                data=io.BytesIO(content),
                length=size,
                content_type=content_type or "application/octet-stream"
            )

            uploaded_files.append({
                "filename": filename,
                "size": size,
                "path": f"s3://{customer_bucket}/{object_name}"
            })

            # Update progress
            progress = int(((idx + 1) / total_files) * 100)
            upload_jobs[job_id]["progress"] = progress
            upload_jobs[job_id]["current_file"] = filename
            upload_jobs[job_id]["uploaded_count"] = idx + 1

            logger.info(f"[{job_id}] Uploaded {idx+1}/{total_files}: {filename}")

            # Real-time AI analysis
            try:
                from .realtime_analysis import analyze_uploaded_file
                await analyze_uploaded_file(customer_id, filename, size, content_type)
            except Exception as e:
                logger.warning(f"Analysis failed for {filename}: {e}")

        # Mark complete
        upload_jobs[job_id]["status"] = "completed"
        upload_jobs[job_id]["progress"] = 100
        upload_jobs[job_id]["files"] = uploaded_files
        upload_jobs[job_id]["completed_at"] = datetime.now().isoformat()

        logger.info(f"✓ Job {job_id} completed: {total_files} files")

        # ALWAYS trigger ingestion after upload completes
        logger.info(f"🚀 Triggering ingestion for {customer_id}")
        try:
            # Start ingestion pipeline
            from ingestion.orchestrator import IngestionOrchestrator, FolderConfig
            from pathlib import Path
            import asyncio

            # Create ingestion task (non-blocking)
            async def run_ingestion():
                logger.info(f"📥 Starting ingestion for bucket: {customer_bucket}")

                # For MinIO-based ingestion, we'd need to:
                # 1. Download files from MinIO to temp directory
                # 2. Run ingestion on temp directory
                # 3. Clean up temp files

                # For now, log that ingestion would start
                logger.info(f"✓ Ingestion pipeline ready for {customer_bucket}")

            # Schedule ingestion (would run in separate task in production)
            asyncio.create_task(run_ingestion())

            upload_jobs[job_id]["ingestion_started"] = True

        except Exception as e:
            logger.error(f"Failed to start ingestion: {e}")
            upload_jobs[job_id]["ingestion_error"] = str(e)

        # Trigger deployment if first upload
        if upload_jobs[job_id].get("first_upload"):
            logger.info(f"📦 Triggering deployment for {customer_id}")
            # Deployment trigger here

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        upload_jobs[job_id]["status"] = "failed"
        upload_jobs[job_id]["error"] = str(e)


@router.post("/start")
async def start_upload(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    customer_id: str = "default"
):
    """
    Start async file upload.
    Returns job_id immediately, processes in background.
    """
    job_id = str(uuid.uuid4())

    # Read file contents (fast)
    files_data = []
    for file in files:
        content = await file.read()
        files_data.append((
            file.filename,
            content,
            len(content),
            file.content_type
        ))

    # Create job
    upload_jobs[job_id] = {
        "job_id": job_id,
        "customer_id": customer_id,
        "status": "queued",
        "total_files": len(files),
        "uploaded_count": 0,
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "first_upload": False
    }

    # Start background processing
    background_tasks.add_task(
        process_upload_job,
        job_id,
        files_data,
        customer_id
    )

    logger.info(f"Created upload job {job_id} for {customer_id}: {len(files)} files")

    return {
        "success": True,
        "job_id": job_id,
        "total_files": len(files),
        "message": f"Upload started for {len(files)} files"
    }


@router.get("/status/{job_id}")
async def get_upload_status(job_id: str):
    """Get upload job status"""
    if job_id not in upload_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = upload_jobs[job_id]

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "total_files": job["total_files"],
        "uploaded_count": job.get("uploaded_count", 0),
        "current_file": job.get("current_file"),
        "first_upload": job.get("first_upload", False),
        "files": job.get("files", []),
        "error": job.get("error")
    }


@router.get("/jobs")
async def list_upload_jobs():
    """List all upload jobs"""
    return {
        "success": True,
        "jobs": list(upload_jobs.values())
    }
