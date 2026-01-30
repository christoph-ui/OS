"""
MCP Developer Routes
Handles third-party MCP developer registration and management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, HttpUrl

from ..database import get_db
from ..models.mcp_developer import MCPDeveloper
from ..models.mcp import MCP
from ..models.user import User
from ..utils.security import get_current_user, require_role

router = APIRouter(prefix="/api/mcp-developers", tags=["mcp-developers"])


# ============================================================================
# SCHEMAS
# ============================================================================

class MCPDeveloperRegister(BaseModel):
    """Developer registration request"""
    company_name: str
    developer_name: str
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = None
    bio: Optional[str] = None
    expertise_areas: Optional[List[str]] = []


class MCPDeveloperResponse(BaseModel):
    """Developer response"""
    id: UUID
    company_name: str
    developer_name: str
    email: str
    verified: bool
    status: str
    total_mcps: int
    published_mcps: int
    total_installations: int
    avg_rating: float
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class MCPDeveloperDetailResponse(MCPDeveloperResponse):
    """Detailed developer response"""
    phone: Optional[str]
    website: Optional[str]
    github_url: Optional[str]
    linkedin_url: Optional[str]
    twitter_handle: Optional[str]
    bio: Optional[str]
    expertise_areas: Optional[List[str]]
    stripe_onboarding_complete: bool
    revenue_share_percentage: int

    class Config:
        orm_mode = True
        from_attributes = True


class MCPSubmit(BaseModel):
    """Submit MCP for approval"""
    name: str
    display_name: str
    version: str
    description: str
    category: str
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = []
    capabilities: Optional[dict] = {}
    supported_languages: Optional[List[str]] = ["en"]
    max_context_length: Optional[int] = 4096
    icon: Optional[str] = "🤖"
    icon_color: Optional[str] = "blue"
    pricing_model: str = "free"
    price_per_month_cents: Optional[int] = None
    min_gpu_memory_gb: Optional[int] = None
    gpu_required: bool = False


# ============================================================================
# DEVELOPER REGISTRATION & PROFILE
# ============================================================================

@router.post("/register", response_model=MCPDeveloperResponse)
async def register_developer(
    registration: MCPDeveloperRegister,
    db: Session = Depends(get_db)
):
    """
    Self-service MCP developer registration

    Creates a developer account in pending status
    """
    # Check if email already exists
    existing = db.query(MCPDeveloper).filter(
        MCPDeveloper.email == registration.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Developer account with this email already exists"
        )

    # Create developer account
    developer = MCPDeveloper(
        company_name=registration.company_name,
        developer_name=registration.developer_name,
        email=registration.email,
        phone=registration.phone,
        website=str(registration.website) if registration.website else None,
        github_url=str(registration.github_url) if registration.github_url else None,
        linkedin_url=str(registration.linkedin_url) if registration.linkedin_url else None,
        twitter_handle=registration.twitter_handle,
        bio=registration.bio,
        expertise_areas=registration.expertise_areas,
        verified=False,
        status="pending",  # Pending admin approval
        total_mcps=0,
        published_mcps=0,
        total_installations=0,
        avg_rating=0.0
    )

    db.add(developer)
    db.commit()
    db.refresh(developer)

    return MCPDeveloperResponse.from_orm(developer)


@router.get("/me", response_model=MCPDeveloperDetailResponse)
async def get_my_developer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's developer profile

    Returns developer account if one exists
    """
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.user_id == current_user.id
    ).first()

    if not developer:
        # Try by email
        developer = db.query(MCPDeveloper).filter(
            MCPDeveloper.email == current_user.email
        ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer account found. Register at /api/mcp-developers/register"
        )

    return MCPDeveloperDetailResponse.from_orm(developer)


@router.get("/{developer_id}", response_model=MCPDeveloperDetailResponse)
async def get_developer(
    developer_id: UUID,
    db: Session = Depends(get_db)
):
    """Get developer profile by ID"""
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.id == developer_id
    ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer not found"
        )

    return MCPDeveloperDetailResponse.from_orm(developer)


# ============================================================================
# MCP SUBMISSION
# ============================================================================

@router.post("/mcps", response_model=dict)
async def submit_mcp(
    mcp_data: MCPSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an MCP for marketplace approval

    Requires verified developer account
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
            detail="No developer account found. Register first at /api/mcp-developers/register"
        )

    # Check if developer is verified
    if not developer.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer account must be verified by platform admin before submitting MCPs"
        )

    # Check if MCP name already exists
    existing = db.query(MCP).filter(MCP.name == mcp_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP with this name already exists"
        )

    # Create MCP in pending status
    mcp = MCP(
        developer_id=developer.id,
        name=mcp_data.name,
        display_name=mcp_data.display_name,
        version=mcp_data.version,
        description=mcp_data.description,
        category=mcp_data.category,
        subcategory=mcp_data.subcategory,
        tags=mcp_data.tags,
        capabilities=mcp_data.capabilities,
        supported_languages=mcp_data.supported_languages,
        max_context_length=mcp_data.max_context_length,
        icon=mcp_data.icon,
        icon_color=mcp_data.icon_color,
        pricing_model=mcp_data.pricing_model,
        price_per_month_cents=mcp_data.price_per_month_cents,
        min_gpu_memory_gb=mcp_data.min_gpu_memory_gb,
        gpu_required=mcp_data.gpu_required,
        approval_status="pending",  # Pending admin approval
        submitted_at=datetime.utcnow(),
        status="active",
        published=False  # Not published until approved
    )

    db.add(mcp)

    # Update developer stats
    developer.total_mcps += 1

    db.commit()
    db.refresh(mcp)

    return {
        "success": True,
        "message": "MCP submitted for approval",
        "mcp_id": str(mcp.id),
        "status": "pending"
    }


@router.get("/mcps/my", response_model=List[dict])
async def list_my_mcps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List MCPs submitted by current developer

    Returns all MCPs (pending, approved, rejected)
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

    # Get all MCPs by this developer
    mcps = db.query(MCP).filter(MCP.developer_id == developer.id).all()

    return [
        {
            "id": str(mcp.id),
            "name": mcp.name,
            "display_name": mcp.display_name,
            "version": mcp.version,
            "approval_status": mcp.approval_status,
            "submitted_at": mcp.submitted_at.isoformat() if mcp.submitted_at else None,
            "approved_at": mcp.approved_at.isoformat() if mcp.approved_at else None,
            "install_count": mcp.install_count,
            "rating": float(mcp.rating) if mcp.rating else 0.0,
            "rejection_reason": mcp.rejection_reason
        }
        for mcp in mcps
    ]


# ============================================================================
# STRIPE ONBOARDING (Placeholder)
# ============================================================================

@router.post("/stripe/onboard")
async def stripe_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start Stripe Connect onboarding

    TODO: Implement Stripe Connect integration for revenue sharing
    """
    developer = db.query(MCPDeveloper).filter(
        MCPDeveloper.user_id == current_user.id
    ).first()

    if not developer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer account found"
        )

    # TODO: Create Stripe Connect account and return onboarding URL

    return {
        "success": False,
        "message": "Stripe Connect integration not yet implemented"
    }
