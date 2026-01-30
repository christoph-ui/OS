"""
Engagement routes
Customer-expert engagement management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.engagement import Engagement
from ..models.expert import Expert
from ..schemas.engagement import (
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    EngagementDetailResponse,
    EngagementListResponse
)
from ..utils.security import get_current_customer_id

router = APIRouter()


@router.get("/", response_model=EngagementListResponse)
async def list_engagements(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """List all engagements for customer"""
    engagements = db.query(Engagement).filter(
        Engagement.customer_id == customer_id
    ).order_by(Engagement.created_at.desc()).all()

    return EngagementListResponse(
        engagements=[EngagementResponse.from_orm(e) for e in engagements],
        total=len(engagements)
    )


@router.get("/{engagement_id}", response_model=EngagementDetailResponse)
async def get_engagement(
    engagement_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get engagement details"""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.customer_id == customer_id
    ).first()

    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )

    # Get expert info
    expert = db.query(Expert).filter(Expert.id == engagement.expert_id).first()

    response = EngagementDetailResponse.from_orm(engagement)
    if expert:
        response.expert_name = expert.name
        response.expert_title = expert.title
        response.expert_avatar_initials = expert.avatar_initials

    return response


@router.post("/", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED)
async def create_engagement(
    engagement_data: EngagementCreate,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Create new engagement with expert

    Books an expert for the customer
    """
    # Verify expert exists and is available
    expert = db.query(Expert).filter(
        Expert.id == engagement_data.expert_id,
        Expert.status == "active",
        Expert.available == True
    ).first()

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert not found or unavailable"
        )

    # Check if expert is at capacity
    if expert.active_clients >= expert.max_concurrent_clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expert is at capacity"
        )

    # Create engagement
    engagement = Engagement(
        customer_id=customer_id,
        expert_id=expert.id,
        title=engagement_data.title,
        description=engagement_data.description,
        focus_area=engagement_data.focus_area,
        mcps_used=engagement_data.mcps_used,
        deliverables=engagement_data.deliverables,
        estimated_hours=engagement_data.estimated_hours,
        status="active",
        started_at=datetime.utcnow()
    )

    db.add(engagement)

    # Update expert stats
    expert.active_clients += 1

    db.commit()
    db.refresh(engagement)

    # TODO: Send engagement confirmation emails

    return EngagementResponse.from_orm(engagement)


@router.patch("/{engagement_id}", response_model=EngagementResponse)
async def update_engagement(
    engagement_id: UUID,
    engagement_data: EngagementUpdate,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Update engagement"""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.customer_id == customer_id
    ).first()

    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )

    # Update fields
    update_data = engagement_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(engagement, field, value)

    db.commit()
    db.refresh(engagement)

    return EngagementResponse.from_orm(engagement)


@router.post("/{engagement_id}/complete")
async def complete_engagement(
    engagement_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Mark engagement as completed"""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.customer_id == customer_id
    ).first()

    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found"
        )

    engagement.status = "completed"
    engagement.completed_at = datetime.utcnow()

    # Update expert stats
    expert = db.query(Expert).filter(Expert.id == engagement.expert_id).first()
    if expert and expert.active_clients > 0:
        expert.active_clients -= 1
        expert.completed_tasks += engagement.tasks_completed

    db.commit()

    return {"message": "Engagement completed"}
