"""
Embedder - Generate vector embeddings for text

Uses sentence-transformers for high-quality multilingual embeddings.
Optimized for German/English business documents.
"""

import asyncio
from typing import List, Optional
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Embedder:
    """
    Generate embeddings using sentence-transformers.

    Uses multilingual-e5-large model for German/English support.
    Handles batching and progress tracking.
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        device: str = "cuda",
        batch_size: int = 32
    ):
        """
        Args:
            model_name: HuggingFace model name
            device: 'cuda' or 'cpu'
            batch_size: Default batch size for encoding
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None
        self._dimension = None

    @property
    def model(self):
        """Lazy load model (only when needed)"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")

            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded. Embedding dimension: {self._dimension}")
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise

        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self._dimension is None:
            # Load model to get dimension
            _ = self.model
        return self._dimension

    async def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (numpy array)
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._embed_sync, text
        )

    def _embed_sync(self, text: str) -> np.ndarray:
        """Synchronous embedding (runs in thread pool)"""
        # Add prefix for E5 models (improves performance)
        if "e5" in self.model_name.lower():
            text = f"passage: {text}"

        return self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False
    ) -> List[np.ndarray]:
        """
        Embed a batch of texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses default if None)
            show_progress: Show progress bar

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        batch_size = batch_size or self.batch_size

        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._embed_batch_sync,
            texts,
            batch_size,
            show_progress
        )

    def _embed_batch_sync(
        self,
        texts: List[str],
        batch_size: int,
        show_progress: bool
    ) -> List[np.ndarray]:
        """Synchronous batch embedding"""
        # Add prefix for E5 models
        if "e5" in self.model_name.lower():
            texts = [f"passage: {t}" for t in texts]

        logger.info(f"Embedding {len(texts)} texts with batch size {batch_size}")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        # Convert to list of arrays
        return [emb for emb in embeddings]

    async def embed_documents(
        self,
        documents: List[dict],
        text_key: str = 'text',
        batch_size: Optional[int] = None,
        show_progress: bool = True
    ) -> List[dict]:
        """
        Embed documents and attach embeddings.

        Args:
            documents: List of document dicts
            text_key: Key containing text to embed
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Documents with 'embedding' key added
        """
        # Extract texts
        texts = [doc.get(text_key, '') for doc in documents]

        # Embed
        embeddings = await self.embed_batch(
            texts,
            batch_size=batch_size,
            show_progress=show_progress
        )

        # Attach embeddings to documents
        for doc, embedding in zip(documents, embeddings):
            doc['embedding'] = embedding

        return documents

    async def embed_chunks(
        self,
        chunks: List[dict],
        batch_size: Optional[int] = None,
        show_progress: bool = True
    ) -> List[dict]:
        """
        Embed chunks with their metadata.

        Args:
            chunks: List of chunk dicts with 'text' key
            batch_size: Batch size
            show_progress: Show progress

        Returns:
            Chunks with 'embedding' added
        """
        return await self.embed_documents(
            chunks,
            text_key='text',
            batch_size=batch_size,
            show_progress=show_progress
        )

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity (embeddings are already normalized)
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to a query.

        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to search
            top_k: Number of results to return

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if not embeddings:
            return []

        # Compute similarities
        similarities = [
            self.compute_similarity(query_embedding, emb)
            for emb in embeddings
        ]

        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [(int(idx), similarities[idx]) for idx in top_indices]

    async def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a search query.

        Uses 'query:' prefix for E5 models (different from documents).

        Args:
            query: Search query text

        Returns:
            Query embedding
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._embed_query_sync, query
        )

    def _embed_query_sync(self, query: str) -> np.ndarray:
        """Synchronous query embedding"""
        # Use 'query:' prefix for E5 models
        if "e5" in self.model_name.lower():
            query = f"query: {query}"

        return self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def save_embeddings(
        self,
        embeddings: List[np.ndarray],
        path: Path
    ):
        """
        Save embeddings to disk.

        Args:
            embeddings: List of embedding vectors
            path: Path to save file (.npy)
        """
        embeddings_array = np.array(embeddings)
        np.save(str(path), embeddings_array)
        logger.info(f"Saved {len(embeddings)} embeddings to {path}")

    def load_embeddings(self, path: Path) -> List[np.ndarray]:
        """
        Load embeddings from disk.

        Args:
            path: Path to .npy file

        Returns:
            List of embedding vectors
        """
        embeddings_array = np.load(str(path))
        logger.info(f"Loaded {len(embeddings_array)} embeddings from {path}")
        return [emb for emb in embeddings_array]

    def __repr__(self) -> str:
        return (
            f"Embedder(model={self.model_name}, "
            f"device={self.device}, "
            f"dimension={self.dimension if self._model else 'not loaded'})"
        )
