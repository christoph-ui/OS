"""
Connector Marketplace Routes

Dynamic connector marketplace with search, filtering, installation, and reviews.
Replaces the old hardcoded MCP marketplace.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import Customer, User
from ..services.marketplace_service import MarketplaceService
from ..utils.security import get_current_user, get_current_customer

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ConnectorListResponse(BaseModel):
    connectors: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class ConnectorResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    direction: Optional[str]
    icon: Optional[str]
    icon_color: Optional[str]
    logo_url: Optional[str]
    version: Optional[str]
    tags: List[str] = []
    featured: bool = False
    verified: bool = False
    pricing_model: Optional[str]
    price_per_month_cents: Optional[int]
    install_count: int = 0
    rating: float = 0
    review_count: int = 0
    is_first_party: bool = True


class InstallConnectorRequest(BaseModel):
    config: Optional[dict] = None


class CreateReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None


# ============================================================================
# DISCOVERY ROUTES
# ============================================================================

@router.get("/", response_model=ConnectorListResponse)
async def list_connectors(
    search: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    direction: Optional[str] = Query(None, regex="^(input|output|bidirectional)$"),
    pricing: Optional[str] = Query(None, regex="^(free|paid)$"),
    tags: Optional[str] = None,  # Comma-separated
    featured: bool = False,
    verified: bool = False,
    sort: str = Query("popular", regex="^(popular|newest|rating|name)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search and browse connectors
    
    Supports filtering by:
    - search: Text search in name, description, tags
    - category: Main category (data_sources, ai_models, outputs)
    - subcategory: Subcategory (crm, tax, ecommerce, etc.)
    - direction: Data flow direction (input, output, bidirectional)
    - pricing: free or paid
    - tags: Comma-separated list of tags
    - featured: Only featured connectors
    - verified: Only verified connectors
    
    Sort options:
    - popular: Most installations
    - newest: Recently published
    - rating: Highest rated
    - name: Alphabetical
    """
    service = MarketplaceService(db)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    result = service.search_connectors(
        search=search,
        category=category,
        subcategory=subcategory,
        direction=direction,
        pricing=pricing,
        tags=tag_list,
        featured_only=featured,
        verified_only=verified,
        sort_by=sort,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/featured")
async def get_featured_connectors(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get featured connectors for homepage"""
    service = MarketplaceService(db)
    return {
        "success": True,
        "connectors": service.get_featured_connectors(limit)
    }


@router.get("/trending")
async def get_trending_connectors(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get trending connectors (most installations recently)"""
    service = MarketplaceService(db)
    return {
        "success": True,
        "connectors": service.get_trending_connectors(limit)
    }


@router.get("/new")
async def get_new_connectors(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get newest connectors"""
    service = MarketplaceService(db)
    return {
        "success": True,
        "connectors": service.get_new_connectors(limit)
    }


@router.get("/stats")
async def get_marketplace_stats(db: Session = Depends(get_db)):
    """Get marketplace statistics"""
    service = MarketplaceService(db)
    return {
        "success": True,
        "stats": service.get_marketplace_stats()
    }


# ============================================================================
# CATEGORY ROUTES
# ============================================================================

@router.get("/categories")
async def list_categories(
    include_counts: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all connector categories with subcategories
    
    Returns hierarchical category structure:
    - data_sources
      - crm
      - erp
      - cloud_storage
    - ai_models
      - tax
      - legal
    - outputs
      - ecommerce
      - publishing
    """
    service = MarketplaceService(db)
    return {
        "success": True,
        "categories": service.get_categories(include_counts)
    }


@router.get("/categories/{category_slug}")
async def get_category_connectors(
    category_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get connectors in a specific category"""
    service = MarketplaceService(db)
    result = service.get_category_connectors(category_slug, page, page_size)
    return {
        "success": True,
        "category": category_slug,
        **result
    }


# ============================================================================
# CONNECTOR DETAIL ROUTES
# ============================================================================

@router.get("/{connector_id}")
async def get_connector(
    connector_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed connector information"""
    service = MarketplaceService(db)
    connector = service.get_connector(connector_id)
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return {
        "success": True,
        "connector": connector
    }


@router.get("/name/{connector_name}")
async def get_connector_by_name(
    connector_name: str,
    db: Session = Depends(get_db)
):
    """Get connector by name/slug"""
    service = MarketplaceService(db)
    connector = service.get_connector_by_name(connector_name)
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return {
        "success": True,
        "connector": connector
    }


# ============================================================================
# INSTALLATION ROUTES
# ============================================================================

@router.post("/{connector_id}/install", status_code=status.HTTP_201_CREATED)
async def install_connector(
    connector_id: UUID,
    request: InstallConnectorRequest,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Install a connector for the current customer
    
    Creates a Connection record. After installation, credentials
    may need to be configured depending on the connector type.
    """
    service = MarketplaceService(db)
    
    try:
        connection = service.install_connector(
            customer_id=customer.id,
            connector_id=connector_id,
            config=request.config
        )
        
        return {
            "success": True,
            "message": "Connector installed successfully",
            "connection_id": str(connection.id),
            "status": connection.status,
            "next_step": "configure_credentials" if connection.status == "pending" else None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/connections/{connection_id}")
async def uninstall_connector(
    connection_id: UUID,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Uninstall a connector"""
    service = MarketplaceService(db)
    
    success = service.uninstall_connector(customer.id, connection_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    return {
        "success": True,
        "message": "Connector uninstalled successfully"
    }


@router.get("/connections/my")
async def get_my_connections(
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get all connectors installed by the current customer"""
    service = MarketplaceService(db)
    connections = service.get_customer_connections(customer.id)
    
    return {
        "success": True,
        "connections": connections
    }


# ============================================================================
# REVIEW ROUTES
# ============================================================================

@router.get("/{connector_id}/reviews")
async def get_connector_reviews(
    connector_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get reviews for a connector"""
    service = MarketplaceService(db)
    result = service.get_connector_reviews(connector_id, page, page_size)
    
    return {
        "success": True,
        **result
    }


@router.post("/{connector_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(
    connector_id: UUID,
    request: CreateReviewRequest,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a review for a connector
    
    Must have an active connection to leave a review.
    """
    service = MarketplaceService(db)
    
    try:
        review = service.create_review(
            connector_id=connector_id,
            customer_id=customer.id,
            user_id=user.id,
            rating=request.rating,
            title=request.title,
            content=request.content,
            pros=request.pros,
            cons=request.cons
        )
        
        return {
            "success": True,
            "message": "Review created successfully",
            "review_id": str(review.id)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# LEGACY ROUTES (backward compatibility)
# ============================================================================

# Alias for old /api/mcps endpoint
legacy_router = APIRouter(prefix="/api/mcps", tags=["mcps (legacy)"])


@legacy_router.get("/")
async def legacy_list_mcps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Legacy endpoint - use /api/connectors instead"""
    service = MarketplaceService(db)
    result = service.search_connectors(page=page, page_size=page_size)
    return {
        "success": True,
        "deprecated": True,
        "message": "This endpoint is deprecated. Use /api/connectors instead.",
        **result
    }
