"""
Admin routes
Internal admin console for customer management, billing, analytics
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from uuid import UUID

from ..database import get_db
from ..models.customer import Customer
from ..models.subscription import Subscription
from ..models.deployment import Deployment
from ..models.invoice import Invoice
from ..models.usage import UsageMetric
from ..models.mcp import MCP
from ..models.mcp_developer import MCPDeveloper
from ..models.workflow import Workflow
from ..models.user import User
from ..schemas.customer import CustomerDetailResponse
from ..schemas.subscription import SubscriptionResponse
from ..schemas.deployment import DeploymentResponse
from ..utils.security import require_admin, get_current_user
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
from pathlib import Path as FilePath

router = APIRouter(dependencies=[Depends(require_admin)])


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_customers: int
    active_deployments: int
    mrr_cents: int
    arr_cents: int
    new_customers_this_week: int
    churn_rate: float
    healthy_deployments: int
    unhealthy_deployments: int


class RevenueMetrics(BaseModel):
    """Revenue metrics"""
    month: str
    mrr_cents: int
    new_mrr_cents: int
    churned_mrr_cents: int
    arr_cents: int


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics

    Returns overview metrics for the admin dashboard.
    """
    # Total customers
    total_customers = db.query(func.count(Customer.id)).scalar()

    # Active deployments
    active_deployments = db.query(func.count(Deployment.id)).filter(
        Deployment.status == "active"
    ).scalar()

    # Healthy vs unhealthy deployments
    # Unhealthy = no heartbeat in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)

    healthy_deployments = db.query(func.count(Deployment.id)).filter(
        and_(
            Deployment.status == "active",
            Deployment.last_heartbeat_at >= yesterday
        )
    ).scalar()

    unhealthy_deployments = db.query(func.count(Deployment.id)).filter(
        and_(
            Deployment.status == "active",
            Deployment.last_heartbeat_at < yesterday
        )
    ).scalar()

    # MRR (Monthly Recurring Revenue)
    active_subs = db.query(Subscription).filter(
        Subscription.status == "active"
    ).all()

    mrr_cents = sum(
        sub.price_monthly_cents or 0
        if sub.billing_cycle == "monthly"
        else (sub.price_annual_cents or 0) // 12
        for sub in active_subs
    )

    # ARR (Annual Recurring Revenue)
    arr_cents = mrr_cents * 12

    # New customers this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_customers_this_week = db.query(func.count(Customer.id)).filter(
        Customer.created_at >= week_ago
    ).scalar()

    # Churn rate (simplified - customers who churned this month / total customers)
    month_ago = datetime.utcnow() - timedelta(days=30)
    churned_count = db.query(func.count(Customer.id)).filter(
        and_(
            Customer.status == "churned",
            Customer.updated_at >= month_ago
        )
    ).scalar()

    churn_rate = (churned_count / total_customers * 100) if total_customers > 0 else 0.0

    return DashboardStats(
        total_customers=total_customers,
        active_deployments=active_deployments,
        mrr_cents=mrr_cents,
        arr_cents=arr_cents,
        new_customers_this_week=new_customers_this_week,
        churn_rate=round(churn_rate, 2),
        healthy_deployments=healthy_deployments,
        unhealthy_deployments=unhealthy_deployments
    )


@router.get("/customers", response_model=List[CustomerDetailResponse])
async def list_all_customers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all customers with filtering

    Args:
        skip: Pagination offset
        limit: Number of results
        status: Filter by status (active, churned, suspended)
        tier: Filter by tier (starter, professional, business, enterprise)
        search: Search by company name or email
    """
    query = db.query(Customer)

    if status:
        query = query.filter(Customer.status == status)

    if tier:
        query = query.filter(Customer.tier == tier)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Customer.company_name.ilike(search_term)) |
            (Customer.contact_email.ilike(search_term))
        )

    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()

    return [CustomerDetailResponse.from_orm(c) for c in customers]


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer_detail(
    customer_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed customer information"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return CustomerDetailResponse.from_orm(customer)


@router.get("/customers/{customer_id}/full")
async def get_customer_full_view(
    customer_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get full 360° customer view

    Returns customer info, subscription, deployments, invoices, and usage.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == customer_id
    ).order_by(Subscription.created_at.desc()).first()

    # Get deployments
    deployments = db.query(Deployment).filter(
        Deployment.customer_id == customer_id
    ).all()

    # Get invoices
    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_id
    ).order_by(Invoice.created_at.desc()).limit(10).all()

    # Get usage this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_metrics = db.query(UsageMetric).filter(
        and_(
            UsageMetric.customer_id == customer_id,
            UsageMetric.period_start >= month_start
        )
    ).all()

    # Aggregate usage
    total_queries = sum(m.query_count for m in usage_metrics)
    total_storage = max((m.storage_bytes for m in usage_metrics), default=0)

    mcp_calls = {}
    for metric in usage_metrics:
        if metric.mcp_calls:
            for mcp, count in metric.mcp_calls.items():
                mcp_calls[mcp] = mcp_calls.get(mcp, 0) + count

    return {
        "customer": CustomerDetailResponse.from_orm(customer),
        "subscription": SubscriptionResponse.from_orm(subscription) if subscription else None,
        "deployments": [DeploymentResponse.from_orm(d) for d in deployments],
        "invoices": [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "total_cents": inv.total_cents,
                "payment_status": inv.payment_status,
                "due_date": inv.due_date.isoformat()
            }
            for inv in invoices
        ],
        "usage_this_month": {
            "queries": total_queries,
            "storage": total_storage,
            "mcp_calls": mcp_calls
        }
    }


@router.post("/customers/{customer_id}/suspend")
async def suspend_customer(
    customer_id: UUID,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Suspend a customer account

    Sets customer status to suspended and marks all deployments as suspended.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Update customer status
    customer.status = "suspended"

    # Suspend all deployments
    db.query(Deployment).filter(Deployment.customer_id == customer_id).update(
        {"status": "suspended"}
    )

    # Cancel active subscriptions
    db.query(Subscription).filter(
        and_(
            Subscription.customer_id == customer_id,
            Subscription.status == "active"
        )
    ).update({"status": "canceled", "canceled_at": datetime.utcnow()})

    db.commit()

    # TODO: Log audit event
    # TODO: Send notification email

    return {"message": f"Customer suspended: {reason}"}


@router.post("/customers/{customer_id}/reactivate")
async def reactivate_customer(
    customer_id: UUID,
    db: Session = Depends(get_db)
):
    """Reactivate a suspended customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    if customer.status != "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer is not suspended"
        )

    # Reactivate customer
    customer.status = "active"

    # Reactivate deployments
    db.query(Deployment).filter(
        and_(
            Deployment.customer_id == customer_id,
            Deployment.status == "suspended"
        )
    ).update({"status": "active"})

    db.commit()

    return {"message": "Customer reactivated"}


@router.get("/revenue/metrics", response_model=List[RevenueMetrics])
async def get_revenue_metrics(
    months: int = 12,
    db: Session = Depends(get_db)
):
    """
    Get revenue metrics over time

    Args:
        months: Number of months to look back
    """
    metrics = []

    for i in range(months):
        # Calculate month start/end
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start = month_start - timedelta(days=30 * i)

        # Get active subscriptions for this month
        active_subs = db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.created_at <= month_start
            )
        ).all()

        # Calculate MRR
        mrr = sum(
            sub.price_monthly_cents or 0
            if sub.billing_cycle == "monthly"
            else (sub.price_annual_cents or 0) // 12
            for sub in active_subs
        )

        # New MRR (subscriptions created this month)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)

        new_subs = db.query(Subscription).filter(
            and_(
                Subscription.created_at >= month_start,
                Subscription.created_at <= month_end
            )
        ).all()

        new_mrr = sum(
            sub.price_monthly_cents or 0
            if sub.billing_cycle == "monthly"
            else (sub.price_annual_cents or 0) // 12
            for sub in new_subs
        )

        # Churned MRR
        churned_subs = db.query(Subscription).filter(
            and_(
                Subscription.status == "canceled",
                Subscription.canceled_at >= month_start,
                Subscription.canceled_at <= month_end
            )
        ).all()

        churned_mrr = sum(
            sub.price_monthly_cents or 0
            if sub.billing_cycle == "monthly"
            else (sub.price_annual_cents or 0) // 12
            for sub in churned_subs
        )

        metrics.append(RevenueMetrics(
            month=month_start.strftime("%Y-%m"),
            mrr_cents=mrr,
            new_mrr_cents=new_mrr,
            churned_mrr_cents=churned_mrr,
            arr_cents=mrr * 12
        ))

    return list(reversed(metrics))


@router.get("/deployments/health")
async def get_deployments_health(
    db: Session = Depends(get_db)
):
    """
    Get deployment health overview

    Returns counts by status and health.
    """
    yesterday = datetime.utcnow() - timedelta(days=1)

    # Count by status
    status_counts = db.query(
        Deployment.status,
        func.count(Deployment.id)
    ).group_by(Deployment.status).all()

    # Count healthy (active with recent heartbeat)
    healthy = db.query(func.count(Deployment.id)).filter(
        and_(
            Deployment.status == "active",
            Deployment.last_heartbeat_at >= yesterday
        )
    ).scalar()

    # Count unhealthy (active but no recent heartbeat)
    unhealthy = db.query(func.count(Deployment.id)).filter(
        and_(
            Deployment.status == "active",
            Deployment.last_heartbeat_at < yesterday
        )
    ).scalar()

    return {
        "by_status": {status: count for status, count in status_counts},
        "healthy": healthy,
        "unhealthy": unhealthy,
        "total": sum(count for _, count in status_counts)
    }


@router.get("/invoices/pending")
async def get_pending_invoices(
    db: Session = Depends(get_db)
):
    """
    Get pending/overdue invoices

    Returns invoices that need attention.
    """
    today = datetime.utcnow().date()

    # Pending invoices
    pending = db.query(Invoice).filter(
        Invoice.payment_status == "pending"
    ).order_by(Invoice.due_date).all()

    # Overdue invoices
    overdue = [inv for inv in pending if inv.due_date < today]

    return {
        "pending_count": len(pending),
        "overdue_count": len(overdue),
        "pending": [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "customer_id": str(inv.customer_id),
                "total_cents": inv.total_cents,
                "due_date": inv.due_date.isoformat(),
                "overdue": inv.due_date < today
            }
            for inv in pending
        ]
    }


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark an invoice as paid"""
    from ..services.invoice_service import InvoiceService

    try:
        invoice = await InvoiceService.mark_invoice_paid(db, str(invoice_id))
        return {
            "message": "Invoice marked as paid",
            "invoice_number": invoice.invoice_number
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# MCP DEVELOPER & MARKETPLACE MANAGEMENT
# ============================================================================

@router.get("/mcp-developers/pending")
async def list_pending_developers(
    db: Session = Depends(get_db)
):
    """
    List pending MCP developer applications

    Platform admins can approve or reject developer registrations
    """
    pending_devs = db.query(MCPDeveloper).filter(
        MCPDeveloper.status == "pending"
    ).order_by(MCPDeveloper.created_at.desc()).all()

    return {
        "total": len(pending_devs),
        "developers": [
            {
                "id": str(dev.id),
                "company_name": dev.company_name,
                "developer_name": dev.developer_name,
                "email": dev.email,
                "website": dev.website,
                "github_url": dev.github_url,
                "expertise_areas": dev.expertise_areas,
                "created_at": dev.created_at.isoformat()
            }
            for dev in pending_devs
        ]
    }


@router.post("/mcp-developers/{developer_id}/verify")
async def verify_developer(
    developer_id: UUID,
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify (approve) an MCP developer

    Sets developer status to active and marks as verified
    """
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.id == developer_id
    ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )

    if developer.verified:
        return {"message": "Developer already verified"}

    # Verify developer
    developer.verified = True
    developer.verified_at = datetime.utcnow()
    developer.verified_by_id = admin.id
    developer.status = "active"

    db.commit()

    return {
        "success": True,
        "message": f"Developer {developer.company_name} verified",
        "developer_id": str(developer.id)
    }


@router.post("/mcp-developers/{developer_id}/reject")
async def reject_developer(
    developer_id: UUID,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Reject an MCP developer application

    Sets status to suspended with rejection reason
    """
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.id == developer_id
    ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )

    developer.status = "suspended"

    db.commit()

    return {
        "success": True,
        "message": f"Developer {developer.company_name} rejected",
        "reason": reason
    }


@router.get("/mcps/pending")
async def list_pending_mcps(
    db: Session = Depends(get_db)
):
    """
    List pending MCP submissions

    Returns MCPs awaiting platform admin approval
    """
    pending_mcps = db.query(MCP).filter(
        MCP.approval_status == "pending"
    ).order_by(MCP.submitted_at.desc()).all()

    return {
        "total": len(pending_mcps),
        "mcps": [
            {
                "id": str(mcp.id),
                "name": mcp.name,
                "display_name": mcp.display_name,
                "version": mcp.version,
                "description": mcp.description,
                "category": mcp.category,
                "developer_id": str(mcp.developer_id),
                "developer": db.query(MCPDeveloper).filter(
                    MCPDeveloper.id == mcp.developer_id
                ).first().company_name if mcp.developer_id else None,
                "submitted_at": mcp.submitted_at.isoformat() if mcp.submitted_at else None,
                "pricing_model": mcp.pricing_model,
                "gpu_required": mcp.gpu_required
            }
            for mcp in pending_mcps
        ]
    }


@router.post("/mcps/{mcp_id}/approve")
async def approve_mcp(
    mcp_id: UUID,
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve an MCP for marketplace publication

    Sets approval_status to approved and publishes to marketplace
    """
    mcp = db.query(MCP).filter(MCP.id == mcp_id).first()

    if not mcp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP not found"
        )

    if mcp.approval_status == "approved":
        return {"message": "MCP already approved"}

    # Approve MCP
    mcp.approval_status = "approved"
    mcp.approved_at = datetime.utcnow()
    mcp.approved_by_id = admin.id
    mcp.published = True
    mcp.published_at = datetime.utcnow()

    # Update developer stats
    if mcp.developer_id:
        developer = db.query(MCPDeveloper).filter(
            MCPDeveloper.id == mcp.developer_id
        ).first()
        if developer:
            developer.published_mcps += 1

    db.commit()

    return {
        "success": True,
        "message": f"MCP {mcp.display_name} approved and published",
        "mcp_id": str(mcp.id)
    }


@router.post("/mcps/{mcp_id}/reject")
async def reject_mcp(
    mcp_id: UUID,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Reject an MCP submission

    Provides feedback to developer on why MCP was rejected
    """
    mcp = db.query(MCP).filter(MCP.id == mcp_id).first()

    if not mcp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP not found"
        )

    # Reject MCP
    mcp.approval_status = "rejected"
    mcp.rejection_reason = reason
    mcp.published = False

    db.commit()

    return {
        "success": True,
        "message": f"MCP {mcp.display_name} rejected",
        "mcp_id": str(mcp.id),
        "reason": reason
    }


@router.get("/mcps/stats")
async def get_mcp_marketplace_stats(
    db: Session = Depends(get_db)
):
    """
    Get marketplace statistics

    Returns counts of MCPs by status, developer stats, etc.
    """
    total_mcps = db.query(func.count(MCP.id)).scalar()
    approved_mcps = db.query(func.count(MCP.id)).filter(
        MCP.approval_status == "approved"
    ).scalar()
    pending_mcps = db.query(func.count(MCP.id)).filter(
        MCP.approval_status == "pending"
    ).scalar()
    rejected_mcps = db.query(func.count(MCP.id)).filter(
        MCP.approval_status == "rejected"
    ).scalar()

    total_developers = db.query(func.count(MCPDeveloper.id)).scalar()
    verified_developers = db.query(func.count(MCPDeveloper.id)).filter(
        MCPDeveloper.verified == True
    ).scalar()
    pending_developers = db.query(func.count(MCPDeveloper.id)).filter(
        MCPDeveloper.status == "pending"
    ).scalar()

    total_installations = db.query(func.sum(MCP.install_count)).scalar() or 0

    return {
        "mcps": {
            "total": total_mcps,
            "approved": approved_mcps,
            "pending": pending_mcps,
            "rejected": rejected_mcps
        },
        "developers": {
            "total": total_developers,
            "verified": verified_developers,
            "pending": pending_developers
        },
        "total_installations": total_installations
    }


# ============================================================================
# WORKFLOW MARKETPLACE MANAGEMENT
# ============================================================================

@router.get("/workflows/pending")
async def list_pending_workflows(
    db: Session = Depends(get_db)
):
    """
    List pending workflow submissions

    Returns workflows awaiting platform admin approval
    """
    from ..models.workflow_definition import WorkflowDefinition

    pending_workflows = db.query(Workflow).filter(
        Workflow.approval_status == "pending"
    ).order_by(Workflow.submitted_at.desc()).all()

    result = []
    for wf in pending_workflows:
        # Get definition
        definition = db.query(WorkflowDefinition).filter(
            WorkflowDefinition.workflow_id == wf.id,
            WorkflowDefinition.is_active == True
        ).first()

        # Get developer info
        developer = None
        if wf.developer_id:
            developer = db.query(MCPDeveloper).filter(
                MCPDeveloper.id == wf.developer_id
            ).first()

        result.append({
            "id": str(wf.id),
            "name": wf.name,
            "display_name": wf.display_name,
            "version": wf.version,
            "description": wf.description,
            "category": wf.category,
            "required_mcps": wf.required_mcps,
            "step_count": definition.step_count if definition else 0,
            "developer_id": str(wf.developer_id) if wf.developer_id else None,
            "developer": developer.company_name if developer else "0711 (First-party)",
            "submitted_at": wf.submitted_at.isoformat() if wf.submitted_at else None,
            "pricing_model": wf.pricing_model,
            "estimated_duration_minutes": wf.estimated_duration_minutes
        })

    return {
        "total": len(result),
        "workflows": result
    }


@router.post("/workflows/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: UUID,
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a workflow for marketplace publication

    Sets approval_status to approved and publishes to marketplace
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    if workflow.approval_status == "approved":
        return {"message": "Workflow already approved"}

    # Approve workflow
    workflow.approval_status = "approved"
    workflow.approved_at = datetime.utcnow()
    workflow.approved_by_id = admin.id
    workflow.published = True
    workflow.published_at = datetime.utcnow()

    # Update developer stats (if third-party)
    if workflow.developer_id:
        developer = db.query(MCPDeveloper).filter(
            MCPDeveloper.id == workflow.developer_id
        ).first()
        if developer:
            developer.published_mcps += 1  # Count workflows too

    db.commit()

    return {
        "success": True,
        "message": f"Workflow '{workflow.display_name}' approved and published",
        "workflow_id": str(workflow.id)
    }


@router.post("/workflows/{workflow_id}/reject")
async def reject_workflow(
    workflow_id: UUID,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Reject a workflow submission

    Provides feedback to developer on why workflow was rejected
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Reject workflow
    workflow.approval_status = "rejected"
    workflow.rejection_reason = reason
    workflow.published = False

    db.commit()

    return {
        "success": True,
        "message": f"Workflow '{workflow.display_name}' rejected",
        "workflow_id": str(workflow.id),
        "reason": reason
    }


@router.get("/workflows/stats")
async def get_workflow_marketplace_stats(
    db: Session = Depends(get_db)
):
    """
    Get workflow marketplace statistics

    Returns counts of workflows by status, category, etc.
    """
    from ..models.workflow_subscription import WorkflowSubscription
    from ..models.workflow_execution import WorkflowExecution

    total_workflows = db.query(func.count(Workflow.id)).scalar()
    approved_workflows = db.query(func.count(Workflow.id)).filter(
        Workflow.approval_status == "approved"
    ).scalar()
    pending_workflows = db.query(func.count(Workflow.id)).filter(
        Workflow.approval_status == "pending"
    ).scalar()
    rejected_workflows = db.query(func.count(Workflow.id)).filter(
        Workflow.approval_status == "rejected"
    ).scalar()

    total_subscriptions = db.query(func.count(WorkflowSubscription.id)).filter(
        WorkflowSubscription.status == "active"
    ).scalar()

    total_executions = db.query(func.count(WorkflowExecution.id)).scalar()
    completed_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.status == "completed"
    ).scalar()
    failed_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.status == "failed"
    ).scalar()

    return {
        "workflows": {
            "total": total_workflows,
            "approved": approved_workflows,
            "pending": pending_workflows,
            "rejected": rejected_workflows
        },
        "subscriptions": {
            "total": total_subscriptions
        },
        "executions": {
            "total": total_executions,
            "completed": completed_executions,
            "failed": failed_executions,
            "success_rate": (completed_executions / total_executions * 100) if total_executions > 0 else 100.0
        }
    }


# =============================================================================
# CRADLE INTEGRATION (Client Deployment Management)
# =============================================================================

class CradleInstallation(BaseModel):
    """Cradle installation info"""
    customer_id: str
    company_name: str
    deployment_target: str
    deployment_date: datetime
    enabled_mcps: List[str]
    initial_stats: dict
    created_at: datetime


def get_cradle_db_connection():
    """Get connection to Cradle installation DB"""
    import os
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="installation_configs",
        user="cradle",
        password=os.getenv("CRADLE_DB_PASSWORD", "cradle_secret_2025"),
        cursor_factory=RealDictCursor
    )


@router.get("/cradle/installations")
async def list_cradle_installations(
    page: int = 1,
    page_size: int = 20
):
    """
    List all Cradle customer installations.

    Returns installations from Cradle DB with pagination.
    """
    try:
        conn = get_cradle_db_connection()
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM installation_configs")
        total = cursor.fetchone()['count']

        # Get paginated results
        cursor.execute("""
            SELECT
                customer_id, company_name, deployment_target,
                deployment_date, enabled_mcps, initial_stats, created_at
            FROM installation_configs
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (page_size, (page - 1) * page_size))

        installations = []
        for row in cursor.fetchall():
            installations.append(CradleInstallation(
                customer_id=row['customer_id'],
                company_name=row['company_name'],
                deployment_target=row['deployment_target'],
                deployment_date=row['deployment_date'],
                enabled_mcps=row['enabled_mcps'] or [],
                initial_stats=row['initial_stats'] or {},
                created_at=row['created_at']
            ))

        cursor.close()
        conn.close()

        return {
            "installations": installations,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cradle DB error: {str(e)}")


@router.get("/cradle/installations/{customer_id}")
async def get_cradle_installation(customer_id: str):
    """Get specific Cradle installation details"""
    try:
        conn = get_cradle_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM installation_configs WHERE customer_id = %s",
            (customer_id,)
        )

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Installation not found")

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# NOTE: Customer deployment is handled by /api/orchestrator/initialize-customer
# This endpoint provides the complete workflow including GPU processing, user creation, etc.
# Admin UI should call that endpoint instead of duplicating logic here.


@router.get("/cradle/services")
async def get_cradle_services_status():
    """Get status of all Cradle services"""
    services = {}

    # Embeddings (port 8001)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:8001/health")
            services['embeddings'] = {
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "port": 8001,
                "details": resp.json() if resp.status_code == 200 else None
            }
    except Exception as e:
        services['embeddings'] = {"status": "unreachable", "port": 8001, "error": str(e)}

    # Vision (port 8002)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:8002/health")
            services['vision'] = {
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "port": 8002,
                "details": resp.json() if resp.status_code == 200 else None
            }
    except Exception as e:
        services['vision'] = {"status": "unreachable", "port": 8002, "error": str(e)}

    # Installation DB (port 5433)
    try:
        conn = get_cradle_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        services['installation_db'] = {"status": "healthy", "port": 5433}
    except Exception as e:
        services['installation_db'] = {"status": "unhealthy", "port": 5433, "error": str(e)}

    return {
        "services": services,
        "overall_status": "healthy" if all(s.get('status') == 'healthy' for s in services.values()) else "degraded"
    }


@router.get("/cradle/images/{customer_id}/download")
async def download_customer_image(customer_id: str, version: str = "1.0"):
    """Download customer Docker image archive"""
    from fastapi.responses import FileResponse

    archive_path = FilePath(f"/home/christoph.bertsch/0711/docker-images/customer/{customer_id}-v{version}.tar.gz")

    if not archive_path.exists():
        raise HTTPException(status_code=404, detail="Image archive not found")

    return FileResponse(
        path=str(archive_path),
        filename=f"{customer_id}-v{version}.tar.gz",
        media_type="application/gzip"
    )


# =============================================================================
# USER MANAGEMENT (Platform Admin - All Users)
# =============================================================================

@router.get("/users")
async def list_all_users(
    page: int = 1,
    page_size: int = 50,
    role: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List ALL users across all customers (Platform Admin only)

    Filters:
        role: Filter by role (platform_admin, partner_admin, customer_admin, customer_user)
        status: Filter by status (active, invited, suspended, inactive)
        customer_id: Filter by customer
        search: Search by name or email
    """
    query = db.query(User)

    # Apply filters
    if role:
        query = query.filter(User.role == role)

    if status:
        query = query.filter(User.status == status)

    if customer_id:
        query = query.filter(User.customer_id == customer_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )

    # Get total
    total = query.count()

    # Paginate
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # Format with customer info
    results = []
    for user in users:
        customer_name = None
        if user.customer_id:
            customer = db.query(Customer).filter(Customer.id == user.customer_id).first()
            if customer:
                customer_name = customer.company_name

        results.append({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "status": user.status.value if hasattr(user.status, 'value') else user.status,
            "customer_id": str(user.customer_id) if user.customer_id else None,
            "customer_name": customer_name,
            "partner_id": str(user.partner_id) if user.partner_id else None,
            "permissions": user.permissions,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {
        "users": results,
        "total": total,
        "page": page,
        "page_size": page_size
    }
