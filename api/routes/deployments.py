"""
Deployment routes
Handles customer deployment management, license validation, heartbeats
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from ..database import get_db
from ..models.deployment import Deployment
from ..models.usage import UsageMetric
from ..schemas.deployment import DeploymentResponse, DeploymentCreate
from ..utils.security import get_current_customer_id
from ..services.license_service import LicenseService

router = APIRouter()


class HeartbeatRequest(BaseModel):
    """Heartbeat request from customer instance"""
    deployment_id: UUID
    license_key: str
    version: str
    storage_used_bytes: int
    query_count: Optional[int] = 0
    mcp_calls: Optional[dict] = None


class LicenseValidationRequest(BaseModel):
    """License validation request"""
    license_key: str


class LicenseValidationResponse(BaseModel):
    """License validation response"""
    valid: bool
    deployment_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    plan: Optional[str] = None
    mcps_enabled: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    days_until_expiration: Optional[int] = None
    message: Optional[str] = None


@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """List all deployments for customer"""
    deployments = db.query(Deployment).filter(
        Deployment.customer_id == customer_id
    ).order_by(Deployment.created_at.desc()).all()

    return [DeploymentResponse.from_orm(d) for d in deployments]


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get deployment details"""
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.customer_id == customer_id
    ).first()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment nicht gefunden"
        )

    return DeploymentResponse.from_orm(deployment)


@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new deployment

    Generates a license key and sets up a new instance.
    Works for both direct customers and partner-managed customers.
    """
    from ..models.customer import Customer
    from ..models.user import User, UserRole
    from ..utils.security import get_current_user, Security, HTTPBearer

    # Get current user (could be customer_admin or partner_admin)
    from fastapi.security import HTTPAuthorizationCredentials
    from fastapi import Request
    import inspect

    # Customer ID must be provided in request body
    target_customer_id = deployment_data.customer_id

    if not target_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_id is required in request body"
        )

    # Get customer
    customer = db.query(Customer).filter(Customer.id == target_customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Generate license key
    license_key = LicenseService.generate_license_key(
        customer_id=str(customer.id),
        plan=customer.tier
    )

    license_expires = LicenseService.calculate_expiration(customer.tier)

    # Create deployment
    deployment = Deployment(
        customer_id=customer.id,
        name=deployment_data.name,
        deployment_type=deployment_data.deployment_type,
        cloud_provider=deployment_data.cloud_provider,
        region=deployment_data.region,
        version="1.0.0",
        license_key=license_key,
        license_expires_at=license_expires,
        status="provisioning",
        mcps_enabled=deployment_data.mcps_enabled or []
    )

    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # Trigger deployment orchestration in background
    try:
        from provisioning.api.services.deployment_orchestrator import CustomerDeploymentOrchestrator

        orchestrator = CustomerDeploymentOrchestrator()

        # Deploy customer stack (vLLM, Lakehouse, Embeddings)
        deployment_info = await orchestrator.deploy_customer(
            customer_id=str(customer.id),
            company_name=customer.company_name,
            selected_mcps=[],  # Partners can configure MCPs later
            uploaded_files_bucket=f"customer-{customer.id}",
            deployment_type="managed"
        )

        # Update deployment with service URLs
        deployment.status = "active"
        deployment.mcps_enabled = deployment_info.get("enabled_mcps", [])
        db.commit()
        db.refresh(deployment)

    except Exception as e:
        # Log error but don't fail the deployment creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Deployment orchestration failed: {e}")
        # Deployment stays in 'provisioning' status

    return DeploymentResponse.from_orm(deployment)


@router.post("/heartbeat")
async def deployment_heartbeat(
    request: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    Receive heartbeat from customer instance

    Updates deployment status and records usage metrics.
    """
    # Validate deployment and license
    deployment = db.query(Deployment).filter(
        Deployment.id == request.deployment_id,
        Deployment.license_key == request.license_key
    ).first()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Deployment ID oder Lizenzschlüssel"
        )

    # Check license expiration
    if LicenseService.is_license_expired(deployment.license_expires_at):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lizenz abgelaufen. Bitte erneuern Sie Ihr Abonnement."
        )

    # Update deployment
    deployment.last_heartbeat_at = datetime.utcnow()
    deployment.version = request.version
    deployment.storage_used_bytes = request.storage_used_bytes

    # Update status to active if it was provisioning
    if deployment.status == "provisioning":
        deployment.status = "active"

    db.commit()

    # Record usage metrics if provided
    if request.query_count or request.mcp_calls:
        # Get or create hourly usage metric
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        next_hour = current_hour.replace(hour=current_hour.hour + 1)

        usage = db.query(UsageMetric).filter(
            UsageMetric.deployment_id == deployment.id,
            UsageMetric.period_start == current_hour
        ).first()

        if not usage:
            usage = UsageMetric(
                deployment_id=deployment.id,
                customer_id=deployment.customer_id,
                period_start=current_hour,
                period_end=next_hour,
                query_count=0,
                mcp_calls={},
                storage_bytes=0
            )
            db.add(usage)

        # Update metrics
        usage.query_count += request.query_count or 0
        usage.storage_bytes = request.storage_used_bytes

        if request.mcp_calls:
            current_mcp_calls = usage.mcp_calls or {}
            for mcp, count in request.mcp_calls.items():
                current_mcp_calls[mcp] = current_mcp_calls.get(mcp, 0) + count
            usage.mcp_calls = current_mcp_calls

        db.commit()

    return {
        "status": "ok",
        "deployment_status": deployment.status,
        "license_valid": True,
        "days_until_expiration": LicenseService.days_until_expiration(
            deployment.license_expires_at
        )
    }


@router.post("/validate-license", response_model=LicenseValidationResponse)
async def validate_license(
    request: LicenseValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a license key

    Public endpoint for customer instances to validate their license.
    """
    # Validate format
    if not LicenseService.validate_license_format(request.license_key):
        return LicenseValidationResponse(
            valid=False,
            message="Ungültiges Lizenzschlüssel-Format"
        )

    # Find deployment with this license
    deployment = db.query(Deployment).filter(
        Deployment.license_key == request.license_key
    ).first()

    if not deployment:
        return LicenseValidationResponse(
            valid=False,
            message="Lizenzschlüssel nicht gefunden"
        )

    # Check expiration
    if LicenseService.is_license_expired(deployment.license_expires_at):
        return LicenseValidationResponse(
            valid=False,
            deployment_id=deployment.id,
            message="Lizenz abgelaufen"
        )

    # Check deployment status
    if deployment.status in ["suspended", "terminated"]:
        return LicenseValidationResponse(
            valid=False,
            deployment_id=deployment.id,
            message=f"Deployment Status: {deployment.status}"
        )

    # Get customer plan
    from ..models.customer import Customer
    customer = db.query(Customer).filter(Customer.id == deployment.customer_id).first()

    return LicenseValidationResponse(
        valid=True,
        deployment_id=deployment.id,
        customer_id=deployment.customer_id,
        plan=customer.tier if customer else None,
        mcps_enabled=deployment.mcps_enabled,
        expires_at=deployment.license_expires_at,
        days_until_expiration=LicenseService.days_until_expiration(
            deployment.license_expires_at
        ),
        message="Lizenz gültig"
    )


@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Delete (terminate) a deployment

    Marks deployment as terminated but preserves data for audit purposes.
    """
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.customer_id == customer_id
    ).first()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment nicht gefunden"
        )

    # Mark as terminated instead of actually deleting
    deployment.status = "terminated"
    db.commit()

    return {"message": "Deployment erfolgreich gelöscht"}


@router.get("/{deployment_id}/usage")
async def get_deployment_usage(
    deployment_id: UUID,
    days: int = 30,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for a deployment

    Args:
        deployment_id: Deployment ID
        days: Number of days to look back (default 30)
    """
    from datetime import timedelta

    # Verify deployment belongs to customer
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.customer_id == customer_id
    ).first()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment nicht gefunden"
        )

    # Get usage metrics
    start_date = datetime.utcnow() - timedelta(days=days)

    metrics = db.query(UsageMetric).filter(
        UsageMetric.deployment_id == deployment_id,
        UsageMetric.period_start >= start_date
    ).order_by(UsageMetric.period_start).all()

    # Aggregate metrics
    total_queries = sum(m.query_count for m in metrics)
    total_storage = deployment.storage_used_bytes

    # Aggregate MCP calls
    mcp_calls_total = {}
    for metric in metrics:
        if metric.mcp_calls:
            for mcp, count in metric.mcp_calls.items():
                mcp_calls_total[mcp] = mcp_calls_total.get(mcp, 0) + count

    return {
        "deployment_id": str(deployment_id),
        "period_days": days,
        "total_queries": total_queries,
        "storage_bytes": total_storage,
        "mcp_calls": mcp_calls_total,
        "daily_metrics": [
            {
                "date": m.period_start.date().isoformat(),
                "queries": m.query_count,
                "mcp_calls": m.mcp_calls or {}
            }
            for m in metrics
        ]
    }
