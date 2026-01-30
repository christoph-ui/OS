"""
MCP (Model Context Protocol) schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class MCPBase(BaseModel):
    """Base MCP schema"""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., max_length=255)
    version: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    direction: str = Field(default="output")  # "input", "output", "bidirectional"


class MCPCreate(MCPBase):
    """Schema for creating an MCP"""
    subcategory: Optional[str] = None
    model_type: str  # "lora", "full_model", "adapter"
    base_model: Optional[str] = None
    model_size_gb: Optional[Decimal] = None
    capabilities: Optional[dict] = None
    supported_languages: List[str] = Field(default_factory=list)
    max_context_length: Optional[int] = None
    icon: str = "🧠"
    icon_color: str = "orange"
    pricing_model: str = "free"
    min_gpu_memory_gb: Optional[int] = None
    min_ram_gb: Optional[int] = None
    gpu_required: bool = False


class MCPUpdate(BaseModel):
    """Schema for updating MCP information"""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    featured: Optional[bool] = None
    published: Optional[bool] = None
    status: Optional[str] = None


class MCPResponse(BaseModel):
    """Schema for MCP response"""
    id: UUID
    name: str
    display_name: str
    version: str
    description: str
    category: str
    subcategory: Optional[str]
    tags: Optional[List[str]]
    direction: str  # "input", "output", "bidirectional"
    model_type: str
    base_model: Optional[str]
    model_size_gb: Optional[Decimal]
    icon: str
    icon_color: str
    logo_url: Optional[str] = None  # Brand logo URL
    featured: bool
    verified: bool
    pricing_model: str
    price_per_month_cents: Optional[int]
    install_count: int
    active_installations: int
    rating: Decimal
    review_count: int
    avg_automation_rate: Optional[Decimal]
    status: str
    published: bool
    created_at: datetime

    # Connection configuration
    connection_type: Optional[str] = None
    oauth_config: Optional[dict] = None
    api_docs_url: Optional[str] = None
    setup_instructions: Optional[str] = None

    model_config = {"from_attributes": True}


class MCPDetailResponse(MCPResponse):
    """Detailed MCP response with additional fields"""
    capabilities: Optional[dict]
    supported_languages: Optional[List[str]]
    max_context_length: Optional[int]
    minio_bucket: Optional[str]
    minio_path: Optional[str]
    model_hash: Optional[str]
    download_size_bytes: Optional[int]
    avg_response_time_ms: Optional[int]
    min_gpu_memory_gb: Optional[int]
    min_ram_gb: Optional[int]
    gpu_required: bool
    updated_at: datetime
    published_at: Optional[datetime]

    model_config = {"from_attributes": True}


class MCPListResponse(BaseModel):
    """List of MCPs with pagination"""
    mcps: List[MCPResponse]
    total: int
    page: int
    page_size: int


class MCPInstallRequest(BaseModel):
    """Request to install an MCP"""
    mcp_id: UUID
    deployment_id: Optional[UUID] = None
    config: Optional[dict] = None


class MCPInstallationResponse(BaseModel):
    """Response for MCP installation"""
    id: UUID
    mcp_id: UUID
    customer_id: UUID
    deployment_id: Optional[UUID]
    version_installed: str
    status: str
    enabled: bool
    total_queries: int
    health_status: str
    installed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
