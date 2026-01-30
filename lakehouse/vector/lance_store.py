"""
Lance Loader - Load embeddings to Lance vector database

Lance provides fast vector search with filtering capabilities.
Optimized for similarity search and hybrid search (vector + metadata).
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import numpy as np

import pyarrow as pa
import lancedb

logger = logging.getLogger(__name__)


class LanceLoader:
    """
    Loads embeddings to Lance vector database.

    Lance provides:
    - Fast approximate nearest neighbor (ANN) search
    - Filtering on metadata
    - Versioning and updates
    - Disk-based storage (doesn't require everything in RAM)
    """

    def __init__(self, lance_path: Path):
        """
        Args:
            lance_path: Path to Lance database storage
        """
        self.lance_path = Path(lance_path)
        self.lance_path.mkdir(parents=True, exist_ok=True)
        self._db = None

    @property
    def db(self):
        """Lazy load Lance database connection"""
        if self._db is None:
            self._db = lancedb.connect(str(self.lance_path))
            logger.info(f"Connected to Lance database at {self.lance_path}")
        return self._db

    async def load_embeddings(self, documents: List[Dict[str, Any]]):
        """
        Load chunk embeddings to Lance.

        Creates a unified index across all MCPs with MCP as filter field.

        Args:
            documents: List of processed documents with embeddings
        """
        if not documents:
            logger.info("No documents to load to Lance")
            return

        records = []
        embedding_dim = None

        for doc in documents:
            embeddings = doc.get("chunk_embeddings", [])
            chunks = doc.get("chunks", [])

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is None:
                    continue

                # Convert embedding to list if numpy array
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()

                # Detect embedding dimension
                if embedding_dim is None and len(embedding) > 0:
                    embedding_dim = len(embedding)
                    logger.info(f"📊 Detected embedding dimension: {embedding_dim}")

                records.append({
                    "chunk_id": f"{doc['id']}_{i}",
                    "document_id": doc["id"],
                    "filename": doc["filename"],
                    "mcp": doc["mcp"],
                    "text": chunk,
                    "vector": embedding,
                    "chunk_index": i,
                    "char_count": len(chunk)
                })

        if not records:
            logger.warning("No embeddings to load")
            return

        logger.info(f"💾 Loading {len(records)} embeddings to Lance (dim={embedding_dim})")

        # Create or open table
        table_name = "embeddings"

        try:
            # Try to open existing table
            table = self.db.open_table(table_name)
            # Add new records
            table.add(records)
            logger.info(f"✅ SAVED: Added {len(records)} embeddings to existing table '{table_name}'")
            logger.info(f"✅ Total rows in table: {table.count_rows()}")

        except Exception as e:
            # Create new table
            logger.info(f"Creating new table '{table_name}' with {len(records)} records...")
            table = self.db.create_table(table_name, data=records, mode="overwrite")
            logger.info(f"✅ SAVED: Created new table with {len(records)} embeddings")
            logger.info(f"✅ Table location: {self.lance_path}/{table_name}.lance")

        # Create index for fast search (if table is large enough)
        row_count = table.count_rows()
        if row_count >= 256:
            logger.info(f"🔍 Creating index for {row_count} embeddings...")
            await self.create_index(table_name, embedding_dim)
        else:
            logger.info(f"⏭️  Skipping index (only {row_count} rows, need 256+)")

        logger.info(f"✅ COMPLETE: Lakehouse saved at {self.lance_path}")

    async def create_index(self, table_name: str = "embeddings", embedding_dim: int = None):
        """
        Create vector index for fast search.

        Uses IVF-PQ (Inverted File Index with Product Quantization)
        for fast approximate nearest neighbor search.

        Args:
            table_name: Name of the table
            embedding_dim: Embedding dimension (auto-detected if None)
        """
        try:
            table = self.db.open_table(table_name)
            row_count = table.count_rows()

            # Auto-detect dimension if not provided
            if embedding_dim is None:
                first_row = table.to_pandas().head(1)
                if len(first_row) > 0:
                    embedding_dim = len(first_row.iloc[0]['vector'])
                else:
                    logger.warning("Cannot detect embedding dimension, skipping index")
                    return

            logger.info(f"🔍 Creating index for {table_name} ({row_count} rows, dim={embedding_dim})")

            # Create IVF-PQ index
            # num_partitions: sqrt(N) is a good heuristic
            num_partitions = max(int(np.sqrt(row_count)), 8)

            # Calculate num_sub_vectors that divides embedding_dim evenly
            # Common divisors for 1024: 128, 64, 32, 16, 8
            # Common divisors for 768: 96, 64, 48, 32, 16, 8
            if embedding_dim == 1024:
                num_sub_vectors = 128  # 1024 / 128 = 8
            elif embedding_dim == 768:
                num_sub_vectors = 96   # 768 / 96 = 8
            else:
                # Generic: find largest divisor <= 128
                num_sub_vectors = 16
                for candidate in [128, 64, 32, 16, 8]:
                    if embedding_dim % candidate == 0:
                        num_sub_vectors = candidate
                        break

            logger.info(f"📐 Index config: {num_partitions} partitions, {num_sub_vectors} sub_vectors")

            table.create_index(
                metric="cosine",
                num_partitions=num_partitions,
                num_sub_vectors=num_sub_vectors
            )

            logger.info(f"✅ INDEX CREATED: {num_partitions} partitions, {num_sub_vectors} sub_vectors")

        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            logger.info("⚠️  Index skipped - search will still work, just slower")

    def search(
        self,
        query_vector: List[float],
        mcp_filter: Optional[str] = None,
        top_k: int = 5,
        table_name: str = "embeddings"
    ) -> List[Dict]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding
            mcp_filter: Optional MCP to filter by
            top_k: Number of results to return
            table_name: Name of the table

        Returns:
            List of matching records with similarity scores
        """
        try:
            table = self.db.open_table(table_name)

            # Build query
            query = table.search(query_vector).limit(top_k)

            # Add MCP filter if specified
            if mcp_filter:
                query = query.where(f"mcp = '{mcp_filter}'")

            # Execute search
            results = query.to_list()

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_by_text(
        self,
        query_text: str,
        embedder,
        mcp_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search using text query (embeds query first).

        Args:
            query_text: Text query
            embedder: Embedder instance to use
            mcp_filter: Optional MCP filter
            top_k: Number of results

        Returns:
            List of matching records
        """
        # Embed query
        import asyncio
        query_vector = asyncio.run(embedder.embed_query(query_text))

        # Convert to list
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()

        # Search
        return self.search(query_vector, mcp_filter=mcp_filter, top_k=top_k)

    def get_by_document_id(
        self,
        document_id: str,
        table_name: str = "embeddings"
    ) -> List[Dict]:
        """
        Get all chunks for a specific document.

        Args:
            document_id: Document ID
            table_name: Table name

        Returns:
            List of chunks for the document
        """
        try:
            table = self.db.open_table(table_name)

            results = (
                table.search()
                .where(f"document_id = '{document_id}'")
                .to_list()
            )

            # Sort by chunk index
            results.sort(key=lambda x: x.get("chunk_index", 0))

            return results

        except Exception as e:
            logger.error(f"Failed to get chunks for document {document_id}: {e}")
            return []

    def get_statistics(self, table_name: str = "embeddings") -> Dict[str, Any]:
        """
        Get statistics about the Lance table.

        Args:
            table_name: Table name

        Returns:
            Dictionary with statistics
        """
        try:
            table = self.db.open_table(table_name)

            # Get row count
            row_count = table.count_rows()

            # Count by MCP
            # Note: Lance doesn't have built-in aggregation, so we query all
            all_records = table.to_pandas()

            mcp_counts = {}
            if not all_records.empty:
                mcp_counts = all_records['mcp'].value_counts().to_dict()

            return {
                "exists": True,
                "total_chunks": row_count,
                "by_mcp": mcp_counts,
                "has_index": table.list_indices() is not None
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"exists": False, "error": str(e)}

    def delete_by_document_id(
        self,
        document_id: str,
        table_name: str = "embeddings"
    ):
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete
            table_name: Table name
        """
        try:
            table = self.db.open_table(table_name)
            table.delete(f"document_id = '{document_id}'")
            logger.info(f"Deleted chunks for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")

    def delete_by_mcp(self, mcp: str, table_name: str = "embeddings"):
        """
        Delete all chunks for an MCP.

        Args:
            mcp: MCP name
            table_name: Table name
        """
        try:
            table = self.db.open_table(table_name)
            table.delete(f"mcp = '{mcp}'")
            logger.info(f"Deleted all chunks for MCP: {mcp}")

        except Exception as e:
            logger.error(f"Failed to delete MCP {mcp}: {e}")

    def compact(self, table_name: str = "embeddings"):
        """
        Compact the table (cleanup deleted rows).

        Args:
            table_name: Table name
        """
        try:
            table = self.db.open_table(table_name)
            table.compact_files()
            logger.info(f"Compacted table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to compact: {e}")
