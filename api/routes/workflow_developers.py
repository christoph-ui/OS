"""
Workflow Developer Routes
Third-party developers can create and submit workflows to the marketplace
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
import uuid as uuid_lib

from ..database import get_db
from ..models.workflow import Workflow
from ..models.workflow_definition import WorkflowDefinition
from ..models.mcp_developer import MCPDeveloper
from ..models.user import User
from ..schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowDetailResponse, WorkflowUpdate
from ..utils.security import get_current_user

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workflow-developers", tags=["workflow-developers"])


@router.post("/workflows", response_model=dict)
async def submit_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a workflow for marketplace approval

    Requires verified MCP developer account
    """
    # Get developer account
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.user_id == current_user.id
    ).first()

    if not developer:
        developer = db.query(MCPDeveloper).filter(
            MCPDeveloper.email == current_user.email
        ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer account found. Register at /api/mcp-developers/register"
        )

    # Check if developer is verified
    if not developer.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer account must be verified before submitting workflows"
        )

    # Check if workflow name already exists
    existing = db.query(Workflow).filter(Workflow.name == workflow_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow with this name already exists"
        )

    # Create workflow in pending status
    workflow = Workflow(
        id=uuid_lib.uuid4(),
        developer_id=developer.id,
        name=workflow_data.name,
        display_name=workflow_data.display_name,
        version="1.0.0",
        description=workflow_data.description,
        category=workflow_data.category,
        subcategory=workflow_data.subcategory,
        tags=workflow_data.tags,
        icon=workflow_data.icon,
        icon_color=workflow_data.icon_color,
        pricing_model=workflow_data.pricing_model,
        price_per_month_cents=workflow_data.price_per_month_cents,
        price_per_execution_cents=workflow_data.price_per_execution_cents,
        approval_status="pending",
        submitted_at=datetime.utcnow(),
        status="active",
        published=False  # Not published until approved
    )

    db.add(workflow)
    db.flush()  # Get workflow.id

    # Create workflow definition
    definition_dict = {
        "nodes": [
            {
                "id": node.id,
                "mcp": node.mcp,
                "action": node.action,
                "config": node.config or {}
            }
            for node in workflow_data.definition.nodes
        ],
        "edges": [
            {
                "from": edge.from_node,
                "to": edge.to_node,
                **({"condition": edge.condition} if edge.condition else {})
            }
            for edge in workflow_data.definition.edges
        ],
        "entry_point": workflow_data.definition.entry_point
    }

    definition = WorkflowDefinition(
        workflow_id=workflow.id,
        version="1.0.0",
        is_active=True,
        definition=definition_dict,
        changelog="Initial submission",
        breaking_changes=False,
        created_by_id=current_user.id
    )

    # Validate definition
    is_valid, errors = definition.validate_definition()
    if not is_valid:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {'; '.join(errors)}"
        )

    definition.validated = True
    db.add(definition)

    # Extract required MCPs from definition
    required_mcps = list(set(node.mcp for node in workflow_data.definition.nodes))
    workflow.required_mcps = required_mcps

    # Update developer stats
    developer.total_mcps += 1  # Count workflows too

    db.commit()
    db.refresh(workflow)

    logger.info(f"Developer {developer.id} submitted workflow {workflow.name}")

    return {
        "success": True,
        "message": "Workflow submitted for approval",
        "workflow_id": str(workflow.id),
        "status": "pending"
    }


@router.get("/workflows/my", response_model=List[dict])
async def list_my_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List workflows submitted by current developer

    Returns all workflows (pending, approved, rejected)
    """
    # Get developer account
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.user_id == current_user.id
    ).first()

    if not developer:
        developer = db.query(MCPDeveloper).filter(
            MCPDeveloper.email == current_user.email
        ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer account found"
        )

    # Get all workflows by this developer
    workflows = db.query(Workflow).filter(Workflow.developer_id == developer.id).all()

    return [
        {
            "id": str(wf.id),
            "name": wf.name,
            "display_name": wf.display_name,
            "version": wf.version,
            "category": wf.category,
            "approval_status": wf.approval_status,
            "submitted_at": wf.submitted_at.isoformat() if wf.submitted_at else None,
            "approved_at": wf.approved_at.isoformat() if wf.approved_at else None,
            "active_subscriptions": wf.active_subscriptions,
            "total_executions": wf.total_executions,
            "rating": float(wf.rating) if wf.rating else 0.0,
            "rejection_reason": wf.rejection_reason
        }
        for wf in workflows
    ]


@router.patch("/workflows/{workflow_id}", response_model=dict)
async def update_workflow(
    workflow_id: UUID,
    updates: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update workflow metadata

    Can only update workflows you own
    """
    # Get developer
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.user_id == current_user.id
    ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer account found"
        )

    # Get workflow
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.developer_id == developer.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or you don't have permission to edit it"
        )

    # Apply updates
    if updates.display_name:
        workflow.display_name = updates.display_name

    if updates.description:
        workflow.description = updates.description

    if updates.tags is not None:
        workflow.tags = updates.tags

    if updates.icon:
        workflow.icon = updates.icon

    if updates.icon_color:
        workflow.icon_color = updates.icon_color

    if updates.pricing_model:
        workflow.pricing_model = updates.pricing_model

    if updates.price_per_month_cents is not None:
        workflow.price_per_month_cents = updates.price_per_month_cents

    workflow.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Workflow updated",
        "workflow_id": str(workflow.id)
    }
