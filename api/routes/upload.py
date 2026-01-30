"""
File Upload API Routes
Handles file uploads for onboarding and data ingestion
Uploads to MinIO S3-compatible storage
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from datetime import datetime
import logging
import io
import asyncio
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])

# MinIO client (lazy initialization)
_minio_client = None
BUCKET_NAME = "uploads"

# AI-generated explanations for normal people
_phase_explanations = {
    "initializing": "Wir bereiten alles für die Datenverarbeitung vor.",
    "downloading": "Ihre Dateien werden heruntergeladen und bereitgestellt.",
    "crawling": "Wir durchsuchen Ihre Dateien und identifizieren die verschiedenen Dokumenttypen.",
    "extracting": "Der Text wird aus Ihren Dokumenten extrahiert - egal ob PDF, Word, Excel oder andere Formate.",
    "classifying": "Wir kategorisieren Ihre Dokumente automatisch (z.B. Verträge, Produktdaten, Rechnungen).",
    "chunking": "Lange Dokumente werden in sinnvolle Abschnitte unterteilt, damit die KI sie besser verstehen kann.",
    "embedding": "Ihre Texte werden in mathematische Vektoren umgewandelt - so kann die KI semantisch ähnliche Inhalte finden.",
    "loading": "Die verarbeiteten Daten werden in Ihre persönliche Wissensdatenbank geladen.",
}

async def generate_ai_explanation(technical_status: str) -> str:
    """
    Generate human-friendly explanation using Claude Sonnet 4.5
    Falls Claude unavailable: Fallback auf vordefinierte Erklärungen
    """
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            response = await asyncio.to_thread(
                client.messages.create,
                model="claude-sonnet-4-5-20250929",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": f"""Erkläre diesen technischen Vorgang für normale Menschen in 1-2 Sätzen auf Deutsch:

"{technical_status}"

Sei freundlich, einfach und ermutigend. Verwende keine Fachbegriffe."""
                }]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"Claude explanation failed, using fallback: {e}")

    # Fallback
    for phase, explanation in _phase_explanations.items():
        if phase in technical_status.lower():
            return explanation

    return "Ihre Daten werden gerade verarbeitet..."

def get_minio_client() -> Minio:
    """Get or create MinIO client"""
    global _minio_client
    if _minio_client is None:
        try:
            _minio_client = Minio(
                endpoint="localhost:4050",
                access_key="0711admin",
                secret_key="0711secret",
                secure=False
            )
            # Ensure default bucket exists
            if not _minio_client.bucket_exists(bucket_name=BUCKET_NAME):
                _minio_client.make_bucket(bucket_name=BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {BUCKET_NAME}")
        except Exception as e:
            logger.error(f"MinIO client initialization error: {e}")
            raise
    return _minio_client


async def trigger_ingestion(customer_id: str, bucket_name: str, selected_mcps: List[str] = None):
    """
    Background task: Trigger ingestion for uploaded files
    Downloads files from MinIO and runs ingestion pipeline
    """
    try:
        logger.info(f"🚀 Starting background ingestion for customer: {customer_id}")

        # Import progress WebSocket
        from api.routes.progress_ws import send_progress_update

        await send_progress_update(customer_id, {
            "type": "ingestion",
            "progress": 5,
            "message": "Ingestion wird vorbereitet...",
            "phase": "initializing",
            "explanation": "Ihre Dateien werden aus dem Speicher heruntergeladen und für die Verarbeitung vorbereitet."
        })

        # Import ingestion components
        from ingestion.orchestrator import IngestionOrchestrator, FolderConfig
        from pathlib import Path
        import tempfile
        import shutil

        # Create temp directory for downloads
        temp_dir = Path(tempfile.mkdtemp(prefix=f"ingestion_{customer_id}_"))
        logger.info(f"Created temp directory: {temp_dir}")

        try:
            # Download files from MinIO to temp dir
            minio = get_minio_client()
            objects = minio.list_objects(bucket_name=bucket_name, recursive=True)

            total_files = sum(1 for _ in minio.list_objects(bucket_name=bucket_name, recursive=True))

            await send_progress_update(customer_id, {
                "type": "ingestion",
                "progress": 10,
                "message": f"{total_files} Dateien werden heruntergeladen...",
                "phase": "downloading",
                "explanation": f"Wir bereiten {total_files} Dateien für die Analyse vor."
            })

            downloaded_count = 0
            for obj in objects:
                file_path = temp_dir / obj.object_name
                file_path.parent.mkdir(parents=True, exist_ok=True)

                minio.fget_object(
                    bucket_name=bucket_name,
                    object_name=obj.object_name,
                    file_path=str(file_path)
                )
                downloaded_count += 1
                logger.info(f"Downloaded: {obj.object_name}")

                # Send progress
                download_progress = 10 + int((downloaded_count / total_files) * 10)
                await send_progress_update(customer_id, {
                    "type": "ingestion",
                    "progress": download_progress,
                    "message": f"{downloaded_count}/{total_files} Dateien heruntergeladen",
                    "phase": "downloading"
                })

            logger.info(f"✓ Downloaded {downloaded_count} files from MinIO")

            # Determine MCP assignment
            mcp_assignment = selected_mcps[0] if selected_mcps else "general"

            # Create folder config
            folder_configs = [FolderConfig(
                path=temp_dir,
                mcp_assignment=mcp_assignment,
                recursive=True
            )]

            # Initialize orchestrator with persistent path
            from core.paths import CustomerPaths

            lakehouse_path = CustomerPaths.get_lakehouse_path(customer_id)
            logger.info(f"Using persistent lakehouse path: {lakehouse_path}")

            orchestrator = IngestionOrchestrator(
                lakehouse_path=lakehouse_path,
                vllm_url="http://localhost:4030",
                embedding_model="intfloat/multilingual-e5-large",
                claude_api_key=os.getenv("ANTHROPIC_API_KEY"),  # Enable intelligent extraction
                batch_size=128,
                max_workers=4
            )

            # Progress callback with WebSocket streaming
            async def stream_progress(progress):
                logger.info(
                    f"Ingestion progress: {progress.status.value} - "
                    f"{progress.progress_percent:.1f}% - {progress.current_phase}"
                )

                # Map phase to human-friendly message with details
                phase_messages = {
                    "crawling": f"Dateien werden eingelesen ({progress.processed_files}/{progress.total_files})",
                    "extracting": f"Text wird extrahiert ({progress.processed_files}/{progress.total_files} Dateien)",
                    "classifying": f"Dokumente werden kategorisiert ({progress.processed_files}/{progress.total_files})",
                    "chunking": f"Texte werden in Abschnitte aufgeteilt ({progress.processed_files}/{progress.total_files})",
                    "embedding": f"Vektoren werden generiert ({progress.processed_files}/{progress.total_files} Dateien)",
                    "loading": f"Daten werden geladen ({progress.processed_files}/{progress.total_files} Dateien)",
                }

                # Generate AI explanation using Claude
                explanation = await generate_ai_explanation(
                    f"Phase: {progress.current_phase}, Dateien: {progress.processed_files}/{progress.total_files}, Status: {progress.status.value}"
                )

                await send_progress_update(customer_id, {
                    "type": "ingestion",
                    "progress": 20 + int(progress.progress_percent * 0.7),  # 20-90%
                    "message": phase_messages.get(progress.current_phase, f"{progress.current_phase} ({progress.processed_files}/{progress.total_files})"),
                    "phase": progress.current_phase,
                    "explanation": explanation,
                    "files_processed": progress.processed_files,
                    "files_total": progress.total_files,
                    "current_file": getattr(progress, 'current_file', None)
                })

            orchestrator.on_progress(lambda p: asyncio.create_task(stream_progress(p)))

            # Run ingestion
            logger.info(f"Running ingestion pipeline for {customer_id}...")

            await send_progress_update(customer_id, {
                "type": "ingestion",
                "progress": 20,
                "message": "Datenanalyse startet...",
                "phase": "starting",
                "explanation": "Jetzt beginnt die intelligente Verarbeitung Ihrer Dokumente."
            })

            result = await orchestrator.ingest(folder_configs, customer_id=customer_id)

            logger.info(
                f"✓ Ingestion complete for {customer_id}: "
                f"{result.processed_files} files processed, "
                f"{result.failed_files} failures"
            )

            # Send completion
            await send_progress_update(customer_id, {
                "type": "ingestion",
                "progress": 100,
                "message": f"✓ {result.processed_files} Dateien verarbeitet!",
                "phase": "complete",
                "explanation": f"Perfekt! {result.processed_files} Dokumente wurden analysiert und sind jetzt durchsuchbar. Die KI kann jetzt auf Ihre Daten zugreifen und Fragen beantworten.",
                "files_processed": result.processed_files,
                "files_total": result.processed_files + result.failed_files,
                "files_failed": result.failed_files,
                "stats": f"{result.processed_files} erfolgreich, {result.failed_files} Fehler"
            })

            return {
                "success": True,
                "customer_id": customer_id,
                "files_processed": result.processed_files,
                "files_failed": result.failed_files,
                "stats_by_mcp": result.stats_by_mcp
            }

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp dir: {temp_dir}")

    except Exception as e:
        logger.error(f"Background ingestion failed for {customer_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/files")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    customer_id: str = "default",
    selected_mcps: str = "general"  # Comma-separated list of MCPs
):
    """
    Upload multiple files to MinIO and trigger ingestion
    Background task processes files and loads them into lakehouse
    """
    logger.info(f"=== UPLOAD START === Customer: {customer_id}, Files: {len(files)}")

    try:
        logger.info("Getting MinIO client...")
        minio = get_minio_client()
        logger.info("✓ MinIO client ready")

        # Check if this is the first upload for this customer
        customer_bucket = f"customer-{customer_id}"
        is_first_upload = False

        try:
            # Check if bucket exists (MinIO 7.2+ requires keyword args)
            bucket_exists = minio.bucket_exists(bucket_name=customer_bucket)
            if not bucket_exists:
                minio.make_bucket(bucket_name=customer_bucket)
                is_first_upload = True
                logger.info(f"🚀 FIRST UPLOAD for {customer_id} - Triggering installation!")
        except S3Error as e:
            logger.warning(f"Bucket check/creation warning: {e}")
            pass
        except Exception as e:
            logger.error(f"Unexpected error checking bucket: {e}")
            # Continue anyway - bucket might exist

        uploaded_files = []

        logger.info(f"Processing {len(files)} files...")

        # Import progress updates
        from api.routes.progress_ws import send_progress_update

        total_files = len(files)

        for idx, file in enumerate(files):
            logger.info(f"  [{idx+1}/{len(files)}] Processing: {file.filename}")

            # Send upload progress
            upload_progress = int(((idx + 1) / total_files) * 100)
            await send_progress_update(customer_id, {
                "type": "upload",
                "progress": upload_progress,
                "message": f"{idx + 1}/{total_files} Dateien hochgeladen",
                "phase": "uploading",
                "current_file": file.filename,
                "explanation": f"Datei '{file.filename}' wird in den sicheren Speicher übertragen."
            })

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            logger.info(f"      Read {file_size} bytes")

            # Create object name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"{timestamp}_{file.filename}"

            # Upload to customer's bucket in MinIO
            logger.info(f"      Uploading to MinIO: {customer_bucket}/{object_name}")
            minio.put_object(
                bucket_name=customer_bucket,
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=file.content_type or "application/octet-stream"
            )
            logger.info(f"      ✓ Uploaded successfully!")

            uploaded_files.append({
                "filename": file.filename,
                "size": file_size,
                "path": f"s3://{customer_bucket}/{object_name}",
                "object_name": object_name,
                "content_type": file.content_type,
                "bucket": customer_bucket
            })

        logger.info(f"✓ All {len(uploaded_files)} files uploaded to MinIO")

        # Final upload complete notification
        await send_progress_update(customer_id, {
            "type": "upload",
            "progress": 100,
            "message": f"Alle {total_files} Dateien hochgeladen!",
            "phase": "complete",
            "explanation": "Upload abgeschlossen. Die Datenanalyse beginnt jetzt."
        })

        # Parse selected MCPs
        mcp_list = [m.strip() for m in selected_mcps.split(",") if m.strip()]

        # Trigger ingestion in background
        logger.info(f"🔄 Scheduling background ingestion for {customer_id} with MCPs: {mcp_list}")
        background_tasks.add_task(trigger_ingestion, customer_id, customer_bucket, mcp_list)

        response = {
            "success": True,
            "message": f"{len(uploaded_files)} files uploaded. Ingestion started in background.",
            "files": uploaded_files,
            "bucket": customer_bucket,
            "ingestion_triggered": True,
            "selected_mcps": mcp_list
        }

        # If first upload, trigger REAL deployment
        if is_first_upload:
            response["installation_triggered"] = True
            response["message"] = f"🚀 First upload! {len(uploaded_files)} files uploaded. Installation starting for customer {customer_id}."
            logger.info(f"📦 Installation triggered for customer {customer_id}")

            # Trigger deployment orchestrator with progress updates
            try:
                from provisioning.api.services.deployment_orchestrator import CustomerDeploymentOrchestrator

                # Send deployment start
                await send_progress_update(customer_id, {
                    "type": "deployment",
                    "progress": 10,
                    "message": "Deployment wird vorbereitet...",
                    "phase": "initializing",
                    "explanation": "Wir richten jetzt Ihre persönliche KI-Umgebung ein. Das beinhaltet Datenbank, KI-Modelle und Services."
                })

                orchestrator = CustomerDeploymentOrchestrator()

                await send_progress_update(customer_id, {
                    "type": "deployment",
                    "progress": 30,
                    "message": "Docker Container werden erstellt...",
                    "phase": "provisioning",
                    "explanation": "Wir starten isolierte Container für Ihre Daten: Lakehouse (Wissensdatenbank), Embeddings (Textverarbeitung) und vLLM (KI-Modell)."
                })

                # Deploy with selected MCPs
                deployment_info = await orchestrator.deploy_customer(
                    customer_id=customer_id,
                    company_name=f"Customer {customer_id}",
                    selected_mcps=mcp_list or ["etim"],
                    uploaded_files_bucket=customer_bucket,
                    deployment_type="managed"
                )

                await send_progress_update(customer_id, {
                    "type": "deployment",
                    "progress": 80,
                    "message": "Services werden gestartet...",
                    "phase": "starting",
                    "explanation": "Die Container sind bereit. Services werden hochgefahren und verbunden."
                })

                response["deployment"] = deployment_info
                logger.info(f"✓ Deployment initiated: {deployment_info.get('ports', {})}")

                await send_progress_update(customer_id, {
                    "type": "deployment",
                    "progress": 100,
                    "message": "✓ Deployment abgeschlossen!",
                    "phase": "complete",
                    "explanation": "Perfekt! Ihre KI-Umgebung ist jetzt aktiv und einsatzbereit."
                })

            except Exception as e:
                logger.error(f"Deployment trigger failed: {e}")

                await send_progress_update(customer_id, {
                    "type": "deployment",
                    "progress": 0,
                    "message": "Deployment übersprungen",
                    "phase": "skipped",
                    "explanation": "Deployment wird später automatisch gestartet."
                })
                # Don't fail upload if deployment fails
                response["deployment_error"] = str(e)

        return response

    except S3Error as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_uploaded_files():
    """
    List all uploaded files from MinIO
    """
    try:
        minio = get_minio_client()
        files = []
        objects = minio.list_objects(bucket_name=BUCKET_NAME)

        for obj in objects:
            files.append({
                "filename": obj.object_name,
                "size": obj.size,
                "path": f"s3://{BUCKET_NAME}/{obj.object_name}",
                "bucket": BUCKET_NAME,
                "modified": obj.last_modified.isoformat() if obj.last_modified else None
            })

        return {
            "success": True,
            "count": len(files),
            "files": files,
            "bucket": BUCKET_NAME
        }

    except S3Error as e:
        logger.error(f"MinIO list error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-ingestion")
async def trigger_ingestion_endpoint(
    customer_id: str,
    selected_mcps: str = "general",
    background_tasks: BackgroundTasks = None
):
    """
    Manually trigger ingestion for files already in MinIO
    Called by console frontend "Process files" button
    """
    try:
        bucket_name = f"customer-{customer_id}"
        mcp_list = [m.strip() for m in selected_mcps.split(",") if m.strip()]

        logger.info(f"🚀 Manual ingestion trigger for {customer_id}, bucket: {bucket_name}, MCPs: {mcp_list}")

        # Trigger ingestion (bucket check happens in trigger_ingestion function)
        minio = get_minio_client()

        # Trigger ingestion in background
        background_tasks.add_task(trigger_ingestion, customer_id, bucket_name, mcp_list)

        return {
            "success": True,
            "message": "Ingestion started in background",
            "customer_id": customer_id,
            "bucket": bucket_name,
            "selected_mcps": mcp_list
        }

    except Exception as e:
        logger.error(f"Trigger ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_uploads():
    """
    Clear all uploaded files from MinIO (development only)
    """
    try:
        minio = get_minio_client()
        count = 0
        objects = minio.list_objects(bucket_name=BUCKET_NAME)

        for obj in objects:
            minio.remove_object(bucket_name=BUCKET_NAME, object_name=obj.object_name)
            count += 1

        return {
            "success": True,
            "message": f"Deleted {count} files from MinIO"
        }

    except S3Error as e:
        logger.error(f"MinIO clear error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        logger.error(f"Clear uploads error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
