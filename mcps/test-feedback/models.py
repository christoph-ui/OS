"""
Pydantic models for test feedback system
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    """Test step status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class NetworkFailure(BaseModel):
    """Failed API call details"""
    url: str
    method: str  # GET, POST, etc.
    status: int  # HTTP status code
    error_message: Optional[str] = None
    timestamp: str


class TestStepResult(BaseModel):
    """Individual test step result"""
    journey_id: str = Field(..., description="Test journey identifier (e.g., 'customer_onboarding')")
    step_number: int = Field(..., description="Step number in the journey")
    step_name: str = Field(..., description="Human-readable step name")
    status: TestStatus = Field(..., description="Step status: pass, fail, or skip")
    screenshot_base64: Optional[str] = Field(None, description="Base64-encoded PNG screenshot")
    console_errors: List[str] = Field(default_factory=list, description="Browser console errors")
    network_failures: List[NetworkFailure] = Field(default_factory=list, description="Failed API calls")
    suggestions: List[str] = Field(default_factory=list, description="Claude Desktop's fix suggestions")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    duration_ms: Optional[int] = Field(None, description="Step execution time in milliseconds")

    class Config:
        use_enum_values = True


class TestStepMetadata(BaseModel):
    """Test step metadata (saved to JSON, screenshot separate)"""
    journey_id: str
    step_number: int
    step_name: str
    status: TestStatus
    console_errors: List[str] = Field(default_factory=list)
    network_failures: List[NetworkFailure] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: str
    duration_ms: Optional[int] = None
    screenshot_filename: Optional[str] = Field(None, description="Filename of screenshot PNG")

    class Config:
        use_enum_values = True


class TestRunMetadata(BaseModel):
    """Metadata for a complete test run"""
    run_id: str  # e.g., "2024-01-15T10-30-00_customer_onboarding"
    journey_id: str
    started_at: str  # ISO timestamp
    completed_at: Optional[str] = None
    total_steps: int = 0
    steps_passed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    status: str = "in_progress"  # in_progress, completed, failed


class FailureRecord(BaseModel):
    """Record of an unacknowledged test failure"""
    run_id: str
    journey_id: str
    step_number: int
    step_name: str
    timestamp: str
    console_errors: List[str] = Field(default_factory=list)
    network_failures: List[NetworkFailure] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    screenshot_path: Optional[str] = None
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    action_taken: Optional[str] = None


class AcknowledgeFailureRequest(BaseModel):
    """Request to acknowledge a failure"""
    run_id: str
    step_number: int
    action_taken: str = Field(..., description="What action Claude Code took to fix the issue")


class SubmitResultResponse(BaseModel):
    """Response after submitting a test result"""
    success: bool
    run_id: str
    step_number: int
    message: str
    screenshot_saved: bool = False


class ReportType(str, Enum):
    """Analysis report types"""
    FIX_SUGGESTIONS = "fix_suggestions"
    UX_REVIEW = "ux_review"
    REGRESSION_ANALYSIS = "regression_analysis"
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE_REPORT = "performance_report"
    API_ISSUES = "api_issues"


class ReportPriority(str, Enum):
    """Report priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisReport(BaseModel):
    """Detailed analysis report from Claude Desktop"""
    journey_id: str
    report_type: ReportType
    title: str = Field(..., description="Report title (e.g., 'Signup Form Validation Issues')")
    markdown_content: str = Field(..., description="Full markdown report content")
    related_steps: List[int] = Field(default_factory=list, description="Test steps this report relates to")
    priority: ReportPriority = Field(default=ReportPriority.MEDIUM)
    affected_files: List[str] = Field(default_factory=list, description="Files that need changes")
    timestamp: str
    actioned: bool = False
    actioned_at: Optional[str] = None
    action_taken: Optional[str] = None

    class Config:
        use_enum_values = True


class SubmitReportResponse(BaseModel):
    """Response after submitting an analysis report"""
    success: bool
    run_id: str
    report_id: str
    message: str
