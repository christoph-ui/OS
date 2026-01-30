"""
Base MCP class
All MCPs inherit from this
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
import logging

from .types import ModelSpec, MCPMetadata, TaskInput, TaskOutput, UsageMetrics


logger = logging.getLogger(__name__)


@dataclass
class MCPContext:
    """
    Execution context for MCP operations

    Provides access to:
    - Model server for inference
    - Lakehouse for data storage/retrieval
    - Configuration
    - Customer data
    """
    engagement_id: str
    customer_id: str
    expert_id: str
    installation_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    customer_data_path: Optional[str] = None

    # Services (injected by runtime)
    model_server: Optional[Any] = None
    lakehouse: Optional[Any] = None
    vector_store: Optional[Any] = None


class BaseMCP(ABC):
    """
    Base class for all MCPs

    MCPs are self-contained AI solutions that solve specific business problems.

    Example:
        class CTaxMCP(BaseMCP):
            metadata = MCPMetadata(
                id="CTAX",
                name="German Tax Engine",
                version="2.0.0",
                category="Finance",
                ...
            )

            models = [
                ModelSpec(
                    name="invoice-ocr",
                    type=ModelType.VISION,
                    size_gb=4.0
                ),
                ...
            ]

            async def process(self, task: TaskInput, ctx: MCPContext) -> TaskOutput:
                # Your business logic here
                ...
    """

    # MCP metadata (override in subclass)
    metadata: MCPMetadata

    # Models used by this MCP (override in subclass)
    models: List[ModelSpec] = []

    def __init__(self):
        """Initialize MCP"""
        self._validate_metadata()
        self._usage_log: List[UsageMetrics] = []

    def _validate_metadata(self):
        """Validate MCP has required metadata"""
        if not hasattr(self, "metadata"):
            raise ValueError(f"{self.__class__.__name__} must define 'metadata'")

        if not self.metadata.id:
            raise ValueError("MCP metadata must include 'id'")
        if not self.metadata.name:
            raise ValueError("MCP metadata must include 'name'")
        if not self.metadata.version:
            raise ValueError("MCP metadata must include 'version'")

    @abstractmethod
    async def process(self, task: TaskInput, ctx: MCPContext) -> TaskOutput:
        """
        Main processing method - implement your business logic here

        Args:
            task: Input task with data and context
            ctx: Execution context with access to services

        Returns:
            TaskOutput with results and confidence score

        Example:
            async def process(self, task: TaskInput, ctx: MCPContext) -> TaskOutput:
                # 1. Load required model
                await self.ensure_model_loaded("invoice-ocr", ctx)

                # 2. Process with AI
                result = await self.generate(
                    prompt="Extract invoice fields...",
                    model="invoice-ocr",
                    ctx=ctx
                )

                # 3. Return result
                return TaskOutput(
                    success=True,
                    confidence=95.0,
                    data=result,
                    model_used="invoice-ocr"
                )
        """
        pass

    # =========================================================================
    # MODEL OPERATIONS
    # =========================================================================

    async def ensure_model_loaded(self, model_name: str, ctx: MCPContext) -> bool:
        """
        Ensure a model is loaded and ready

        Args:
            model_name: Name of the model to load
            ctx: Execution context

        Returns:
            True if model is loaded

        Raises:
            ValueError: If model not found in MCP's model list
            RuntimeError: If model server not available
        """
        # Find model spec
        model_spec = self.get_model_spec(model_name)
        if not model_spec:
            raise ValueError(f"Model '{model_name}' not found in {self.metadata.id}")

        if not ctx.model_server:
            raise RuntimeError("Model server not available in context")

        # Request model loading from model server
        try:
            is_loaded = await ctx.model_server.ensure_loaded(model_spec)
            if is_loaded:
                logger.info(f"Model {model_name} loaded for {self.metadata.id}")
            return is_loaded
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        model: str,
        ctx: MCPContext,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Generate text using specified model

        Args:
            prompt: Input prompt
            model: Model name
            ctx: Execution context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            **kwargs: Additional model parameters

        Returns:
            Generated text
        """
        start_time = time.time()

        # Ensure model is loaded
        await self.ensure_model_loaded(model, ctx)

        if not ctx.model_server:
            raise RuntimeError("Model server not available")

        # Generate
        result = await ctx.model_server.generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        # Track usage
        processing_time = int((time.time() - start_time) * 1000)
        self._track_usage(
            model=model,
            input_tokens=len(prompt.split()),  # Rough estimate
            output_tokens=len(result.split()),
            processing_time_ms=processing_time,
            ctx=ctx
        )

        return result

    async def embed(self, text: str, ctx: MCPContext) -> List[float]:
        """
        Generate embeddings for text

        Args:
            text: Text to embed
            ctx: Execution context

        Returns:
            Embedding vector
        """
        if not ctx.model_server:
            raise RuntimeError("Model server not available")

        return await ctx.model_server.embed(text)

    def get_model_spec(self, model_name: str) -> Optional[ModelSpec]:
        """Get model specification by name"""
        for model in self.models:
            if model.name == model_name:
                return model
        return None

    # =========================================================================
    # LAKEHOUSE OPERATIONS
    # =========================================================================

    def query_lakehouse(
        self,
        query: str,
        ctx: MCPContext,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query customer's lakehouse for relevant context

        Args:
            query: Search query
            ctx: Execution context
            limit: Maximum results

        Returns:
            List of relevant documents
        """
        if not ctx.lakehouse:
            logger.warning("Lakehouse not available, returning empty results")
            return []

        return ctx.lakehouse.query(
            query=query,
            mcp=self.metadata.id,
            customer_id=ctx.customer_id,
            limit=limit
        )

    def store_result(
        self,
        data: Dict[str, Any],
        ctx: MCPContext,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store result in customer's lakehouse

        Args:
            data: Data to store
            ctx: Execution context
            metadata: Additional metadata

        Returns:
            Document ID
        """
        if not ctx.lakehouse:
            logger.warning("Lakehouse not available, cannot store result")
            return ""

        return ctx.lakehouse.store(
            data=data,
            mcp=self.metadata.id,
            engagement_id=ctx.engagement_id,
            customer_id=ctx.customer_id,
            metadata=metadata or {}
        )

    def search_similar(
        self,
        vector: List[float],
        ctx: MCPContext,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity

        Args:
            vector: Query vector
            ctx: Execution context
            limit: Maximum results

        Returns:
            List of similar documents
        """
        if not ctx.vector_store:
            logger.warning("Vector store not available")
            return []

        return ctx.vector_store.search_similar(
            vector=vector,
            customer_id=ctx.customer_id,
            limit=limit
        )

    # =========================================================================
    # USAGE TRACKING & BILLING
    # =========================================================================

    def _track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        processing_time_ms: int,
        ctx: MCPContext,
        task_id: Optional[str] = None
    ):
        """Track usage for billing"""
        metrics = UsageMetrics(
            mcp_id=self.metadata.id,
            engagement_id=ctx.engagement_id,
            task_id=task_id or "unknown",
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time_ms=processing_time_ms
        )

        self._usage_log.append(metrics)

        # Flush periodically
        if len(self._usage_log) >= 10:
            self._flush_usage_log()

    def _flush_usage_log(self):
        """Flush usage log to billing system"""
        if not self._usage_log:
            return

        # TODO: Send to billing API
        logger.debug(f"Flushing {len(self._usage_log)} usage records for {self.metadata.id}")
        self._usage_log = []

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def get_config(self, key: str, ctx: MCPContext, default: Any = None) -> Any:
        """Get configuration value"""
        return ctx.config.get(key, default)

    def log(self, message: str, level: str = "info"):
        """Log message"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.metadata.id}] {message}")

    @property
    def total_gpu_memory_required_gb(self) -> float:
        """Calculate total GPU memory required for all models"""
        return sum(model.memory_required_gb() for model in self.models)

    def __repr__(self):
        return f"<MCP {self.metadata.id} v{self.metadata.version}>"
