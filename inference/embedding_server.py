"""
Embedding Server

Serves multilingual-e5-large for vector embeddings.
Runs as a separate lightweight service alongside vLLM.
"""

import os
import logging
from typing import List, Union
from contextlib import asynccontextmanager

# IMPORTANT: Set CUDA_VISIBLE_DEVICES before importing torch!
if os.getenv("CUDA_VISIBLE_DEVICES") == "":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from .config import config

logger = logging.getLogger(__name__)


class EmbeddingRequest(BaseModel):
    """OpenAI-compatible embedding request"""
    input: Union[str, List[str]]
    model: str = "multilingual-e5-large"
    encoding_format: str = "float"


class EmbeddingData(BaseModel):
    """Single embedding result"""
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    """OpenAI-compatible embedding response"""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: dict


class EmbeddingService:
    """
    Embedding service using multilingual-e5-large.

    Optimized for German business documents.
    Supports batch processing for efficiency.
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.embedding_model
        self.device = device or config.embedding_device
        self.model: SentenceTransformer = None
        self.batch_size = config.embedding_batch_size

    def load_model(self):
        """Load the embedding model"""
        logger.info(f"Loading embedding model: {self.model_name}")

        self.model = SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=str(config.model_cache_path)
        )

        # Optimize for inference
        self.model.eval()
        if self.device == "cuda":
            self.model.half()  # FP16 for faster inference

        logger.info(f"Embedding model loaded on {self.device}")

    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Normalize input
        if isinstance(texts, str):
            texts = [texts]

        # Add e5 prefix for better performance
        # See: https://huggingface.co/intfloat/multilingual-e5-large
        prefixed_texts = [f"query: {text}" for text in texts]

        # Generate embeddings
        with torch.no_grad():
            embeddings = self.model.encode(
                prefixed_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization
            )

        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self.model is None:
            return 1024  # Default for multilingual-e5-large
        return self.model.get_sentence_embedding_dimension()


# Global service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup"""
    service = get_embedding_service()
    service.load_model()
    yield
    logger.info("Embedding server shutting down")


app = FastAPI(
    title="0711 Embedding Server",
    description="Multilingual embedding service for German business documents",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """
    Create embeddings (OpenAI-compatible API).

    Usage:
        POST /v1/embeddings
        {
            "input": "Wie hoch ist die Umsatzsteuer?",
            "model": "multilingual-e5-large"
        }
    """
    try:
        service = get_embedding_service()

        # Handle single string or list
        texts = request.input if isinstance(request.input, list) else [request.input]

        # Generate embeddings
        embeddings = service.embed(texts)

        # Format response
        data = [
            EmbeddingData(
                embedding=emb,
                index=i
            )
            for i, emb in enumerate(embeddings)
        ]

        # Calculate token usage (approximate)
        total_tokens = sum(len(t.split()) for t in texts)

        return EmbeddingResponse(
            data=data,
            model=request.model,
            usage={
                "prompt_tokens": total_tokens,
                "total_tokens": total_tokens
            }
        )

    except Exception as e:
        logger.error(f"Embedding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    service = get_embedding_service()
    return {
        "status": "healthy",
        "model": service.model_name,
        "device": service.device,
        "dimension": service.get_dimension(),
        "model_loaded": service.model is not None
    }


@app.get("/v1/models")
async def list_models():
    """List available embedding models"""
    service = get_embedding_service()
    return {
        "object": "list",
        "data": [
            {
                "id": service.model_name,
                "object": "model",
                "owned_by": "0711",
                "permission": []
            }
        ]
    }


def run_server(host: str = None, port: int = None):
    """Run the embedding server"""
    import uvicorn

    host = host or config.vllm_host
    port = port or config.embedding_port

    uvicorn.run(
        "inference.embedding_server:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
