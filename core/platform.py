"""
0711 Platform

The main entry point for the 0711 Intelligence Platform.
Clean, minimal interface - just like Ray.

Usage:
    from zero711 import Platform

    platform = Platform()
    platform.ingest("/data/Buchhaltung", mcp="ctax")
    result = await platform.query("What's our Q4 tax liability?")
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from .config import PlatformConfig, config as default_config

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from a platform query"""
    answer: str
    confidence: float
    mcp_used: str
    sources: List[str]
    metadata: Dict[str, Any]


class Platform:
    """
    0711 Intelligence Platform

    The clean, unified entry point for:
    - Data ingestion (folder → lakehouse)
    - Querying with MCPs (natural language → answer)
    - Direct MCP access

    Example:
        # Initialize
        platform = Platform(lakehouse_path="/data/lakehouse")

        # Ingest data
        platform.ingest("/data/Buchhaltung", mcp="ctax")
        platform.ingest("/data/Vertraege", mcp="law")

        # Query
        result = await platform.query("What's our Q4 tax liability?")
        print(result.answer)

        # Direct MCP access
        ctax = platform.get_mcp("ctax")
        response = await ctax.process("Calculate VAT for €10,000")
    """

    def __init__(
        self,
        lakehouse_path: Union[str, Path] = None,
        vllm_url: str = None,
        config: PlatformConfig = None
    ):
        """
        Initialize the platform.

        Args:
            lakehouse_path: Path to lakehouse storage (shared/default)
            vllm_url: URL of vLLM inference server (shared/default)
            config: Full configuration (overrides individual params)

        Note:
            For multi-customer deployments, lakehouse_path and vllm_url
            are per-customer and loaded from customer_registry.
        """
        self._config = config or default_config

        # Override with explicit params
        if lakehouse_path:
            self._config.lakehouse_path = Path(lakehouse_path)
        if vllm_url:
            self._config.vllm_url = vllm_url

        # Initialize components (lazy loading)
        self._registry = None
        self._model_server = None
        self._lakehouse = None
        self._ingestion = None
        self._customer_registry = None
        self._initialized = False

        logger.info(f"Platform initialized with lakehouse at {self._config.lakehouse_path}")

    async def _ensure_initialized(self):
        """Lazy initialization of components"""
        if self._initialized:
            return

        # Import here to avoid circular imports
        from mcps.registry import get_registry
        from inference import get_model_server
        from core.customer_registry import initialize_registry

        # Initialize MCP registry
        self._registry = get_registry()
        if self._config.auto_load_core_mcps:
            self._registry.load_core_mcps()

        # Initialize customer registry (for routing)
        self._customer_registry = await initialize_registry()

        # Initialize model server (default/shared)
        self._model_server = get_model_server()

        # Initialize lakehouse (default/shared)
        try:
            from lakehouse import Lakehouse
            self._lakehouse = Lakehouse(self._config.lakehouse_path)
        except ImportError:
            logger.warning("Lakehouse not available")

        self._initialized = True
        logger.info("Platform fully initialized with customer registry")

    def _ensure_initialized_sync(self):
        """Synchronous initialization check"""
        if not self._initialized:
            try:
                # Try to get the running loop (if we're in an async context)
                loop = asyncio.get_running_loop()
                # If we're in an async context, we can't use run_until_complete
                # This would need to be called from async code instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._ensure_initialized())
                    future.result()
            except RuntimeError:
                # No running loop - safe to use asyncio.run()
                asyncio.run(self._ensure_initialized())

    # =========================================================================
    # INGESTION
    # =========================================================================

    def ingest(
        self,
        path: Union[str, Path],
        mcp: str = None,
        recursive: bool = True,
        file_types: List[str] = None,
        customer_id: str = None
    ) -> Dict[str, Any]:
        """
        Ingest documents from a folder into the lakehouse.

        Args:
            path: Path to folder or file
            mcp: MCP to associate with (for categorization)
            recursive: Process subdirectories
            file_types: Specific file types to process (e.g., [".pdf", ".docx"])
            customer_id: Customer ID for multi-tenancy isolation

        Returns:
            Ingestion statistics

        Example:
            # Ingest tax documents for a customer
            stats = platform.ingest(
                "/data/Buchhaltung",
                mcp="ctax",
                customer_id="acme_corp"
            )
            print(f"Processed {stats['files_processed']} files")
        """
        self._ensure_initialized_sync()

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        # Require customer_id for production
        if not customer_id:
            customer_id = "default"
            logger.warning("No customer_id provided, using 'default'")

        logger.info(f"Starting ingestion from {path} for MCP: {mcp}, customer: {customer_id}")

        try:
            from ingestion import IngestionOrchestrator

            orchestrator = IngestionOrchestrator(
                lakehouse_path=self._config.lakehouse_path,
                vllm_url=self._config.vllm_url
            )

            # Run ingestion with customer_id
            stats = orchestrator.ingest_folder(
                folder_path=path,
                mcp_category=mcp,
                recursive=recursive,
                file_types=file_types,
                customer_id=customer_id
            )

            logger.info(f"Ingestion complete: {stats}")
            return stats

        except ImportError:
            logger.error("Ingestion module not available")
            return {"error": "Ingestion module not available"}

    # =========================================================================
    # QUERYING
    # =========================================================================

    async def query(
        self,
        question: str,
        mcp: str = None,
        context: Dict[str, Any] = None
    ) -> QueryResult:
        """
        Query the platform with natural language.

        Automatically routes to the appropriate MCP based on the question.

        Args:
            question: Natural language question
            mcp: Specific MCP to use (optional, auto-routes if not specified)
            context: Additional context

        Returns:
            QueryResult with answer and metadata

        Example:
            # Auto-route based on question
            result = await platform.query("What's our Q4 tax liability?")
            # Routes to CTAX

            result = await platform.query("Summarize our supplier contracts")
            # Routes to LAW

            # Explicit MCP selection
            result = await platform.query("Calculate VAT", mcp="ctax")
        """
        await self._ensure_initialized()

        # Extract customer context
        customer_id = context.get("customer_id", "default") if context else "default"
        user_id = context.get("user_id") if context else None

        # Determine which MCP to use
        target_mcp = mcp or await self._route_query(question)

        logger.info(f"Routing query to MCP: {target_mcp} for customer: {customer_id}")

        # Get customer deployment (for routing to customer containers)
        deployment = self._customer_registry.get_deployment(customer_id)
        if deployment:
            logger.info(f"Using customer deployment: {deployment.vllm_url}, {deployment.lakehouse_url}")
            # Create customer-specific lakehouse client
            # For HTTP-based lakehouse, we'll pass the URL in context
            customer_lakehouse_url = deployment.lakehouse_url
            customer_vllm_url = deployment.vllm_url
        else:
            logger.warning(f"No deployment found for customer {customer_id}, using shared lakehouse")
            customer_lakehouse_url = None
            customer_vllm_url = self._config.vllm_url

        # Get relevant documents for RAG
        documents_result = await self.browse_documents(
            customer_id=customer_id,
            page=1,
            page_size=10  # Get top 10 documents for context
        )
        context_documents = documents_result.get("documents", [])

        # Use Claude Sonnet 4.5 for chat (bypasses MCP/vLLM complexity)
        from core.claude_chat import get_claude_chat

        claude = get_claude_chat()

        # Call Claude with RAG context
        claude_response = await claude.chat(
            message=question,
            context_documents=context_documents,
            customer_id=customer_id,
            system_prompt=None  # Use default
        )

        # Convert Claude response to QueryResult format
        # Include suggested_questions and all metadata from Claude
        full_metadata = {
            **claude_response.get('metadata', {}),
            'suggested_questions': claude_response.get('suggested_questions', []),
            'usage': claude_response.get('usage', {}),
            'model': claude_response.get('model', 'unknown')
        }

        response = type('obj', (object,), {
            'data': {
                'answer': claude_response['answer'],
                'sources': claude_response['sources']
            },
            'confidence': claude_response['confidence'],
            'metadata': full_metadata
        })()

        # Normalize response
        if hasattr(response, 'data'):
            answer = response.data.get('answer') or response.data.get('analysis') or str(response.data)
            confidence = response.confidence
            sources = response.data.get('sources', [])
            metadata = response.metadata if hasattr(response, 'metadata') else {}
        else:
            answer = str(response)
            confidence = 0.8
            sources = []
            metadata = {}

        return QueryResult(
            answer=answer,
            confidence=confidence,
            mcp_used=target_mcp,
            sources=sources,
            metadata=metadata
        )

    async def _route_query(self, question: str) -> str:
        """
        Route query to appropriate MCP based on content.

        Uses simple keyword matching for now.
        TODO: Use embeddings for smarter routing.
        """
        question_lower = question.lower()

        # Tax keywords
        tax_keywords = [
            "steuer", "tax", "vat", "ust", "mwst", "umsatzsteuer",
            "elster", "finanzamt", "steuererklärung", "vorsteuer"
        ]

        # Legal keywords
        legal_keywords = [
            "vertrag", "contract", "rechtlich", "legal", "klausel",
            "haftung", "kündigung", "gdpr", "dsgvo", "compliance"
        ]

        # Tender keywords
        tender_keywords = [
            "ausschreibung", "tender", "rfp", "angebot", "bid",
            "vergabe", "leistungsverzeichnis", "vob", "vol"
        ]

        # Market intelligence keywords (NEW)
        market_keywords = [
            "competitor", "competitive", "market", "pricing", "compare",
            "alternative", "vs", "versus", "positioning", "market share",
            "distributor", "coverage", "gap", "opportunity", "abb", "siemens",
            "schneider", "analysis", "intelligence"
        ]

        # Publishing/content keywords (NEW)
        publish_keywords = [
            "generate", "create", "listing", "amazon", "datasheet",
            "linkedin", "content", "export", "bmecat", "feed", "publish",
            "marketing", "seo", "description", "catalog"
        ]

        # Score each MCP
        scores = {
            "market": sum(1 for k in market_keywords if k in question_lower),
            "publish": sum(1 for k in publish_keywords if k in question_lower),
            "ctax": sum(1 for k in tax_keywords if k in question_lower),
            "law": sum(1 for k in legal_keywords if k in question_lower),
            "tender": sum(1 for k in tender_keywords if k in question_lower)
        }

        # Return highest scoring MCP
        # Priority: MARKET > PUBLISH > Specialized (CTAX, LAW, TENDER)
        best_mcp = max(scores, key=scores.get)

        # If no keywords match, default to MARKET (never CTAX)
        if scores[best_mcp] == 0:
            return "market"  # Default to market intelligence

        return best_mcp

    # =========================================================================
    # MCP ACCESS
    # =========================================================================

    def get_mcp(self, mcp_id: str):
        """
        Get an MCP instance by ID.

        Args:
            mcp_id: MCP identifier (e.g., "ctax", "law", "tender")

        Returns:
            MCP instance

        Example:
            ctax = platform.get_mcp("ctax")
            result = await ctax.process("Calculate VAT for €10,000")
        """
        self._ensure_initialized_sync()

        mcp = self._registry.get(mcp_id)
        if not mcp:
            raise ValueError(f"MCP '{mcp_id}' not found")

        # Note: Context should be set when using the MCP with proper customer_id
        # This method returns the MCP without context - caller should set it
        logger.info(f"Retrieved MCP '{mcp_id}' - caller should set customer context")

        return mcp

    # =========================================================================
    # DATA BROWSING (Customer-aware)
    # =========================================================================

    async def browse_documents(
        self,
        customer_id: str,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Browse documents for a customer.

        Routes to customer-specific lakehouse container.

        Args:
            customer_id: Customer ID
            category: Optional category filter
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            Dict with documents list and pagination info
        """
        await self._ensure_initialized()

        # Get customer deployment
        deployment = self._customer_registry.get_deployment(customer_id)
        if not deployment:
            raise ValueError(f"No deployment found for customer: {customer_id}")

        # Query customer's lakehouse via HTTP
        import httpx

        lakehouse_url = deployment.lakehouse_url
        offset = (page - 1) * page_size

        # Try multiple table names (customers may have different schemas)
        table_names = ["general_documents", "products_documents", "general_chunks"]
        all_documents = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for table_name in table_names:
                    try:
                        response = await client.get(
                            f"{lakehouse_url}/delta/query/{table_name}",
                            params={"limit": page_size, "offset": offset}
                        )

                        if response.status_code == 200:
                            data = response.json()
                            rows = data.get("rows", [])

                            if rows:
                                logger.info(f"Found {len(rows)} documents in {table_name} for customer {customer_id}")
                                all_documents.extend(rows)
                                break  # Use first table that has data

                    except Exception as e:
                        logger.debug(f"Table {table_name} not available for {customer_id}: {e}")
                        continue

                return {
                    "documents": all_documents[:page_size],
                    "total": len(all_documents),
                    "page": page,
                    "page_size": page_size
                }

        except Exception as e:
            logger.error(f"Error browsing documents for {customer_id}: {e}", exc_info=True)
            return {
                "documents": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "error": str(e)
            }

    def list_mcps(self) -> List[str]:
        """List all available MCPs"""
        self._ensure_initialized_sync()
        return self._registry.list_all()

    def list_core_mcps(self) -> List[str]:
        """List core MCPs"""
        self._ensure_initialized_sync()
        return self._registry.list_core()

    # =========================================================================
    # UTILITIES
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all platform components"""
        await self._ensure_initialized()

        health = {
            "platform": "healthy",
            "lakehouse": "unknown",
            "model_server": "unknown",
            "mcps_loaded": 0
        }

        # Check lakehouse
        if self._lakehouse:
            try:
                health["lakehouse"] = "healthy"
            except:
                health["lakehouse"] = "unhealthy"

        # Check model server
        if self._model_server:
            try:
                status = await self._model_server.health_check()
                health["model_server"] = status.get("status", "unknown")
            except:
                health["model_server"] = "unhealthy"

        # Count MCPs
        health["mcps_loaded"] = len(self._registry)

        return health

    @property
    def config(self) -> PlatformConfig:
        """Get platform configuration"""
        return self._config

    def __repr__(self):
        return f"<Platform lakehouse={self._config.lakehouse_path}>"
