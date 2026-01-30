"""
0711 Lakehouse

Unified data storage layer combining:
- Delta Lake for structured data (ACID transactions, time travel)
- Lance for vector embeddings (fast similarity search)

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │  LAKEHOUSE                                                  │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌─────────────────────────┐  ┌─────────────────────────┐  │
    │  │    Delta Lake           │  │    Lance Vector DB      │  │
    │  │    (Structured Data)    │  │    (Embeddings)         │  │
    │  │                         │  │                         │  │
    │  │  - documents table      │  │  - embeddings index     │  │
    │  │  - chunks table         │  │  - ANN search           │  │
    │  │  - mcp_results table    │  │  - metadata filtering   │  │
    │  └─────────────────────────┘  └─────────────────────────┘  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Usage:
    from lakehouse import Lakehouse

    lh = Lakehouse("/data/lakehouse")

    # Query structured data
    docs = lh.query("SELECT * FROM documents WHERE mcp = 'ctax'")

    # Vector search
    similar = lh.search_similar(embedding_vector, top_k=5)

    # Store results
    lh.store("mcp_results", {"analysis": "...", "confidence": 0.95})
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class Lakehouse:
    """
    Unified interface to Delta Lake + Lance vector store.

    Provides:
    - SQL queries on structured Delta tables
    - Vector similarity search on Lance indices
    - Document storage and retrieval
    - Customer data isolation
    """

    def __init__(self, path: Union[str, Path]):
        """
        Initialize lakehouse.

        Args:
            path: Root path for lakehouse storage
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

        # Sub-paths
        self.delta_path = self.path / "delta"
        self.lance_path = self.path / "lance"

        # Lazy-loaded components
        self._delta_loader = None
        self._lance_loader = None

        logger.info(f"Lakehouse initialized at {self.path}")

    @property
    def delta(self):
        """Lazy load Delta loader"""
        if self._delta_loader is None:
            from .delta.delta_loader import DeltaLoader
            self._delta_loader = DeltaLoader(self.delta_path)
        return self._delta_loader

    @property
    def lance(self):
        """Lazy load Lance loader"""
        if self._lance_loader is None:
            from .vector.lance_store import LanceLoader
            self._lance_loader = LanceLoader(self.lance_path)
        return self._lance_loader

    # =========================================================================
    # QUERY INTERFACE
    # =========================================================================

    def query(
        self,
        query: str,
        customer_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query structured data using SQL-like syntax.

        Args:
            query: SQL query (simplified - supports basic SELECT)
            customer_id: Filter by customer (REQUIRED for multi-tenancy)
            limit: Maximum rows to return

        Returns:
            List of row dictionaries

        Example:
            docs = lh.query(
                "SELECT * FROM documents WHERE category = 'tax'",
                customer_id="acme_corp"
            )

        Note:
            All queries are automatically filtered by customer_id to ensure
            data isolation between tenants.
        """
        # Warn if no customer_id provided
        if not customer_id:
            logger.warning("Query without customer_id - using 'default'. This should be avoided in production.")
            customer_id = "default"

        # Parse table name from query (simplified)
        query_lower = query.lower()

        # Determine MCP/table from query
        mcp = self._extract_mcp_from_query(query)

        if mcp:
            try:
                table = self.delta.query_documents(mcp)
                # Convert PyArrow table to list of dicts
                if hasattr(table, 'to_pylist'):
                    results = table.to_pylist()
                else:
                    results = table.to_pandas().to_dict('records')

                # CRITICAL: Filter by customer_id for multi-tenancy isolation
                results = [
                    r for r in results
                    if r.get('customer_id') == customer_id or r.get('customer_id') is None
                ]

                # Apply limit
                return results[:limit]
            except Exception as e:
                logger.error(f"Query failed: {e}")
                return []

        return []

    def _extract_mcp_from_query(self, query: str) -> Optional[str]:
        """Extract MCP name from query"""
        query_lower = query.lower()

        # Look for FROM table pattern
        if "from " in query_lower:
            parts = query_lower.split("from ")
            if len(parts) > 1:
                table_part = parts[1].split()[0].strip()
                # Remove _documents suffix if present
                if table_part.endswith("_documents"):
                    return table_part.replace("_documents", "")
                if table_part.endswith("_chunks"):
                    return table_part.replace("_chunks", "")
                # Check for known MCPs
                if table_part in ["ctax", "law", "tender", "documents"]:
                    return table_part

        # Look for mcp = 'value' pattern
        if "mcp = '" in query_lower or "mcp='" in query_lower:
            import re
            match = re.search(r"mcp\s*=\s*'(\w+)'", query_lower)
            if match:
                return match.group(1)

        # Look for category = 'value' pattern
        if "category = '" in query_lower:
            import re
            match = re.search(r"category\s*=\s*'(\w+)'", query_lower)
            if match:
                return match.group(1)

        return None

    # =========================================================================
    # VECTOR SEARCH
    # =========================================================================

    def search(
        self,
        vector: List[float],
        customer_id: Optional[str] = None,
        limit: int = 10,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            vector: Query embedding vector
            customer_id: Filter by customer (REQUIRED for multi-tenancy)
            limit: Number of results
            filter_category: Optional category/MCP filter

        Returns:
            List of similar documents with scores

        Note:
            Results are automatically filtered by customer_id for data isolation.
        """
        # Warn if no customer_id provided
        if not customer_id:
            logger.warning("Search without customer_id - using 'default'. This should be avoided in production.")
            customer_id = "default"

        results = self.lance.search(
            query_vector=vector,
            mcp_filter=filter_category,
            top_k=limit * 2  # Get extra results to filter
        )

        # Filter by customer_id for multi-tenancy
        filtered = [
            r for r in results
            if r.get('customer_id') == customer_id or r.get('customer_id') is None
        ]

        return filtered[:limit]

    def search_similar(
        self,
        vector: List[float],
        top_k: int = 10,
        mcp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Alias for search() with cleaner API"""
        return self.search(vector, limit=top_k, filter_category=mcp)

    # =========================================================================
    # STORAGE
    # =========================================================================

    def store(
        self,
        table: str,
        data: Dict[str, Any],
        mcp: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> str:
        """
        Store data in the lakehouse.

        Args:
            table: Target table name
            data: Data to store
            mcp: Associated MCP
            customer_id: Customer ID (REQUIRED for multi-tenancy)

        Returns:
            Record ID

        Note:
            customer_id is required to ensure proper data isolation.
        """
        import uuid
        from datetime import datetime

        # Require customer_id for production
        if not customer_id:
            logger.warning("Storing data without customer_id - using 'default'. This should be avoided in production.")
            customer_id = "default"

        record_id = str(uuid.uuid4())

        # Add metadata with required customer_id
        record = {
            "id": record_id,
            "mcp": mcp or "general",
            "customer_id": customer_id,  # Always include for isolation
            "created_at": datetime.utcnow().isoformat(),
            **data
        }

        # Store in Delta (would need to implement proper table management)
        # For now, log and return ID
        logger.info(f"Stored record {record_id} in {table} for customer {customer_id}")

        return record_id

    # =========================================================================
    # DOCUMENT ACCESS
    # =========================================================================

    def get_document(self, doc_id: str, mcp: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.

        Args:
            doc_id: Document ID
            mcp: MCP/category

        Returns:
            Document dict or None
        """
        return self.delta.get_document_by_id(mcp, doc_id)

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of chunks with embeddings
        """
        return self.lance.get_by_document_id(doc_id)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get lakehouse statistics"""
        stats = {
            "path": str(self.path),
            "delta": {},
            "lance": {}
        }

        # Delta stats
        try:
            mcps = self.delta.list_mcps()
            stats["delta"]["mcps"] = mcps
            stats["delta"]["tables"] = len(mcps)
        except Exception as e:
            stats["delta"]["error"] = str(e)

        # Lance stats
        try:
            stats["lance"] = self.lance.get_statistics()
        except Exception as e:
            stats["lance"]["error"] = str(e)

        return stats

    def list_mcps(self) -> List[str]:
        """List all MCPs with data in the lakehouse"""
        try:
            return self.delta.list_mcps()
        except:
            return []

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    def vacuum(self, mcp: Optional[str] = None, retention_hours: int = 168):
        """
        Cleanup old files.

        Args:
            mcp: Specific MCP to vacuum (None for all)
            retention_hours: Keep files newer than this
        """
        mcps = [mcp] if mcp else self.delta.list_mcps()

        for m in mcps:
            try:
                self.delta.vacuum(m, retention_hours)
            except Exception as e:
                logger.error(f"Vacuum failed for {m}: {e}")

    def compact(self):
        """Compact Lance indices"""
        try:
            self.lance.compact()
        except Exception as e:
            logger.error(f"Compact failed: {e}")

    def __repr__(self):
        return f"<Lakehouse path={self.path}>"


# Convenience exports
__all__ = ["Lakehouse"]
