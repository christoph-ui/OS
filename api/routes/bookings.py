"""
Booking Routes
Expert booking flow with availability, requests, and responses
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import Customer, User, Expert
from ..services.booking_service import BookingService
from ..utils.security import get_current_user, get_current_customer

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


# ============================================================================
# SCHEMAS
# ============================================================================

class CreateBookingRequest(BaseModel):
    expert_id: UUID
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    connector_focus: Optional[List[str]] = None
    project_type: str = Field("one_time", regex="^(one_time|ongoing|consultation)$")
    estimated_hours: Optional[int] = Field(None, ge=1)
    budget_min_cents: Optional[int] = Field(None, ge=0)
    budget_max_cents: Optional[int] = Field(None, ge=0)
    urgency: str = Field("normal", regex="^(flexible|normal|urgent|asap)$")
    requested_start: Optional[datetime] = None
    preferred_times: Optional[List[dict]] = None
    timezone: str = "Europe/Berlin"
    attachments: Optional[List[dict]] = None
    context_data: Optional[dict] = None


class AcceptBookingRequest(BaseModel):
    message: Optional[str] = None
    proposed_rate_cents: Optional[int] = Field(None, ge=0)
    proposed_hours: Optional[int] = Field(None, ge=1)
    proposed_start: Optional[datetime] = None


class DeclineBookingRequest(BaseModel):
    reason: Optional[str] = None


class CounterProposalRequest(BaseModel):
    message: str
    proposed_rate_cents: int = Field(..., ge=0)
    proposed_hours: int = Field(..., ge=1)
    proposed_start: Optional[datetime] = None
    additional_terms: Optional[dict] = None


class CancelBookingRequest(BaseModel):
    reason: Optional[str] = None


class SetAvailabilityRequest(BaseModel):
    schedule: dict  # {"monday": [{"start": "09:00", "end": "17:00"}], ...}


class BlockTimeRequest(BaseModel):
    start: datetime
    end: datetime
    reason: Optional[str] = None


# ============================================================================
# CUSTOMER ROUTES
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a booking request for an expert
    
    This sends a request to the expert for review. The expert can:
    - Accept (optionally with a counter-proposal)
    - Decline
    - Send a counter-proposal
    
    Bookings expire after 48 hours (24 for urgent) if not responded to.
    """
    service = BookingService(db)
    
    try:
        booking = service.create_booking(
            customer_id=customer.id,
            expert_id=request.expert_id,
            title=request.title,
            description=request.description,
            connector_focus=request.connector_focus,
            project_type=request.project_type,
            estimated_hours=request.estimated_hours,
            budget_min_cents=request.budget_min_cents,
            budget_max_cents=request.budget_max_cents,
            urgency=request.urgency,
            requested_start=request.requested_start,
            preferred_times=request.preferred_times,
            timezone=request.timezone,
            attachments=request.attachments,
            context_data=request.context_data
        )
        
        return {
            "success": True,
            "message": "Booking request sent to expert",
            "booking_id": str(booking.id),
            "status": booking.status,
            "expires_at": booking.expires_at.isoformat() if booking.expires_at else None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my")
async def get_my_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get all booking requests made by the current customer"""
    service = BookingService(db)
    result = service.get_customer_bookings(
        customer_id=customer.id,
        status=status_filter,
        page=page,
        page_size=page_size
    )
    return {"success": True, **result}


@router.get("/{booking_id}")
async def get_booking(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get booking details"""
    service = BookingService(db)
    booking = service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check access (customer or expert)
    # TODO: Proper authorization check
    
    return {
        "success": True,
        "booking": service._booking_to_dict(booking)
    }


@router.post("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Confirm a booking after expert acceptance
    
    This creates the actual Engagement and work can begin.
    """
    service = BookingService(db)
    
    try:
        booking = service.confirm_booking(booking_id, customer.id)
        
        return {
            "success": True,
            "message": "Booking confirmed, engagement created",
            "booking_id": str(booking.id),
            "engagement_id": str(booking.engagement_id),
            "status": booking.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: UUID,
    request: CancelBookingRequest,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Cancel a booking request"""
    service = BookingService(db)
    
    try:
        booking = service.cancel_booking(
            booking_id=booking_id,
            user_id=user.id,
            is_customer=True,
            reason=request.reason
        )
        
        return {
            "success": True,
            "message": "Booking cancelled",
            "booking_id": str(booking.id),
            "status": booking.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# EXPERT ROUTES
# ============================================================================

expert_router = APIRouter(prefix="/api/expert/bookings", tags=["expert-bookings"])


@expert_router.get("/")
async def get_expert_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all booking requests for the current expert
    
    Requires expert authentication.
    """
    # Get expert from user
    # TODO: Proper expert-user linking
    expert = db.query(Expert).filter(Expert.email == user.email).first()
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an expert account"
        )
    
    service = BookingService(db)
    result = service.get_expert_bookings(
        expert_id=expert.id,
        status=status_filter,
        page=page,
        page_size=page_size
    )
    return {"success": True, **result}


@expert_router.post("/{booking_id}/view")
async def mark_booking_viewed(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a booking as viewed"""
    expert = db.query(Expert).filter(Expert.email == user.email).first()
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an expert account"
        )
    
    service = BookingService(db)
    success = service.mark_booking_viewed(booking_id, expert.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return {"success": True, "message": "Booking marked as viewed"}


@expert_router.post("/{booking_id}/accept")
async def accept_booking(
    booking_id: UUID,
    request: AcceptBookingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept a booking request
    
    Optionally include a counter-proposal for rate, hours, or start date.
    """
    expert = db.query(Expert).filter(Expert.email == user.email).first()
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an expert account"
        )
    
    service = BookingService(db)
    
    try:
        booking = service.accept_booking(
            booking_id=booking_id,
            expert_id=expert.id,
            message=request.message,
            proposed_rate_cents=request.proposed_rate_cents,
            proposed_hours=request.proposed_hours,
            proposed_start=request.proposed_start
        )
        
        return {
            "success": True,
            "message": "Booking accepted",
            "booking_id": str(booking.id),
            "status": booking.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@expert_router.post("/{booking_id}/decline")
async def decline_booking(
    booking_id: UUID,
    request: DeclineBookingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Decline a booking request"""
    expert = db.query(Expert).filter(Expert.email == user.email).first()
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an expert account"
        )
    
    service = BookingService(db)
    
    try:
        booking = service.decline_booking(
            booking_id=booking_id,
            expert_id=expert.id,
            reason=request.reason
        )
        
        return {
            "success": True,
            "message": "Booking declined",
            "booking_id": str(booking.id),
            "status": booking.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@expert_router.post("/{booking_id}/counter")
async def send_counter_proposal(
    booking_id: UUID,
    request: CounterProposalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a counter-proposal to the customer"""
    expert = db.query(Expert).filter(Expert.email == user.email).first()
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an expert account"
        )
    
    service = BookingService(db)
    
    try:
        booking = service.send_counter_proposal(
            booking_id=booking_id,
            expert_id=expert.id,
            message=request.message,
            proposed_rate_cents=request.proposed_rate_cents,
            proposed_hours=request.proposed_hours,
            proposed_start=request.proposed_start,
            additional_terms=request.additional_terms
        )
        
        return {
            "success": True,
            "message": "Counter-proposal sent",
            "booking_id": str(booking.id),
            "status": booking.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# AVAILABILITY ROUTES
# ============================================================================

availability_router = APIRouter(prefix="/api/experts", tags=["expert-availability"])


@availability_router.get("/{expert_id}/availability")
async def get_expert_availability(
    expert_id: UUID,
    db: Session = Depends(get_db)
):
    """Get an expert's availability schedule"""
    service = BookingService(db)
    availability = service.get_expert_availability(expert_id)
    
    return {
        "success": True,
        **availability
    }


@availability_router.get("/{expert_id}/blocked-times")
async def get_expert_blocked_times(
    expert_id: UUID,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db)
):
    """Get an expert's blocked time periods"""
    service = BookingService(db)
    blocked = service.get_expert_blocked_times(expert_id, start, end)
    
    return {
        "success": True,
        "blocked_times": blocked
    }


@availability_router.put("/{expert_id}/availability")
async def set_expert_availability(
    expert_id: UUID,
    request: SetAvailabilityRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set an expert's weekly availability schedule
    
    Requires expert authentication.
    """
    # Verify the user is this expert
    expert = db.query(Expert).filter(
        Expert.id == expert_id,
        Expert.email == user.email
    ).first()
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this expert's availability"
        )
    
    service = BookingService(db)
    success = service.set_expert_availability(expert_id, request.schedule)
    
    return {
        "success": success,
        "message": "Availability updated"
    }


@availability_router.post("/{expert_id}/blocked-times")
async def block_expert_time(
    expert_id: UUID,
    request: BlockTimeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Block a specific time period
    
    Requires expert authentication.
    """
    expert = db.query(Expert).filter(
        Expert.id == expert_id,
        Expert.email == user.email
    ).first()
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this expert's availability"
        )
    
    service = BookingService(db)
    blocked = service.block_time(
        expert_id=expert_id,
        start=request.start,
        end=request.end,
        reason=request.reason
    )
    
    return {
        "success": True,
        "message": "Time blocked",
        "blocked_time_id": str(blocked.id)
    }
