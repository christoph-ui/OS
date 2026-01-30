"""
Workflow schemas for API requests/responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# Workflow Marketplace Schemas
# ============================================================================

class WorkflowResponse(BaseModel):
    """Basic workflow response"""
    id: UUID
    name: str
    display_name: str
    version: str
    description: str
    category: str
    icon: str
    icon_color: str
    required_mcps: List[str]
    estimated_duration_minutes: Optional[int]
    complexity_level: str
    pricing_model: str
    price_per_month_cents: Optional[int]
    price_per_execution_cents: Optional[int]
    rating: float
    install_count: int
    featured: bool

    class Config:
        orm_mode = True
        from_attributes = True


class WorkflowDetailResponse(WorkflowResponse):
    """Detailed workflow response"""
    subcategory: Optional[str]
    tags: List[str]
    verified: bool
    active_subscriptions: int
    total_executions: int
    review_count: int
    avg_execution_time_ms: Optional[int]
    success_rate: float
    created_at: datetime
    published_at: Optional[datetime]

    # Include definition preview
    step_count: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Paginated workflow list"""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Workflow Subscription Schemas
# ============================================================================

class WorkflowSubscribeRequest(BaseModel):
    """Subscribe to a workflow"""
    workflow_id: UUID
    config: Optional[Dict[str, Any]] = {}
    schedule_enabled: Optional[bool] = False
    schedule_cron: Optional[str] = None


class WorkflowSubscriptionResponse(BaseModel):
    """Workflow subscription response"""
    id: UUID
    workflow_id: UUID
    customer_id: UUID
    enabled: bool
    status: str
    config: Dict[str, Any]
    schedule_enabled: bool
    schedule_cron: Optional[str]
    total_executions: int
    successful_executions: int
    subscribed_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================================================
# Workflow Execution Schemas
# ============================================================================

class WorkflowExecuteRequest(BaseModel):
    """Execute a workflow"""
    workflow_id: UUID
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = {}


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response"""
    id: UUID
    workflow_id: UUID
    customer_id: UUID
    status: str
    current_step: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    steps_completed: int
    steps_failed: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class WorkflowExecutionDetailResponse(WorkflowExecutionResponse):
    """Detailed execution response with step logs"""
    state_snapshot: Optional[Dict[str, Any]]
    retry_count: int
    cost_cents: int
    trigger_type: str
    step_logs: Optional[List[Dict[str, Any]]] = []

    class Config:
        orm_mode = True
        from_attributes = True


class WorkflowStepLogResponse(BaseModel):
    """Workflow step log response"""
    id: UUID
    step_index: int
    step_id: str
    step_name: str
    mcp_name: str
    mcp_action: str
    status: str
    error_message: Optional[str]
    duration_ms: int
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================================================
# Workflow Builder Schemas (Custom Workflows)
# ============================================================================

class WorkflowNodeCreate(BaseModel):
    """Node definition for custom workflow"""
    id: str = Field(..., pattern="^[a-z0-9_]+$")
    mcp: str
    action: str
    config: Optional[Dict[str, Any]] = {}


class WorkflowEdgeCreate(BaseModel):
    """Edge definition for custom workflow"""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    condition: Optional[str] = None

    class Config:
        populate_by_name = True


class WorkflowDefinitionCreate(BaseModel):
    """Create custom workflow definition"""
    nodes: List[WorkflowNodeCreate] = Field(..., min_items=1)
    edges: List[WorkflowEdgeCreate] = Field(..., min_items=1)
    entry_point: str

    @validator('entry_point')
    def validate_entry_point(cls, v, values):
        """Ensure entry_point exists in nodes"""
        if 'nodes' in values:
            node_ids = [node.id for node in values['nodes']]
            if v not in node_ids:
                raise ValueError(f"Entry point '{v}' not found in nodes")
        return v


class WorkflowCreate(BaseModel):
    """Create custom workflow"""
    name: str = Field(..., pattern="^[a-z0-9-]+$", min_length=3, max_length=100)
    display_name: str = Field(..., min_length=3, max_length=255)
    description: str
    category: str
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = []
    icon: Optional[str] = "🔄"
    icon_color: Optional[str] = "blue"
    definition: WorkflowDefinitionCreate
    pricing_model: str = "free"
    price_per_month_cents: Optional[int] = None
    price_per_execution_cents: Optional[int] = None


class WorkflowUpdate(BaseModel):
    """Update custom workflow"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    pricing_model: Optional[str] = None
    price_per_month_cents: Optional[int] = None
