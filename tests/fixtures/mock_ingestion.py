"""
Mock Ingestion Orchestrator

Mock implementation that simulates file ingestion without actual processing.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio


class MockIngestionOrchestrator:
    """
    Mock ingestion orchestrator for testing.

    Simulates file processing without actually reading files or
    using Claude/embeddings/lakehouse.
    """

    def __init__(self, lakehouse_path: Path = None, vllm_url: str = None):
        """
        Initialize mock orchestrator.

        Args:
            lakehouse_path: Path to lakehouse (ignored in mock)
            vllm_url: vLLM URL (ignored in mock)
        """
        self.lakehouse_path = lakehouse_path
        self.vllm_url = vllm_url

    def ingest_folder(
        self,
        folder_path: Path,
        mcp_category: str = None,
        recursive: bool = True,
        file_types: List[str] = None,
        customer_id: str = None
    ) -> Dict[str, Any]:
        """
        Mock ingestion that returns fake statistics.

        Args:
            folder_path: Path to folder
            mcp_category: MCP to associate with
            recursive: Scan recursively
            file_types: File extensions to include
            customer_id: Customer ID for isolation

        Returns:
            Mock ingestion statistics
        """
        # Simulate finding files
        if "customer-" in str(folder_path):
            # MinIO bucket - simulate finding uploaded files
            files_found = 3
        else:
            # Regular path - simulate scanning
            files_found = 5

        # Filter by file types if specified
        if file_types:
            files_found = len(file_types)

        return {
            "files_processed": files_found,
            "files_total": files_found,
            "files_failed": 0,
            "chunks_created": files_found * 10,  # 10 chunks per file
            "embeddings_created": files_found * 10,
            "customer_id": customer_id or "test",
            "mcp_category": mcp_category,
            "status": "completed"
        }

    async def ingest_folder_async(
        self,
        folder_path: Path,
        mcp_category: str = None,
        recursive: bool = True,
        file_types: List[str] = None,
        customer_id: str = None,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Async version of ingest_folder.

        Simulates progress updates via callback.
        """
        files_found = 5 if file_types is None else len(file_types)

        # Simulate progress
        if progress_callback:
            for i in range(1, files_found + 1):
                await asyncio.sleep(0.05)  # Simulate processing time
                progress_callback({
                    "files_processed": i,
                    "files_total": files_found,
                    "status": "running"
                })

        # Final result
        result = {
            "files_processed": files_found,
            "files_total": files_found,
            "files_failed": 0,
            "chunks_created": files_found * 10,
            "embeddings_created": files_found * 10,
            "customer_id": customer_id or "test",
            "mcp_category": mcp_category,
            "status": "completed"
        }

        if progress_callback:
            progress_callback(result)

        return result
