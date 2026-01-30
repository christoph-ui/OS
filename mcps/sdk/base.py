"""
0711 MCP SDK - Base Class

The ONLY interface MCPs need to implement.

Architecture:
    Core provides:
    - Lakehouse access (query_data)
    - Model access (generate with LoRA)
    - Embedding access (embed)

    MCP provides:
    - Business logic (process)
    - LoRA adapter path (optional)
    - Output formatting

Example:
    from mcps.sdk import BaseMCP

    class TaxMCP(BaseMCP):
        name = "ctax"
        version = "1.0.0"
        lora_adapter = "adapters/ctax-lora"

        async def process(self, input, context):
            # Query customer's tax documents
            docs = self.query_data("SELECT * FROM tax_documents")

            # Generate with tax-specialized LoRA
            result = await self.generate(
                f"Analyze these tax documents: {docs}\\n"
                f"Question: {input}"
            )

            return {"answer": result, "confidence": 0.95}
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPContext:
    """
    Execution context injected by the platform.

    Contains access to all platform services.
    MCPs don't create this - the Platform injects it.

    Multi-tenancy:
        - customer_id: Required for data isolation
        - user_id: Optional, for audit/tracking
        - All data operations are filtered by customer_id
    """
    # Identifiers (multi-tenancy)
    customer_id: str
    user_id: Optional[str] = None
    engagement_id: Optional[str] = None

    # Services (injected by Platform)
    _model_server: Optional[Any] = None
    _lakehouse: Optional[Any] = None
    _vector_store: Optional[Any] = None

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.customer_id:
            raise ValueError("customer_id is required for data isolation")


@dataclass
class MCPResponse:
    """Standard response from MCP processing"""
    data: Any
    confidence: float = 1.0
    requires_review: bool = False
    review_reason: Optional[str] = None
    model_used: Optional[str] = None
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMCP(ABC):
    """
    Base class for all MCPs.

    Minimal interface - implement only what you need.

    Required:
        name: str           - Unique identifier (e.g., "ctax", "law")
        version: str        - Semantic version (e.g., "1.0.0")
        process()           - Your business logic

    Optional:
        lora_adapter: str   - Path to LoRA adapter (.safetensors)
        description: str    - Human-readable description
        category: str       - Category (e.g., "finance", "legal")

    Core Provides (just use these):
        generate()          - Text generation with your LoRA
        embed()             - Vector embeddings
        query_data()        - Query customer's lakehouse
        search_similar()    - Vector similarity search
    """

    # Required - override in subclass
    name: str
    version: str

    # Optional - override if needed
    lora_adapter: Optional[str] = None  # Path to .safetensors
    description: str = ""
    category: str = "general"

    def __init__(self):
        """Initialize MCP"""
        self._context: Optional[MCPContext] = None
        self._validate()

    def _validate(self):
        """Validate MCP has required attributes"""
        if not getattr(self, 'name', None):
            raise ValueError(f"{self.__class__.__name__} must define 'name'")
        if not getattr(self, 'version', None):
            raise ValueError(f"{self.__class__.__name__} must define 'version'")

    def set_context(self, context: MCPContext):
        """Set execution context (called by Platform)"""
        self._context = context

    # =========================================================================
    # ABSTRACT METHOD - Implement this
    # =========================================================================

    @abstractmethod
    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[MCPResponse, Dict[str, Any], str]:
        """
        Main processing method - implement your business logic here.

        Args:
            input: User input (query, file path, structured data, etc.)
            context: Optional additional context

        Returns:
            MCPResponse, dict, or string with results

        Example:
            async def process(self, input, context=None):
                # 1. Get relevant data from lakehouse
                docs = self.query_data(f"SELECT * FROM documents WHERE topic='{input}'")

                # 2. Generate response with your LoRA
                response = await self.generate(
                    f"Based on these documents: {docs}\\n"
                    f"Answer: {input}"
                )

                # 3. Return result
                return MCPResponse(
                    data={"answer": response},
                    confidence=0.92
                )
        """
        pass

    # =========================================================================
    # CORE PROVIDES - Just use these methods
    # =========================================================================

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text using Mixtral + your LoRA adapter.

        The platform automatically loads your LoRA adapter when processing.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated text

        Example:
            response = await self.generate(
                "Explain the German VAT regulations for digital services.",
                max_tokens=500,
                temperature=0.3
            )
        """
        if not self._context or not self._context._model_server:
            raise RuntimeError("Model server not available. Set context first.")

        return await self._context._model_server.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            adapter=self.name if self.lora_adapter else None,
            **kwargs
        )

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Uses multilingual-e5-large for German/English support.

        Args:
            text: Single text or list of texts

        Returns:
            List of embedding vectors

        Example:
            embeddings = await self.embed("Umsatzsteuervoranmeldung")
            similar_docs = self.search_similar(embeddings[0])
        """
        if not self._context or not self._context._model_server:
            raise RuntimeError("Model server not available. Set context first.")

        texts = [text] if isinstance(text, str) else text
        result = await self._context._model_server.embed(texts)
        return result.embeddings

    def query_data(
        self,
        query: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query customer's lakehouse using SQL.

        Access Delta tables with customer's ingested data.

        Args:
            query: SQL query
            limit: Maximum rows to return

        Returns:
            List of row dictionaries

        Example:
            # Get all tax documents
            docs = self.query_data(
                "SELECT * FROM documents WHERE category = 'tax'"
            )

            # Get specific invoices
            invoices = self.query_data(
                "SELECT * FROM invoices WHERE year = 2024 LIMIT 50"
            )
        """
        if not self._context or not self._context._lakehouse:
            logger.warning("Lakehouse not available")
            return []

        return self._context._lakehouse.query(
            query=query,
            customer_id=self._context.customer_id,
            limit=limit
        )

    def search_similar(
        self,
        vector: List[float],
        limit: int = 10,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            vector: Query embedding vector
            limit: Maximum results
            filter_category: Optional category filter

        Returns:
            List of similar documents with scores

        Example:
            # First embed the query
            embeddings = await self.embed("VAT regulations")

            # Then find similar docs
            similar = self.search_similar(embeddings[0], limit=5)
        """
        if not self._context or not self._context._vector_store:
            logger.warning("Vector store not available")
            return []

        return self._context._vector_store.search(
            vector=vector,
            customer_id=self._context.customer_id,
            limit=limit,
            filter_category=filter_category
        )

    def store_result(
        self,
        data: Dict[str, Any],
        table: str = "mcp_results"
    ) -> str:
        """
        Store result in customer's lakehouse.

        Args:
            data: Data to store
            table: Target table name

        Returns:
            Record ID

        Example:
            result_id = self.store_result({
                "tax_calculation": 12500.00,
                "vat_rate": 0.19,
                "period": "Q4-2024"
            })
        """
        if not self._context or not self._context._lakehouse:
            logger.warning("Lakehouse not available")
            return ""

        return self._context._lakehouse.store(
            table=table,
            data=data,
            mcp=self.name,
            customer_id=self._context.customer_id
        )

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def log(self, message: str, level: str = "info"):
        """Log a message with MCP prefix"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.name}] {message}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if not self._context:
            return default
        return self._context.config.get(key, default)

    @property
    def info(self) -> Dict[str, Any]:
        """Get MCP info as dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "lora_adapter": self.lora_adapter
        }

    def __repr__(self):
        return f"<MCP {self.name} v{self.version}>"
