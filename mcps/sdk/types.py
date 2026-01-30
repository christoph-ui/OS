"""
Type definitions for MCP SDK
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ModelType(str, Enum):
    """Type of AI model"""
    TEXT = "text"
    VISION = "vision"
    MULTIMODAL = "multimodal"
    EMBEDDING = "embedding"


@dataclass
class ModelSpec:
    """
    Specification for a model used by an MCP

    Example:
        ModelSpec(
            name="german-invoice-ocr-v2",
            type=ModelType.VISION,
            size_gb=4.0,
            quantization="Q4_K_M",
            file_path="models/invoice-ocr-3b.gguf"
        )
    """
    name: str
    type: ModelType
    size_gb: float
    quantization: str = "Q4_K_M"
    base_model: Optional[str] = None
    lora_adapter: Optional[str] = None
    file_path: Optional[str] = None
    context_length: int = 4096
    requires_gpu: bool = True

    def memory_required_gb(self) -> float:
        """Calculate GPU memory needed"""
        base = self.size_gb

        # LoRA uses base model + small adapter
        if self.lora_adapter:
            return base * 0.7 + 0.1

        # Add overhead for KV cache and inference
        return base * 1.2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type.value,
            "size_gb": self.size_gb,
            "quantization": self.quantization,
            "base_model": self.base_model,
            "lora_adapter": self.lora_adapter,
            "file_path": self.file_path,
            "context_length": self.context_length,
            "requires_gpu": self.requires_gpu
        }


@dataclass
class MCPMetadata:
    """
    Metadata for an MCP

    Example:
        MCPMetadata(
            id="CTAX",
            name="German Tax Engine",
            version="2.1.0",
            category="Finance",
            description="Full German tax calculation, ELSTER filing, audit preparation",
            author="0711 Intelligence",
            tools=["Tax Calculation", "ELSTER Filing", "Audit Prep"],
            automation_rate=92.0
        )
    """
    id: str
    name: str
    version: str
    category: str
    description: str
    author: str
    tools: List[str] = field(default_factory=list)
    automation_rate: float = 0.0
    supported_languages: List[str] = field(default_factory=lambda: ["de", "en"])
    compliance_standards: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "author": self.author,
            "tools": self.tools,
            "automation_rate": self.automation_rate,
            "supported_languages": self.supported_languages,
            "compliance_standards": self.compliance_standards,
            "integrations": self.integrations
        }


@dataclass
class TaskInput:
    """Input data for a task"""
    task_id: str
    task_type: str
    data: Dict[str, Any]
    files: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskOutput:
    """Output from task processing"""
    success: bool
    confidence: float  # 0-100
    data: Dict[str, Any]
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    model_used: Optional[str] = None
    requires_review: bool = False
    review_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "confidence": self.confidence,
            "data": self.data,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used,
            "requires_review": self.requires_review,
            "review_reason": self.review_reason
        }


@dataclass
class UsageMetrics:
    """Usage metrics for billing"""
    mcp_id: str
    engagement_id: str
    task_id: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    processing_time_ms: int = 0
    billable_units: int = 1  # e.g., 1 document, 1 request
    cost_cents: int = 0
