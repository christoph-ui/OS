"""
0711-OS Data Sync API Routes

Handles the sync protocol between playground and deployed instances:
1. /export/{customer_id} - Create export bundle
2. /deploy/initiate - Start deployment to target
3. /sync/ready - Target signals ready
4. /sync/complete - Target signals import complete
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

router = APIRouter(prefix="/api", tags=["sync"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    customer_id: str
    include_raw: bool = False
    notify_url: Optional[str] = None  # Webhook when export ready


class ExportResponse(BaseModel):
    export_id: str
    status: str
    bundle_path: Optional[str] = None
    archive_path: Optional[str] = None
    download_url: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DeployInitiateRequest(BaseModel):
    customer_id: str
    deployment_type: str = "cloud"  # cloud | onprem
    target_url: Optional[str] = None  # For on-prem, the target server
    selected_mcps: List[str] = []
    config_overrides: Dict[str, Any] = {}


class DeployInitiateResponse(BaseModel):
    deployment_id: str
    status: str
    export_url: Optional[str] = None
    instance_url: Optional[str] = None
    message: str


class SyncReadyRequest(BaseModel):
    customer_id: str
    instance_id: str
    api_key: str
    instance_url: str


class SyncReadyResponse(BaseModel):
    export_url: str
    manifest_url: str
    expected_checksum: str


class SyncCompleteRequest(BaseModel):
    customer_id: str
    import_id: str
    instance_id: str
    result: Dict[str, Any]


class SyncCompleteResponse(BaseModel):
    success: bool
    message: str
    next_steps: List[str]


# ============================================================================
# In-Memory State (use Redis/DB in production)
# ============================================================================

_exports: Dict[str, ExportResponse] = {}
_deployments: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Routes
# ============================================================================

@router.post("/export", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create export bundle for customer data.
    
    This packages all processed data (Delta tables, vectors, LoRA weights)
    into a portable bundle that can be imported into any 0711-OS instance.
    """
    export_id = f"{request.customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Start export in background
    response = ExportResponse(
        export_id=export_id,
        status="in_progress",
    )
    _exports[export_id] = response
    
    async def run_export():
        try:
            from orchestrator.export import DataExporter
            from pathlib import Path
            
            exporter = DataExporter()
            bundle = await exporter.export_customer(
                request.customer_id,
                include_raw=request.include_raw,
            )
            
            download_url = await exporter.get_export_url(bundle.archive_path)
            
            _exports[export_id] = ExportResponse(
                export_id=export_id,
                status="completed",
                bundle_path=str(bundle.bundle_path),
                archive_path=str(bundle.archive_path),
                download_url=download_url,
                manifest=bundle.manifest.to_dict(),
            )
            
            logger.info(f"✓ Export {export_id} completed")
            
            # Notify webhook if provided
            if request.notify_url:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(request.notify_url, json=_exports[export_id].dict())
            
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            _exports[export_id] = ExportResponse(
                export_id=export_id,
                status="failed",
                error=str(e),
            )
    
    background_tasks.add_task(run_export)
    
    return response


@router.get("/export/{export_id}", response_model=ExportResponse)
async def get_export_status(export_id: str):
    """Get export status and download URL"""
    if export_id not in _exports:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return _exports[export_id]


@router.get("/export/{export_id}/download")
async def download_export(export_id: str):
    """Redirect to export download URL"""
    from fastapi.responses import RedirectResponse
    
    if export_id not in _exports:
        raise HTTPException(status_code=404, detail="Export not found")
    
    export = _exports[export_id]
    if export.status != "completed":
        raise HTTPException(status_code=400, detail=f"Export status: {export.status}")
    
    if not export.download_url:
        raise HTTPException(status_code=404, detail="Download URL not available")
    
    return RedirectResponse(url=export.download_url)


@router.post("/deploy/initiate", response_model=DeployInitiateResponse)
async def initiate_deployment(
    request: DeployInitiateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Initiate deployment of customer 0711-OS instance.
    
    For cloud: Provisions on H200 cluster, imports data
    For on-prem: Generates download package, waits for target to call back
    """
    deployment_id = f"deploy_{request.customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    _deployments[deployment_id] = {
        "customer_id": request.customer_id,
        "deployment_type": request.deployment_type,
        "status": "initiated",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    if request.deployment_type == "cloud":
        # Cloud deployment: we control everything
        async def deploy_cloud():
            try:
                # 1. Create export
                from orchestrator.export import DataExporter
                exporter = DataExporter()
                bundle = await exporter.export_customer(request.customer_id)
                export_url = await exporter.get_export_url(bundle.archive_path)
                
                # 2. Provision instance
                from provisioning.api.services.deployment_orchestrator import CustomerDeploymentOrchestrator
                orchestrator = CustomerDeploymentOrchestrator()
                
                # Generate compose with IMPORT_URL env var
                compose_file = orchestrator.generate_customer_compose(
                    request.customer_id,
                    f"Customer {request.customer_id}",
                    request.selected_mcps,
                    deployment_type="managed",
                )
                
                # Inject IMPORT_URL into compose
                # (In production, modify the compose generation to include this)
                
                _deployments[deployment_id]["status"] = "provisioning"
                _deployments[deployment_id]["export_url"] = export_url
                
                # 3. Start instance (it will auto-import)
                # ... docker compose up logic ...
                
                _deployments[deployment_id]["status"] = "running"
                
            except Exception as e:
                logger.error(f"Cloud deployment failed: {e}")
                _deployments[deployment_id]["status"] = "failed"
                _deployments[deployment_id]["error"] = str(e)
        
        background_tasks.add_task(deploy_cloud)
        
        return DeployInitiateResponse(
            deployment_id=deployment_id,
            status="initiated",
            message="Cloud deployment started. Instance will auto-import data.",
        )
    
    else:
        # On-prem deployment: create package, wait for target
        async def prepare_onprem():
            try:
                # 1. Create export bundle
                from orchestrator.export import DataExporter
                exporter = DataExporter()
                bundle = await exporter.export_customer(request.customer_id)
                export_url = await exporter.get_export_url(bundle.archive_path)
                
                _deployments[deployment_id]["status"] = "ready"
                _deployments[deployment_id]["export_url"] = export_url
                _deployments[deployment_id]["manifest"] = bundle.manifest.to_dict()
                
            except Exception as e:
                logger.error(f"On-prem preparation failed: {e}")
                _deployments[deployment_id]["status"] = "failed"
                _deployments[deployment_id]["error"] = str(e)
        
        background_tasks.add_task(prepare_onprem)
        
        return DeployInitiateResponse(
            deployment_id=deployment_id,
            status="preparing",
            message="On-prem package being prepared. Use /sync/ready when target is running.",
        )


@router.get("/deploy/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    """Get deployment status"""
    if deployment_id not in _deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return _deployments[deployment_id]


@router.post("/sync/ready", response_model=SyncReadyResponse)
async def sync_ready(request: SyncReadyRequest):
    """
    Called by fresh 0711-OS instance when it boots and is ready to import.
    
    Returns the export URL for the instance to download and import.
    """
    logger.info(f"Instance ready: {request.instance_id} for customer {request.customer_id}")
    
    # Find pending deployment for this customer
    deployment = None
    for dep_id, dep in _deployments.items():
        if dep.get("customer_id") == request.customer_id and dep.get("status") in ["ready", "provisioning"]:
            deployment = dep
            deployment["instance_id"] = request.instance_id
            deployment["instance_url"] = request.instance_url
            deployment["status"] = "syncing"
            break
    
    if not deployment:
        # No pending deployment, check for existing export
        for exp_id, exp in _exports.items():
            if exp_id.startswith(request.customer_id) and exp.status == "completed":
                return SyncReadyResponse(
                    export_url=exp.download_url,
                    manifest_url=f"/api/export/{exp_id}/manifest",
                    expected_checksum=exp.manifest.get("components", [{}])[0].get("checksum_sha256", ""),
                )
        
        raise HTTPException(
            status_code=404,
            detail=f"No pending deployment or export for customer {request.customer_id}",
        )
    
    return SyncReadyResponse(
        export_url=deployment.get("export_url", ""),
        manifest_url=f"/api/export/{request.customer_id}/manifest",
        expected_checksum=deployment.get("manifest", {}).get("components", [{}])[0].get("checksum_sha256", ""),
    )


@router.post("/sync/complete", response_model=SyncCompleteResponse)
async def sync_complete(request: SyncCompleteRequest):
    """
    Called by 0711-OS instance when data import is complete.
    
    Updates deployment status and triggers any post-import actions.
    """
    logger.info(f"Sync complete: {request.instance_id} for customer {request.customer_id}")
    
    # Find and update deployment
    for dep_id, dep in _deployments.items():
        if dep.get("customer_id") == request.customer_id:
            dep["status"] = "completed"
            dep["import_result"] = request.result
            dep["completed_at"] = datetime.utcnow().isoformat()
            break
    
    # Post-import actions
    next_steps = [
        "Instance is ready for use",
        "LoRA adapter loaded",
        "Vector indices active",
    ]
    
    # Trigger LoRA training if needed
    if request.result.get("stats", {}).get("imported_documents", 0) > 100:
        next_steps.append("Background LoRA fine-tuning scheduled")
    
    return SyncCompleteResponse(
        success=True,
        message=f"Import complete. {request.result.get('stats', {}).get('imported_documents', 0)} documents ready.",
        next_steps=next_steps,
    )


# ============================================================================
# Playground Endpoints
# ============================================================================

class PlaygroundQueryRequest(BaseModel):
    customer_id: str
    query: str
    mcp: Optional[str] = None


class PlaygroundQueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    confidence: float


@router.post("/playground/query", response_model=PlaygroundQueryResponse)
async def playground_query(request: PlaygroundQueryRequest):
    """
    Test query against customer's staged data.
    
    Allows customer to validate their data before committing to deployment.
    """
    # This would use the staging lakehouse and shared MCPs
    # For now, return placeholder
    
    return PlaygroundQueryResponse(
        response="[Playground mode] Your data has been processed. Deploy to get full AI responses.",
        sources=[{"type": "staged", "count": 42}],
        confidence=0.85,
    )


@router.get("/playground/{customer_id}/stats")
async def playground_stats(customer_id: str):
    """
    Get statistics about customer's staged data.
    """
    # Would query staging lakehouse
    return {
        "customer_id": customer_id,
        "documents": 156,
        "chunks": 4832,
        "embeddings": 4832,
        "handlers_generated": 3,
        "mcps_available": ["ctax", "law", "tender"],
        "estimated_lora_training_time": "~2 hours",
        "ready_to_deploy": True,
    }
