"""
Task management routes
Individual tasks within engagements
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.task import Task
from ..models.engagement import Engagement
from ..schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskRatingRequest
)
from ..utils.security import get_current_customer_id

router = APIRouter()


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    engagement_id: Optional[UUID] = None,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """List tasks for customer"""
    query = db.query(Task).filter(Task.customer_id == customer_id)

    if engagement_id:
        query = query.filter(Task.engagement_id == engagement_id)

    tasks = query.order_by(Task.created_at.desc()).all()

    return TaskListResponse(
        tasks=[TaskResponse.from_orm(t) for t in tasks],
        total=len(tasks)
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get task details"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.customer_id == customer_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return TaskDetailResponse.from_orm(task)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Create new task in engagement"""
    # Verify engagement belongs to customer
    engagement = db.query(Engagement).filter(
        Engagement.id == task_data.engagement_id,
        Engagement.customer_id == customer_id,
        Engagement.status == "active"
    ).first()

    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found or not active"
        )

    # Create task
    task = Task(
        engagement_id=engagement.id,
        expert_id=engagement.expert_id,
        customer_id=customer_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        estimated_hours=task_data.estimated_hours,
        due_date=task_data.due_date,
        status="pending"
    )

    db.add(task)

    # Update engagement task count
    engagement.tasks_total += 1

    db.commit()
    db.refresh(task)

    return TaskResponse.from_orm(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Update task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.customer_id == customer_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update fields
    update_data = task_data.dict(exclude_unset=True)

    # Handle status change to completed
    if update_data.get("status") == "completed" and task.status != "completed":
        update_data["completed_at"] = datetime.utcnow()

        # Update engagement stats
        engagement = db.query(Engagement).filter(
            Engagement.id == task.engagement_id
        ).first()
        if engagement:
            engagement.tasks_completed += 1
            engagement.hours_logged += task.actual_hours or 0

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return TaskResponse.from_orm(task)


@router.post("/{task_id}/rate")
async def rate_task(
    task_id: UUID,
    rating_data: TaskRatingRequest,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Rate a completed task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.customer_id == customer_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate completed tasks"
        )

    # Update task rating
    task.customer_rating = rating_data.rating
    task.customer_feedback = rating_data.feedback

    # Update expert rating
    from ..models.expert import Expert
    expert = db.query(Expert).filter(Expert.id == task.expert_id).first()

    if expert:
        # Recalculate expert rating (simple average for now)
        rated_tasks = db.query(Task).filter(
            Task.expert_id == expert.id,
            Task.customer_rating.isnot(None)
        ).all()

        if rated_tasks:
            avg_rating = sum(t.customer_rating for t in rated_tasks) / len(rated_tasks)
            expert.rating = round(avg_rating, 2)
            expert.review_count = len(rated_tasks)

    db.commit()

    return {"message": "Task rated successfully"}
