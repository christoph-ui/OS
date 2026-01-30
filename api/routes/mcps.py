"""
MCP marketplace routes
Browse, install, and manage AI models
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.mcp import MCP
from ..models.mcp_installation import MCPInstallation
from ..schemas.mcp import (
    MCPCreate,
    MCPUpdate,
    MCPResponse,
    MCPDetailResponse,
    MCPListResponse,
    MCPInstallRequest,
    MCPInstallationResponse
)
from ..utils.security import get_current_customer_id, require_admin
from ..services.minio_service import minio_service

router = APIRouter()


@router.get("/", response_model=MCPListResponse)
async def list_mcps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    featured_only: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all MCPs in marketplace

    Supports filtering by category, featured status, search
    """
    query = db.query(MCP).filter(
        MCP.status == "active",
        MCP.published == True
    )

    # Apply filters
    if category:
        query = query.filter(MCP.category == category)

    if featured_only:
        query = query.filter(MCP.featured == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                MCP.name.ilike(search_term),
                MCP.display_name.ilike(search_term),
                MCP.description.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Paginate
    mcps = query.order_by(
        MCP.featured.desc(),
        MCP.install_count.desc(),
        MCP.rating.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return MCPListResponse(
        mcps=[MCPResponse.from_orm(m) for m in mcps],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{mcp_id}", response_model=MCPDetailResponse)
async def get_mcp(
    mcp_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed MCP information"""
    mcp = db.query(MCP).filter(MCP.id == mcp_id).first()

    if not mcp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP not found"
        )

    return MCPDetailResponse.from_orm(mcp)


@router.post("/", response_model=MCPResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_mcp(
    mcp_data: MCPCreate,
    db: Session = Depends(get_db)
):
    """
    Create new MCP listing (Admin only)

    Adds a new AI model to the marketplace
    """
    # Check if MCP name already exists
    existing = db.query(MCP).filter(MCP.name == mcp_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP with this name already exists"
        )

    # Create MCP
    mcp = MCP(
        name=mcp_data.name,
        display_name=mcp_data.display_name,
        version=mcp_data.version,
        description=mcp_data.description,
        category=mcp_data.category,
        subcategory=mcp_data.subcategory,
        tags=mcp_data.tags,
        model_type=mcp_data.model_type,
        base_model=mcp_data.base_model,
        model_size_gb=mcp_data.model_size_gb,
        capabilities=mcp_data.capabilities,
        supported_languages=mcp_data.supported_languages,
        max_context_length=mcp_data.max_context_length,
        icon=mcp_data.icon,
        icon_color=mcp_data.icon_color,
        pricing_model=mcp_data.pricing_model,
        min_gpu_memory_gb=mcp_data.min_gpu_memory_gb,
        min_ram_gb=mcp_data.min_ram_gb,
        gpu_required=mcp_data.gpu_required,
        status="active",
        published=True,
        published_at=datetime.utcnow()
    )

    db.add(mcp)
    db.commit()
    db.refresh(mcp)

    return MCPResponse.from_orm(mcp)


@router.post("/install", response_model=MCPInstallationResponse)
async def install_mcp(
    request: MCPInstallRequest,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """
    Install an MCP for customer

    Creates installation record and provides download info
    """
    # Get MCP
    mcp = db.query(MCP).filter(MCP.id == request.mcp_id).first()
    if not mcp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP not found"
        )

    # Check if already installed
    existing = db.query(MCPInstallation).filter(
        and_(
            MCPInstallation.customer_id == customer_id,
            MCPInstallation.mcp_id == request.mcp_id,
            MCPInstallation.status.in_(["installing", "active"])
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP already installed"
        )

    # Create installation record
    installation = MCPInstallation(
        customer_id=customer_id,
        mcp_id=mcp.id,
        deployment_id=request.deployment_id,
        version_installed=mcp.version,
        config=request.config or {},
        status="installing",
        enabled=True
    )

    db.add(installation)

    # Update MCP install count
    mcp.install_count += 1
    mcp.active_installations += 1

    db.commit()
    db.refresh(installation)

    # TODO: Trigger actual installation process
    # For now, just mark as installed
    installation.status = "active"
    installation.installed_at = datetime.utcnow()
    db.commit()

    return MCPInstallationResponse.from_orm(installation)


@router.get("/installations", response_model=List[MCPInstallationResponse])
async def list_installations(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """List customer's installed MCPs"""
    installations = db.query(MCPInstallation).filter(
        MCPInstallation.customer_id == customer_id,
        MCPInstallation.status.in_(["active", "updating"])
    ).all()

    return [MCPInstallationResponse.from_orm(i) for i in installations]


@router.delete("/installations/{installation_id}")
async def uninstall_mcp(
    installation_id: UUID,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Uninstall an MCP"""
    installation = db.query(MCPInstallation).filter(
        MCPInstallation.id == installation_id,
        MCPInstallation.customer_id == customer_id
    ).first()

    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation not found"
        )

    # Mark as uninstalled
    installation.status = "uninstalled"
    installation.uninstalled_at = datetime.utcnow()
    installation.enabled = False

    # Update MCP stats
    mcp = db.query(MCP).filter(MCP.id == installation.mcp_id).first()
    if mcp and mcp.active_installations > 0:
        mcp.active_installations -= 1

    db.commit()

    return {"message": "MCP uninstalled"}
