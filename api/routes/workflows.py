"""
Workflow Routes
Browse marketplace, subscribe to workflows, execute workflows
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import uuid as uuid_lib

from ..database import get_db
from ..models.workflow import Workflow
from ..models.workflow_definition import WorkflowDefinition
from ..models.workflow_subscription import WorkflowSubscription
from ..models.workflow_execution import WorkflowExecution
from ..models.workflow_step_log import WorkflowStepLog
from ..models.customer import Customer
from ..models.user import User
from ..schemas.workflow import (
    WorkflowResponse,
    WorkflowDetailResponse,
    WorkflowListResponse,
    WorkflowSubscribeRequest,
    WorkflowSubscriptionResponse,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionDetailResponse,
    WorkflowStepLogResponse
)
from ..utils.security import get_current_user, get_current_customer
from orchestrator.langgraph.workflow_engine import WorkflowEngine

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ============================================================================
# WORKFLOW MARKETPLACE
# ============================================================================

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    featured_only: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all workflows in marketplace

    Supports filtering by category, featured status, search
    """
    query = db.query(Workflow).filter(
        Workflow.status == "active",
        Workflow.published == True,
        Workflow.approval_status == "approved"
    )

    # Apply filters
    if category:
        query = query.filter(Workflow.category == category)

    if featured_only:
        query = query.filter(Workflow.featured == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Workflow.name.ilike(search_term),
                Workflow.display_name.ilike(search_term),
                Workflow.description.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Paginate
    workflows = query.order_by(
        Workflow.featured.desc(),
        Workflow.install_count.desc(),
        Workflow.rating.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return WorkflowListResponse(
        workflows=[WorkflowResponse.from_orm(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed workflow information"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Get active definition
    definition = db.query(WorkflowDefinition).filter(
        WorkflowDefinition.workflow_id == workflow_id,
        WorkflowDefinition.is_active == True
    ).first()

    response = WorkflowDetailResponse.from_orm(workflow)
    if definition:
        response.step_count = definition.step_count

    return response


# ============================================================================
# WORKFLOW SUBSCRIPTIONS
# ============================================================================

@router.post("/subscribe", response_model=WorkflowSubscriptionResponse)
async def subscribe_to_workflow(
    request: WorkflowSubscribeRequest,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Subscribe to a workflow

    Enables customer to use the workflow
    """
    # Get workflow
    workflow = db.query(Workflow).filter(Workflow.id == request.workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    if not workflow.can_execute:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not available for subscription"
        )

    # Check if already subscribed
    existing = db.query(WorkflowSubscription).filter(
        and_(
            WorkflowSubscription.customer_id == customer.id,
            WorkflowSubscription.workflow_id == request.workflow_id,
            WorkflowSubscription.status == "active"
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already subscribed to this workflow"
        )

    # Create subscription
    subscription = WorkflowSubscription(
        customer_id=customer.id,
        workflow_id=workflow.id,
        enabled=True,
        status="active",
        config=request.config or {},
        schedule_enabled=request.schedule_enabled or False,
        schedule_cron=request.schedule_cron
    )

    db.add(subscription)

    # Update workflow stats
    workflow.install_count += 1
    workflow.active_subscriptions += 1

    db.commit()
    db.refresh(subscription)

    logger.info(f"Customer {customer.id} subscribed to workflow {workflow.name}")

    return WorkflowSubscriptionResponse.from_orm(subscription)


@router.get("/subscriptions", response_model=List[WorkflowSubscriptionResponse])
async def list_my_subscriptions(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """List customer's workflow subscriptions"""
    subscriptions = db.query(WorkflowSubscription).filter(
        WorkflowSubscription.customer_id == customer.id,
        WorkflowSubscription.status == "active"
    ).all()

    return [WorkflowSubscriptionResponse.from_orm(s) for s in subscriptions]


@router.delete("/subscriptions/{subscription_id}")
async def unsubscribe_from_workflow(
    subscription_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Unsubscribe from a workflow"""
    subscription = db.query(WorkflowSubscription).filter(
        WorkflowSubscription.id == subscription_id,
        WorkflowSubscription.customer_id == customer.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Cancel subscription
    subscription.status = "canceled"
    subscription.unsubscribed_at = datetime.utcnow()

    # Update workflow stats
    workflow = db.query(Workflow).filter(Workflow.id == subscription.workflow_id).first()
    if workflow and workflow.active_subscriptions > 0:
        workflow.active_subscriptions -= 1

    db.commit()

    return {"message": "Workflow unsubscribed"}


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Execute a workflow

    Runs workflow in background and returns execution ID for tracking
    """
    # Check subscription
    subscription = db.query(WorkflowSubscription).filter(
        and_(
            WorkflowSubscription.customer_id == customer.id,
            WorkflowSubscription.workflow_id == request.workflow_id,
            WorkflowSubscription.status == "active"
        )
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not subscribed to this workflow. Subscribe first."
        )

    # Get workflow definition
    workflow = db.query(Workflow).filter(Workflow.id == request.workflow_id).first()
    definition = db.query(WorkflowDefinition).filter(
        WorkflowDefinition.workflow_id == request.workflow_id,
        WorkflowDefinition.is_active == True
    ).first()

    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found"
        )

    # Create execution record
    execution = WorkflowExecution(
        id=uuid_lib.uuid4(),
        customer_id=customer.id,
        workflow_id=workflow.id,
        subscription_id=subscription.id,
        triggered_by_user_id=user.id,
        status="pending",
        input_data=request.input_data,
        state_snapshot={},
        trigger_type="manual",
        trigger_metadata=request.config or {}
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Execute workflow in background
    background_tasks.add_task(
        run_workflow_async,
        execution_id=str(execution.id),
        workflow_definition=definition.definition,
        customer_id=str(customer.id),
        workflow_id=str(workflow.id),
        input_data=request.input_data,
        config=request.config
    )

    logger.info(f"Started workflow execution {execution.id} for customer {customer.id}")

    return WorkflowExecutionResponse.from_orm(execution)


async def run_workflow_async(
    execution_id: str,
    workflow_definition: dict,
    customer_id: str,
    workflow_id: str,
    input_data: dict,
    config: dict = None
):
    """
    Background task to run workflow

    Updates execution record with results
    """
    db = SessionLocal()

    try:
        # Get execution
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()

        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        # Update status to running
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db.commit()

        # Execute workflow
        engine = WorkflowEngine(db_session=db)
        result = await engine.execute_workflow(
            workflow_definition=workflow_definition,
            customer_id=customer_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            input_data=input_data,
            config=config
        )

        # Update execution with results
        execution.status = result["status"]
        execution.output_data = result["output"]
        execution.steps_completed = result["step_count"]
        execution.steps_failed = len(result.get("errors", []))
        execution.completed_at = datetime.utcnow()
        execution.execution_time_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

        if result.get("errors"):
            execution.error_message = "; ".join(result["errors"])

        # Update subscription stats
        subscription = db.query(WorkflowSubscription).filter(
            WorkflowSubscription.id == execution.subscription_id
        ).first()

        if subscription:
            subscription.total_executions += 1
            if result["status"] == "completed":
                subscription.successful_executions += 1
            else:
                subscription.failed_executions += 1
            subscription.last_execution_at = datetime.utcnow()

        # Update workflow stats
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow:
            workflow.total_executions += 1

        db.commit()

        logger.info(f"Workflow execution {execution_id} completed: {result['status']}")

    except Exception as e:
        logger.error(f"Workflow execution {execution_id} failed: {e}", exc_info=True)

        if execution:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()

    finally:
        db.close()


@router.get("/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """List workflow executions for customer"""
    query = db.query(WorkflowExecution).filter(
        WorkflowExecution.customer_id == customer.id
    )

    if workflow_id:
        query = query.filter(WorkflowExecution.workflow_id == workflow_id)

    if status:
        query = query.filter(WorkflowExecution.status == status)

    executions = query.order_by(
        WorkflowExecution.created_at.desc()
    ).limit(limit).all()

    return [WorkflowExecutionResponse.from_orm(e) for e in executions]


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionDetailResponse)
async def get_execution(
    execution_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get detailed execution information with step logs"""
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id,
        WorkflowExecution.customer_id == customer.id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    # Get step logs
    step_logs = db.query(WorkflowStepLog).filter(
        WorkflowStepLog.execution_id == execution_id
    ).order_by(WorkflowStepLog.step_index).all()

    response = WorkflowExecutionDetailResponse.from_orm(execution)
    response.step_logs = [WorkflowStepLogResponse.from_orm(log).dict() for log in step_logs]

    return response


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Cancel a running workflow execution

    Only works for pending/running executions
    """
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id,
        WorkflowExecution.customer_id == customer.id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    if execution.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution with status: {execution.status}"
        )

    # Cancel execution
    execution.status = "canceled"
    execution.completed_at = datetime.utcnow()
    execution.error_message = "Canceled by user"

    db.commit()

    return {"message": "Workflow execution canceled"}


# Import SessionLocal for background task
from ..database import SessionLocal
