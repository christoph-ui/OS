"""
Booking Service
Expert booking flow with availability checking and payment processing
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, time
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models import (
    Booking,
    Expert,
    ExpertAvailability,
    ExpertBlockedTime,
    Engagement,
    Customer,
    User
)

logger = logging.getLogger(__name__)


class BookingService:
    """
    Expert booking operations
    
    Handles:
    - Availability checking
    - Booking request creation
    - Expert accept/decline flow
    - Engagement creation from bookings
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # AVAILABILITY
    # =========================================================================

    def get_expert_availability(self, expert_id: UUID) -> Dict[str, Any]:
        """Get expert's weekly availability schedule"""
        slots = self.db.query(ExpertAvailability).filter(
            ExpertAvailability.expert_id == expert_id,
            ExpertAvailability.is_active == True
        ).order_by(ExpertAvailability.day_of_week).all()

        schedule = {}
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for slot in slots:
            day = days[slot.day_of_week]
            if day not in schedule:
                schedule[day] = []
            schedule[day].append({
                "start": slot.start_time,
                "end": slot.end_time,
                "slot_duration": slot.slot_duration_minutes,
                "timezone": slot.timezone
            })

        return {
            "expert_id": str(expert_id),
            "schedule": schedule
        }

    def get_expert_blocked_times(
        self,
        expert_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get expert's blocked time periods"""
        blocked = self.db.query(ExpertBlockedTime).filter(
            ExpertBlockedTime.expert_id == expert_id,
            ExpertBlockedTime.start_datetime <= end_date,
            ExpertBlockedTime.end_datetime >= start_date
        ).all()

        return [
            {
                "start": b.start_datetime.isoformat(),
                "end": b.end_datetime.isoformat(),
                "reason": b.reason
            }
            for b in blocked
        ]

    def set_expert_availability(
        self,
        expert_id: UUID,
        schedule: Dict[str, List[Dict[str, str]]]
    ) -> bool:
        """
        Set expert's weekly availability
        
        schedule format:
        {
            "monday": [{"start": "09:00", "end": "17:00"}],
            "tuesday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "18:00"}]
        }
        """
        days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
                "friday": 4, "saturday": 5, "sunday": 6}

        # Clear existing availability
        self.db.query(ExpertAvailability).filter(
            ExpertAvailability.expert_id == expert_id
        ).delete()

        # Create new slots
        for day_name, slots in schedule.items():
            if day_name not in days:
                continue
            
            for slot in slots:
                availability = ExpertAvailability(
                    expert_id=expert_id,
                    day_of_week=days[day_name],
                    start_time=slot.get("start", "09:00"),
                    end_time=slot.get("end", "17:00"),
                    timezone=slot.get("timezone", "Europe/Berlin"),
                    slot_duration_minutes=slot.get("slot_duration", 60),
                    buffer_minutes=slot.get("buffer", 15),
                    is_active=True
                )
                self.db.add(availability)

        self.db.commit()
        return True

    def block_time(
        self,
        expert_id: UUID,
        start: datetime,
        end: datetime,
        reason: Optional[str] = None
    ) -> ExpertBlockedTime:
        """Block a specific time period"""
        blocked = ExpertBlockedTime(
            expert_id=expert_id,
            start_datetime=start,
            end_datetime=end,
            reason=reason
        )
        self.db.add(blocked)
        self.db.commit()
        self.db.refresh(blocked)
        return blocked

    # =========================================================================
    # BOOKING REQUESTS
    # =========================================================================

    def create_booking(
        self,
        customer_id: UUID,
        expert_id: UUID,
        title: str,
        description: str,
        connector_focus: Optional[List[str]] = None,
        project_type: str = "one_time",
        estimated_hours: Optional[int] = None,
        budget_min_cents: Optional[int] = None,
        budget_max_cents: Optional[int] = None,
        urgency: str = "normal",
        requested_start: Optional[datetime] = None,
        preferred_times: Optional[List[Dict]] = None,
        timezone: str = "Europe/Berlin",
        attachments: Optional[List[Dict]] = None,
        context_data: Optional[Dict] = None
    ) -> Booking:
        """
        Create a booking request
        
        This sends a request to the expert for review.
        """
        # Verify expert exists and is available
        expert = self.db.query(Expert).filter(Expert.id == expert_id).first()
        if not expert:
            raise ValueError("Expert not found")
        
        if not expert.available:
            raise ValueError("Expert is not accepting new bookings")

        # Calculate expiration (48 hours for normal, 24 for urgent)
        if urgency == "urgent" or urgency == "asap":
            expires_at = datetime.now(timezone) + timedelta(hours=24)
        else:
            expires_at = datetime.now(timezone) + timedelta(hours=48)

        booking = Booking(
            customer_id=customer_id,
            expert_id=expert_id,
            title=title,
            description=description,
            connector_focus=connector_focus,
            project_type=project_type,
            estimated_hours=estimated_hours,
            budget_min_cents=budget_min_cents,
            budget_max_cents=budget_max_cents,
            urgency=urgency,
            requested_start=requested_start,
            preferred_times=preferred_times,
            timezone=timezone,
            attachments=attachments,
            context_data=context_data,
            status="pending",
            expires_at=expires_at
        )
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Created booking {booking.id} for expert {expert_id}")
        
        # TODO: Send notification to expert
        
        return booking

    def get_booking(self, booking_id: UUID) -> Optional[Booking]:
        """Get a booking by ID"""
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_customer_bookings(
        self,
        customer_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get bookings for a customer"""
        query = self.db.query(Booking).filter(Booking.customer_id == customer_id)
        
        if status:
            query = query.filter(Booking.status == status)
        
        total = query.count()
        bookings = query.order_by(Booking.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "bookings": [self._booking_to_dict(b) for b in bookings],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_expert_bookings(
        self,
        expert_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get bookings for an expert"""
        query = self.db.query(Booking).filter(Booking.expert_id == expert_id)
        
        if status:
            query = query.filter(Booking.status == status)
        
        total = query.count()
        bookings = query.order_by(Booking.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "bookings": [self._booking_to_dict(b) for b in bookings],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    # =========================================================================
    # EXPERT RESPONSES
    # =========================================================================

    def mark_booking_viewed(self, booking_id: UUID, expert_id: UUID) -> bool:
        """Mark a booking as viewed by the expert"""
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.expert_id == expert_id
        ).first()
        
        if not booking:
            return False
        
        if not booking.viewed_at:
            booking.viewed_at = datetime.now(timezone.utc)
            self.db.commit()
        
        return True

    def accept_booking(
        self,
        booking_id: UUID,
        expert_id: UUID,
        message: Optional[str] = None,
        proposed_rate_cents: Optional[int] = None,
        proposed_hours: Optional[int] = None,
        proposed_start: Optional[datetime] = None
    ) -> Booking:
        """
        Expert accepts a booking request
        
        Can include a counter-proposal for rate/hours/start date.
        """
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.expert_id == expert_id
        ).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if not booking.can_respond:
            raise ValueError(f"Cannot respond to booking in status: {booking.status}")

        booking.status = "accepted"
        booking.expert_message = message
        booking.responded_at = datetime.now(timezone.utc)
        booking.accepted_at = datetime.now(timezone.utc)
        
        if proposed_rate_cents:
            booking.proposed_rate_cents = proposed_rate_cents
        if proposed_hours:
            booking.proposed_hours = proposed_hours
        if proposed_start:
            booking.proposed_start = proposed_start

        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Expert {expert_id} accepted booking {booking_id}")
        
        # TODO: Send notification to customer
        
        return booking

    def decline_booking(
        self,
        booking_id: UUID,
        expert_id: UUID,
        reason: Optional[str] = None
    ) -> Booking:
        """Expert declines a booking request"""
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.expert_id == expert_id
        ).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if not booking.can_respond:
            raise ValueError(f"Cannot respond to booking in status: {booking.status}")

        booking.status = "declined"
        booking.declined_reason = reason
        booking.responded_at = datetime.now(timezone.utc)
        booking.declined_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Expert {expert_id} declined booking {booking_id}")
        
        # TODO: Send notification to customer
        
        return booking

    def send_counter_proposal(
        self,
        booking_id: UUID,
        expert_id: UUID,
        message: str,
        proposed_rate_cents: int,
        proposed_hours: int,
        proposed_start: Optional[datetime] = None,
        additional_terms: Optional[Dict] = None
    ) -> Booking:
        """Expert sends a counter-proposal"""
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.expert_id == expert_id
        ).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if not booking.can_respond:
            raise ValueError(f"Cannot respond to booking in status: {booking.status}")

        booking.status = "negotiating"
        booking.expert_message = message
        booking.proposed_rate_cents = proposed_rate_cents
        booking.proposed_hours = proposed_hours
        booking.proposed_start = proposed_start
        booking.counter_proposal = {
            "rate_cents": proposed_rate_cents,
            "hours": proposed_hours,
            "start": proposed_start.isoformat() if proposed_start else None,
            "additional_terms": additional_terms,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        booking.responded_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Expert {expert_id} sent counter-proposal for booking {booking_id}")
        
        return booking

    # =========================================================================
    # CUSTOMER RESPONSES
    # =========================================================================

    def confirm_booking(self, booking_id: UUID, customer_id: UUID) -> Booking:
        """
        Customer confirms a booking (after expert acceptance or counter-proposal)
        
        This creates the actual Engagement.
        """
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.customer_id == customer_id
        ).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if booking.status not in ("accepted", "negotiating"):
            raise ValueError(f"Cannot confirm booking in status: {booking.status}")

        # Create engagement
        engagement = Engagement(
            customer_id=customer_id,
            expert_id=booking.expert_id,
            title=booking.title,
            description=booking.description,
            focus_area=booking.connector_focus[0] if booking.connector_focus else None,
            connectors_used=booking.connector_focus,
            estimated_hours=booking.proposed_hours or booking.estimated_hours,
            status="active",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(engagement)
        self.db.flush()  # Get engagement ID

        # Update booking
        booking.status = "confirmed"
        booking.engagement_id = engagement.id

        # Update expert stats
        expert = booking.expert
        if expert:
            expert.active_clients = (expert.active_clients or 0) + 1

        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Booking {booking_id} confirmed, engagement {engagement.id} created")
        
        return booking

    def cancel_booking(
        self,
        booking_id: UUID,
        user_id: UUID,
        is_customer: bool,
        reason: Optional[str] = None
    ) -> Booking:
        """Cancel a booking (by either party)"""
        if is_customer:
            booking = self.db.query(Booking).filter(
                Booking.id == booking_id
            ).join(Customer).filter(
                Customer.primary_admin_id == user_id
            ).first()
        else:
            booking = self.db.query(Booking).filter(
                Booking.id == booking_id
            ).join(Expert).filter(
                Expert.id == Booking.expert_id
            ).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if booking.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot cancel booking in status: {booking.status}")

        booking.status = "cancelled"
        # Store who cancelled and why
        if not booking.context_data:
            booking.context_data = {}
        booking.context_data["cancelled_by"] = "customer" if is_customer else "expert"
        booking.context_data["cancel_reason"] = reason
        booking.context_data["cancelled_at"] = datetime.now(timezone.utc).isoformat()

        self.db.commit()
        self.db.refresh(booking)

        logger.info(f"Booking {booking_id} cancelled by {'customer' if is_customer else 'expert'}")
        
        return booking

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _booking_to_dict(self, booking: Booking) -> Dict[str, Any]:
        """Convert booking to dictionary"""
        expert = booking.expert
        customer = booking.customer
        
        return {
            "id": str(booking.id),
            "title": booking.title,
            "description": booking.description,
            "connector_focus": booking.connector_focus,
            "project_type": booking.project_type,
            "estimated_hours": booking.estimated_hours,
            "budget_min_cents": booking.budget_min_cents,
            "budget_max_cents": booking.budget_max_cents,
            "urgency": booking.urgency,
            "status": booking.status,
            
            # Expert info
            "expert": {
                "id": str(expert.id),
                "name": expert.name,
                "title": expert.title,
                "avatar_url": expert.avatar_url,
                "hourly_rate_cents": expert.hourly_rate_cents,
                "rating": float(expert.rating) if expert.rating else 0
            } if expert else None,
            
            # Customer info
            "customer": {
                "id": str(customer.id),
                "company_name": customer.company_name
            } if customer else None,
            
            # Expert proposal
            "expert_message": booking.expert_message,
            "proposed_rate_cents": booking.proposed_rate_cents,
            "proposed_hours": booking.proposed_hours,
            "proposed_start": booking.proposed_start.isoformat() if booking.proposed_start else None,
            "counter_proposal": booking.counter_proposal,
            
            # Timestamps
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
            "viewed_at": booking.viewed_at.isoformat() if booking.viewed_at else None,
            "responded_at": booking.responded_at.isoformat() if booking.responded_at else None,
            "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
            
            # Result
            "engagement_id": str(booking.engagement_id) if booking.engagement_id else None
        }


def get_booking_service(db: Session) -> BookingService:
    """Factory function for dependency injection"""
    return BookingService(db)
