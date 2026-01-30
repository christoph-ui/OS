"""
Mock Platform for Testing

Provides a mock implementation of the Platform class for testing
without requiring real LLM, lakehouse, or other infrastructure.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from .mock_responses import MOCK_VLLM_RESPONSES


@dataclass
class MockQueryResult:
    """Mock query result matching Platform.QueryResult"""
    answer: str
    confidence: float
    mcp_used: str
    sources: List[str]
    metadata: Dict[str, Any]


class MockPlatform:
    """
    Mock Platform for testing.

    Returns canned responses based on query keywords.
    No real LLM, lakehouse, or processing required.

    Example:
        platform = MockPlatform()
        result = await platform.query("What is the tax rate?")
        # Returns mock CTAX response
    """

    def __init__(self, lakehouse_path: Path = None, vllm_url: str = None, **kwargs):
        """
        Initialize mock platform.

        Args are accepted but ignored (for compatibility with real Platform).
        """
        self.lakehouse_path = lakehouse_path or Path("/tmp/mock_lakehouse")
        self.vllm_url = vllm_url or "http://mock-vllm:8000"
        self._ingestion_jobs = {}

    async def query(
        self,
        question: str,
        mcp: str = None,
        context: Dict[str, Any] = None
    ) -> MockQueryResult:
        """
        Mock query that returns canned responses.

        Args:
            question: Natural language question
            mcp: Specific MCP (or auto-route)
            context: Additional context (includes customer_id)

        Returns:
            Mock query result
        """
        # Auto-route based on keywords if MCP not specified
        if mcp is None:
            mcp = await self._route_query(question)

        # Get mock response based on MCP
        # First check if explicit MCP is specified
        if mcp == "ctax":
            response_data = MOCK_VLLM_RESPONSES["tax_query"]
            mcp_used = "ctax"
        elif mcp == "law":
            response_data = MOCK_VLLM_RESPONSES["legal_query"]
            mcp_used = "law"
        elif mcp == "tender":
            response_data = MOCK_VLLM_RESPONSES["tender_query"]
            mcp_used = "tender"
        # If no explicit MCP, auto-route based on keywords
        elif "tax" in question.lower() or "vat" in question.lower() or "umsatzsteuer" in question.lower():
            response_data = MOCK_VLLM_RESPONSES["tax_query"]
            mcp_used = "ctax"
        elif "contract" in question.lower() or "legal" in question.lower() or "vertrag" in question.lower():
            response_data = MOCK_VLLM_RESPONSES["legal_query"]
            mcp_used = "law"
        elif "tender" in question.lower() or "ausschreibung" in question.lower() or "rfp" in question.lower():
            response_data = MOCK_VLLM_RESPONSES["tender_query"]
            mcp_used = "tender"
        else:
            # Default response
            response_data = {
                "answer": f"Mock response for: {question}",
                "confidence": 0.75,
                "sources": ["mock_document.pdf"]
            }
            mcp_used = mcp or "ctax"

        # Add small delay to simulate processing
        await asyncio.sleep(0.1)

        return MockQueryResult(
            answer=response_data["answer"],
            confidence=response_data["confidence"],
            mcp_used=mcp_used,
            sources=response_data["sources"],
            metadata={
                "customer_id": context.get("customer_id") if context else "test",
                "mock": True
            }
        )

    async def _route_query(self, question: str) -> str:
        """
        Auto-route query to appropriate MCP based on keywords.

        Args:
            question: Natural language question

        Returns:
            MCP name (ctax, law, tender)
        """
        question_lower = question.lower()

        # Tax keywords (German and English)
        tax_keywords = [
            "tax", "vat", "steuer", "umsatzsteuer", "körperschaftsteuer",
            "elster", "finanzamt", "liability", "steuererklärung"
        ]
        if any(kw in question_lower for kw in tax_keywords):
            return "ctax"

        # Legal keywords
        legal_keywords = [
            "contract", "legal", "vertrag", "compliance", "dsgvo",
            "gdpr", "law", "recht", "klausel", "agb"
        ]
        if any(kw in question_lower for kw in legal_keywords):
            return "law"

        # Tender keywords
        tender_keywords = [
            "tender", "ausschreibung", "rfp", "vob", "procurement",
            "bid", "proposal", "submission"
        ]
        if any(kw in question_lower for kw in tender_keywords):
            return "tender"

        # Default to CTAX
        return "ctax"

    def ingest(
        self,
        path: str,
        mcp: str = None,
        recursive: bool = True,
        file_types: List[str] = None,
        customer_id: str = None
    ) -> Dict[str, Any]:
        """
        Mock ingestion that simulates file processing.

        Args:
            path: Path to folder
            mcp: MCP to associate with
            recursive: Process subdirectories
            file_types: File types to include
            customer_id: Customer ID

        Returns:
            Mock ingestion statistics
        """
        import uuid

        # Generate job ID
        job_id = str(uuid.uuid4())[:8]

        # Simulate finding files (try to count from MinIO or use smart defaults)
        files_found = 0

        if "customer-" in path:
            # Try to extract bucket name and count actual files
            try:
                # Extract bucket name from path like "/data/customer-xxx"
                import re
                bucket_match = re.search(r'customer-[a-f0-9-]+', path)
                if bucket_match and hasattr(self, '_minio_client'):
                    bucket_name = bucket_match.group(0)
                    objects = list(self._minio_client.list_objects(bucket_name=bucket_name))
                    files_found = len(objects)
                else:
                    # Fallback: use reasonable default based on path context
                    files_found = 4  # Increased default to match typical test scenarios
            except:
                files_found = 4  # Safe default
        else:
            # Regular path
            files_found = 5

        # Apply file type filter if specified
        if file_types:
            # Simulate filtering: If only .pdf and .csv selected from 4 files
            # Assume ~50% match (2 out of 4)
            files_found = max(2, files_found // 2)

        # Simulate status progression (for polling tests)
        initial_status = "running" if getattr(self, '_simulate_progression', False) else "completed"

        # Store job info
        self._ingestion_jobs[job_id] = {
            "status": initial_status,
            "files_processed": 0 if initial_status == "running" else files_found,
            "files_total": files_found,
            "customer_id": customer_id or "test",
            "mcp": mcp,
            "errors": []
        }

        # Simulate async completion for running jobs
        if initial_status == "running":
            import asyncio
            asyncio.create_task(self._complete_ingestion_job(job_id, files_found))

        return {
            "job_id": job_id,
            "files_processed": 0 if initial_status == "running" else files_found,
            "files_total": files_found,
            "status": initial_status,
            "customer_id": customer_id
        }

    async def _complete_ingestion_job(self, job_id: str, files_total: int):
        """Simulate job completion after delay (for status polling tests)"""
        await asyncio.sleep(1.5)
        if job_id in self._ingestion_jobs:
            self._ingestion_jobs[job_id]["status"] = "completed"
            self._ingestion_jobs[job_id]["files_processed"] = files_total

    def get_mcp(self, name: str):
        """
        Get MCP by name.

        Args:
            name: MCP name (ctax, law, tender)

        Returns:
            Mock MCP instance
        """
        from .mock_mcps import MockCTaxMCP, MockLawMCP, MockTenderMCP

        mcps = {
            "ctax": MockCTaxMCP(),
            "law": MockLawMCP(),
            "tender": MockTenderMCP()
        }

        return mcps.get(name)

    async def _ensure_initialized(self):
        """Mock initialization (no-op)"""
        pass

    def _ensure_initialized_sync(self):
        """Mock initialization (no-op)"""
        pass
