"""
Delta Loader - Load processed documents to Delta Lake tables

Delta Lake provides ACID transactions, time travel, and schema evolution
for the structured data layer.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

logger = logging.getLogger(__name__)


class DeltaLoader:
    """
    Loads processed documents to Delta Lake tables.

    Creates MCP-specific tables with appropriate schemas.
    Supports incremental loading and schema evolution.
    """

    def __init__(self, delta_path: Path):
        """
        Args:
            delta_path: Path to Delta Lake storage
        """
        self.delta_path = Path(delta_path)
        self.delta_path.mkdir(parents=True, exist_ok=True)

    async def load_documents(self, mcp: str, documents: List[Dict[str, Any]]):
        """
        Load documents to MCP-specific Delta table.

        Args:
            mcp: MCP name (tax, legal, products, etc.)
            documents: List of processed documents
        """
        if not documents:
            logger.info(f"No documents to load for {mcp}")
            return

        table_path = self.delta_path / f"{mcp}_documents"

        logger.info(f"Loading {len(documents)} documents to {table_path}")

        # Convert to records for Delta
        records = []
        for doc in documents:
            records.append({
                "id": doc["id"],
                "path": doc["path"],
                "filename": doc["filename"],
                "mcp": doc["mcp"],
                "text": doc["text"],
                "chunk_count": len(doc.get("chunks", [])),
                "size_bytes": doc["metadata"]["size"],
                "modified_at": doc["metadata"]["modified"],
                "ingested_at": datetime.utcnow().isoformat(),
                "mime_type": doc["metadata"].get("mime_type", ""),
                "extension": doc["metadata"].get("extension", "")
            })

        # Define schema
        schema = pa.schema([
            ("id", pa.string()),
            ("path", pa.string()),
            ("filename", pa.string()),
            ("mcp", pa.string()),
            ("text", pa.large_string()),
            ("chunk_count", pa.int32()),
            ("size_bytes", pa.int64()),
            ("modified_at", pa.string()),
            ("ingested_at", pa.string()),
            ("mime_type", pa.string()),
            ("extension", pa.string()),
        ])

        # Create PyArrow table
        table = pa.Table.from_pylist(records, schema=schema)

        # Write to Delta
        write_deltalake(
            str(table_path),
            table,
            mode="append",
            schema_mode="merge"
        )

        logger.info(f"✓ Loaded {len(documents)} documents to {mcp}_documents")

        # Also load chunks separately for better query performance
        await self.load_chunks(mcp, documents)

    async def load_chunks(self, mcp: str, documents: List[Dict[str, Any]]):
        """
        Load document chunks to separate table for RAG.

        Args:
            mcp: MCP name
            documents: List of documents with chunks
        """
        table_path = self.delta_path / f"{mcp}_chunks"

        records = []
        for doc in documents:
            for i, chunk in enumerate(doc.get("chunks", [])):
                records.append({
                    "chunk_id": f"{doc['id']}_{i}",
                    "document_id": doc["id"],
                    "chunk_index": i,
                    "text": chunk,
                    "mcp": doc["mcp"],
                    "char_count": len(chunk),
                    "word_count": len(chunk.split())
                })

        if not records:
            return

        schema = pa.schema([
            ("chunk_id", pa.string()),
            ("document_id", pa.string()),
            ("chunk_index", pa.int32()),
            ("text", pa.large_string()),
            ("mcp", pa.string()),
            ("char_count", pa.int32()),
            ("word_count", pa.int32()),
        ])

        table = pa.Table.from_pylist(records, schema=schema)

        write_deltalake(
            str(table_path),
            table,
            mode="append",
            schema_mode="merge"
        )

        logger.info(f"✓ Loaded {len(records)} chunks to {mcp}_chunks")

    def query_documents(
        self,
        mcp: str,
        filter_expr: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> pa.Table:
        """
        Query documents from Delta table.

        Args:
            mcp: MCP name
            filter_expr: Optional filter expression (SQL-like)
            columns: Optional list of columns to return

        Returns:
            PyArrow table with results
        """
        table_path = self.delta_path / f"{mcp}_documents"

        if not table_path.exists():
            logger.warning(f"Table does not exist: {table_path}")
            return pa.Table.from_pydict({})

        dt = DeltaTable(str(table_path))

        # Convert to PyArrow table
        table = dt.to_pyarrow_table()

        # Apply filter if provided
        if filter_expr:
            import pyarrow.compute as pc
            # Simple filtering (can be enhanced)
            table = table.filter(pc.field(filter_expr))

        # Select columns if specified
        if columns:
            table = table.select(columns)

        return table

    def get_document_by_id(self, mcp: str, doc_id: str) -> Optional[Dict]:
        """
        Get a specific document by ID.

        Args:
            mcp: MCP name
            doc_id: Document ID

        Returns:
            Document dict or None if not found
        """
        table = self.query_documents(mcp)

        # Find matching document
        import pyarrow.compute as pc
        mask = pc.equal(table['id'], doc_id)
        filtered = table.filter(mask)

        if len(filtered) == 0:
            return None

        # Convert first row to dict
        return filtered.slice(0, 1).to_pylist()[0]

    def get_statistics(self, mcp: str) -> Dict[str, Any]:
        """
        Get statistics for an MCP table.

        Args:
            mcp: MCP name

        Returns:
            Dictionary with statistics
        """
        table_path = self.delta_path / f"{mcp}_documents"

        if not table_path.exists():
            return {"exists": False}

        dt = DeltaTable(str(table_path))
        table = dt.to_pyarrow_table()

        return {
            "exists": True,
            "num_documents": len(table),
            "num_files": dt.files(),
            "version": dt.version(),
            "size_bytes": sum(f["size_bytes"] for f in dt.file_uris()),
        }

    def list_mcps(self) -> List[str]:
        """
        List all MCP tables.

        Returns:
            List of MCP names
        """
        mcps = []

        for path in self.delta_path.iterdir():
            if path.is_dir() and path.name.endswith("_documents"):
                mcp_name = path.name.replace("_documents", "")
                mcps.append(mcp_name)

        return sorted(mcps)

    def vacuum(self, mcp: str, retention_hours: int = 168):
        """
        Vacuum old files from Delta table (cleanup).

        Args:
            mcp: MCP name
            retention_hours: Retention period in hours (default 7 days)
        """
        table_path = self.delta_path / f"{mcp}_documents"

        if not table_path.exists():
            return

        dt = DeltaTable(str(table_path))
        dt.vacuum(retention_hours=retention_hours, enforce_retention_duration=True)

        logger.info(f"Vacuumed {mcp}_documents (retention: {retention_hours}h)")
