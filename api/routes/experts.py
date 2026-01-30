"""
Expert marketplace routes
Browse, create, and manage expert profiles
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.expert import Expert
from ..schemas.expert import (
    ExpertCreate,
    ExpertUpdate,
    ExpertResponse,
    ExpertDetailResponse,
    ExpertListResponse
)
from ..utils.security import get_current_customer_id, require_admin

router = APIRouter()


@router.get("/", response_model=ExpertListResponse)
async def list_experts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    specialization: Optional[str] = None,
    mcp: Optional[str] = None,
    available_only: bool = False,
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    List all experts in marketplace

    Supports filtering by specialization, MCP expertise, availability, rating
    """
    query = db.query(Expert).filter(
        Expert.status == "active",
        Expert.verified == True
    )

    # Apply filters
    if specialization:
        query = query.filter(Expert.specializations.contains([specialization]))

    if mcp:
        query = query.filter(Expert.mcp_expertise.contains([mcp]))

    if available_only:
        query = query.filter(Expert.available == True)

    if min_rating:
        query = query.filter(Expert.rating >= min_rating)

    # Get total count
    total = query.count()

    # Paginate
    experts = query.order_by(
        Expert.rating.desc(),
        Expert.active_clients.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return ExpertListResponse(
        experts=[ExpertResponse.from_orm(e) for e in experts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{expert_id}", response_model=ExpertDetailResponse)
async def get_expert(
    expert_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed expert profile"""
    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert not found"
        )

    return ExpertDetailResponse.from_orm(expert)


@router.post("/", response_model=ExpertResponse, status_code=status.HTTP_201_CREATED)
async def create_expert(
    expert_data: ExpertCreate,
    db: Session = Depends(get_db)
):
    """
    Create new expert profile

    Public endpoint for expert applications
    """
    # Check if email already exists
    existing = db.query(Expert).filter(Expert.email == expert_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create expert
    expert = Expert(
        name=expert_data.name,
        email=expert_data.email,
        title=expert_data.title,
        bio=expert_data.bio,
        avatar_initials=expert_data.avatar_initials or expert_data.name[:2].upper(),
        specializations=expert_data.specializations,
        mcp_expertise=expert_data.mcp_expertise,
        years_experience=expert_data.years_experience,
        hourly_rate_cents=expert_data.hourly_rate_cents,
        certifications=expert_data.certifications,
        education=expert_data.education,
        status="pending",  # Requires admin approval
        verified=False
    )

    db.add(expert)
    db.commit()
    db.refresh(expert)

    return ExpertResponse.from_orm(expert)


@router.patch("/{expert_id}", response_model=ExpertResponse)
async def update_expert(
    expert_id: UUID,
    expert_data: ExpertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update expert profile

    TODO: Add authentication - only expert can update their own profile
    """
    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert not found"
        )

    # Update fields
    update_data = expert_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expert, field, value)

    db.commit()
    db.refresh(expert)

    return ExpertResponse.from_orm(expert)


@router.post("/{expert_id}/approve", dependencies=[Depends(require_admin)])
async def approve_expert(
    expert_id: UUID,
    db: Session = Depends(get_db)
):
    """Admin: Approve expert application"""
    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert not found"
        )

    expert.status = "active"
    expert.verified = True

    db.commit()

    # TODO: Send approval email to expert

    return {"message": "Expert approved", "expert_id": str(expert_id)}


@router.get("/search", response_model=ExpertListResponse)
async def search_experts(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search experts by name, title, or bio"""
    search_term = f"%{q}%"

    query = db.query(Expert).filter(
        and_(
            Expert.status == "active",
            Expert.verified == True,
            or_(
                Expert.name.ilike(search_term),
                Expert.title.ilike(search_term),
                Expert.bio.ilike(search_term)
            )
        )
    )

    total = query.count()

    experts = query.order_by(Expert.rating.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ExpertListResponse(
        experts=[ExpertResponse.from_orm(e) for e in experts],
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================================
# NEW ENDPOINTS - Expert Network Enhancement
# ============================================================================

@router.post("/marketplace/search-advanced")
async def marketplace_search_advanced(
    mcps: List[str] = Query([]),
    industry: Optional[str] = None,
    price_min: int = Query(2000),
    price_max: int = Query(6000),
    availability: str = Query("any"),
    languages: List[str] = Query(["German"]),
    sort_by: str = Query("match"),
    db: Session = Depends(get_db)
):
    """
    Advanced marketplace search with AI-powered matching

    Returns experts with match scores based on company needs
    """
    # Get all approved experts
    query = db.query(Expert).filter(
        Expert.status == "active",
        Expert.verified == True
    )

    # Filter by availability
    if availability == "available":
        query = query.filter(Expert.available == True)

    experts_list = query.all()

    # Calculate match scores
    expert_results = []
    for expert in experts_list:
        score = 0
        reasons = []

        # MCP overlap (40% weight)
        if mcps:
            expert_mcps = expert.mcp_expertise or []
            mcp_matches = set(mcps) & set(expert_mcps)
            mcp_rate = len(mcp_matches) / len(mcps) if mcps else 0
            score += mcp_rate * 40
            if mcp_rate >= 0.67:
                reasons.append(f"Strong {', '.join(list(mcp_matches)[:2])} expertise")

        # Industry match (20% weight)
        if industry and industry != "any":
            if industry in (expert.specializations or []):
                score += 20
                reasons.append(f"{industry} experience")

        # Price alignment (15% weight)
        avg_rate = expert.hourly_rate_cents / 100 if expert.hourly_rate_cents else 0
        if price_min <= avg_rate <= price_max:
            score += 15
            reasons.append("Within budget")

        # Availability (10% weight)
        if expert.available:
            score += 10
            reasons.append("Available now")

        # Response time (10% weight) - assuming we track this
        score += 10  # TODO: Add actual response time tracking

        # Rating (5% weight)
        if expert.rating and expert.rating >= 4.5:
            score += 5

        expert_results.append({
            "id": str(expert.id),
            "name": expert.name,
            "title": expert.title,
            "avatar_initials": expert.avatar_initials,
            "rating": float(expert.rating or 0),
            "total_reviews": expert.active_clients or 0,
            "mcps": expert.mcp_expertise or [],
            "rate_min": (expert.hourly_rate_cents or 0) / 100,
            "rate_max": (expert.hourly_rate_cents or 0) / 100 * 1.2,
            "slots_available": 5,  # TODO: Calculate from max_clients - current_clients
            "match_score": min(round(score), 100),
            "match_reasons": reasons[:3]
        })

    # Sort by selected criteria
    if sort_by == "match":
        expert_results.sort(key=lambda x: x["match_score"], reverse=True)
    elif sort_by == "rating":
        expert_results.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "experience":
        expert_results.sort(key=lambda x: x.get("years_experience", 0), reverse=True)

    return {
        "success": True,
        "total": len(expert_results),
        "experts": expert_results
    }


@router.post("/applications/submit")
async def submit_expert_application(
    application_data: dict,
    db: Session = Depends(get_db)
):
    """
    Submit new expert application

    Application will be reviewed by admin team within 2-5 business days
    """
    # Check for existing application with same email
    email = application_data.get("email")
    existing = db.query(Expert).filter(Expert.email == email).first()

    if existing:
        if existing.status == "pending":
            return {
                "success": False,
                "message": "Application already submitted and under review",
                "application_id": str(existing.id)
            }
        elif existing.status == "active":
            return {
                "success": False,
                "message": "Expert profile already exists and is active"
            }

    # Create expert with pending status
    hourly_rate = application_data.get("hourly_rate_expectation", 150)

    expert = Expert(
        name=f"{application_data.get('first_name')} {application_data.get('last_name')}",
        email=email,
        title=application_data.get("headline"),
        bio=application_data.get("previous_clients"),
        avatar_initials=f"{application_data.get('first_name')[0]}{application_data.get('last_name')[0]}".upper(),
        specializations=application_data.get("industries", []),
        mcp_expertise=[m["mcpId"] for m in application_data.get("selected_mcps", [])],
        years_experience=application_data.get("years_experience", 0),
        certifications=application_data.get("certifications", []),
        hourly_rate_cents=hourly_rate * 100,  # Convert to cents
        status="pending",
        verified=False,
        available=False
    )

    db.add(expert)
    db.commit()
    db.refresh(expert)

    # TODO: Send confirmation email
    # TODO: Notify admin team

    return {
        "success": True,
        "application_id": str(expert.id),
        "message": "Application submitted successfully. We'll review it within 2-5 business days.",
        "status": "pending"
    }
