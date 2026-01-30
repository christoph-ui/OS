"""
Model Serving Orchestrator

Coordinates vLLM server, LoRA management, and embedding service.
Provides unified API for the 0711 platform.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from .config import config
from .lora_manager import LoRAManager, get_lora_manager

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateRequest(BaseModel):
    """Text generation request"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.95
    adapter: Optional[str] = None  # LoRA adapter name


class GenerateResponse(BaseModel):
    """Text generation response"""
    text: str
    model: str
    adapter: Optional[str]
    usage: Dict[str, int]


class EmbedRequest(BaseModel):
    """Embedding request"""
    texts: List[str]


class EmbedResponse(BaseModel):
    """Embedding response"""
    embeddings: List[List[float]]
    model: str
    dimension: int


class AdapterInfo(BaseModel):
    """LoRA adapter information"""
    name: str
    path: str
    loaded: bool
    is_active: bool
    request_count: int


# =============================================================================
# Model Serving API
# =============================================================================

class ModelServer:
    """
    Unified model serving interface.

    Wraps vLLM and embedding service into single API.
    Handles LoRA adapter management automatically.
    """

    def __init__(
        self,
        vllm_url: str = None,
        embedding_url: str = None
    ):
        self.vllm_url = vllm_url or f"http://localhost:{config.vllm_port}"
        self.embedding_url = embedding_url or f"http://localhost:{config.embedding_port}"
        self.lora_manager = get_lora_manager(self.vllm_url)
        self._client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        adapter: str = None,
        **kwargs
    ) -> GenerateResponse:
        """
        Generate text using Mixtral + optional LoRA adapter.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            adapter: LoRA adapter name (e.g., "ctax", "law", "tender")

        Returns:
            Generated text with metadata
        """
        # Swap to requested adapter if specified
        if adapter:
            loaded = await self.lora_manager.ensure_adapter_loaded(adapter)
            if not loaded:
                raise HTTPException(
                    status_code=400,
                    detail=f"Adapter '{adapter}' not available"
                )
            await self.lora_manager.swap_adapter(adapter)

        # Build vLLM request
        request_body = {
            "model": config.base_model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        # Add LoRA adapter if active
        active_adapter = await self.lora_manager.get_active_adapter()
        if active_adapter:
            request_body["lora_request"] = {
                "lora_name": active_adapter,
                "lora_int_id": 1  # vLLM internal ID
            }

        try:
            response = await self._client.post(
                f"{self.vllm_url}/v1/completions",
                json=request_body
            )
            response.raise_for_status()
            data = response.json()

            return GenerateResponse(
                text=data["choices"][0]["text"],
                model=config.base_model,
                adapter=active_adapter,
                usage={
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "total_tokens": data["usage"]["total_tokens"]
                }
            )

        except httpx.HTTPError as e:
            logger.error(f"vLLM error: {e}")
            raise HTTPException(status_code=502, detail=f"Model server error: {e}")

    async def embed(self, texts: List[str]) -> EmbedResponse:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = await self._client.post(
                f"{self.embedding_url}/v1/embeddings",
                json={"input": texts}
            )
            response.raise_for_status()
            data = response.json()

            embeddings = [item["embedding"] for item in data["data"]]

            return EmbedResponse(
                embeddings=embeddings,
                model=config.embedding_model,
                dimension=len(embeddings[0]) if embeddings else 1024
            )

        except httpx.HTTPError as e:
            logger.error(f"Embedding error: {e}")
            raise HTTPException(status_code=502, detail=f"Embedding server error: {e}")

    async def list_adapters(self) -> List[AdapterInfo]:
        """List all available LoRA adapters"""
        loaded = await self.lora_manager.list_adapters()
        active = await self.lora_manager.get_active_adapter()

        adapters = []
        for name, adapter_config in config.core_adapters.items():
            loaded_info = next((a for a in loaded if a["name"] == name), None)
            adapters.append(AdapterInfo(
                name=name,
                path=adapter_config["path"],
                loaded=loaded_info is not None,
                is_active=name == active,
                request_count=loaded_info["request_count"] if loaded_info else 0
            ))

        return adapters

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all model services"""
        vllm_healthy = False
        embedding_healthy = False

        try:
            r = await self._client.get(f"{self.vllm_url}/health")
            vllm_healthy = r.status_code == 200
        except:
            pass

        try:
            r = await self._client.get(f"{self.embedding_url}/health")
            embedding_healthy = r.status_code == 200
        except:
            pass

        lora_health = await self.lora_manager.health_check()

        return {
            "status": "healthy" if (vllm_healthy and embedding_healthy) else "degraded",
            "vllm": {
                "healthy": vllm_healthy,
                "url": self.vllm_url,
                "model": config.base_model
            },
            "embedding": {
                "healthy": embedding_healthy,
                "url": self.embedding_url,
                "model": config.embedding_model
            },
            "lora": lora_health
        }

    async def close(self):
        """Cleanup resources"""
        await self._client.aclose()
        await self.lora_manager.close()


# =============================================================================
# FastAPI Application
# =============================================================================

_model_server: Optional[ModelServer] = None


def get_model_server() -> ModelServer:
    """Get model server singleton"""
    global _model_server
    if _model_server is None:
        _model_server = ModelServer()
    return _model_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle"""
    server = get_model_server()

    # Pre-load core adapters
    logger.info("Pre-loading core LoRA adapters...")
    await server.lora_manager.load_core_adapters()

    yield

    # Cleanup
    await server.close()
    logger.info("Model server shut down")


app = FastAPI(
    title="0711 Model Serving",
    description="Unified API for Mixtral + LoRA + Embeddings",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text with optional LoRA adapter"""
    server = get_model_server()
    return await server.generate(
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        adapter=request.adapter
    )


@app.post("/v1/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Generate embeddings"""
    server = get_model_server()
    return await server.embed(request.texts)


@app.get("/v1/adapters", response_model=List[AdapterInfo])
async def list_adapters():
    """List available LoRA adapters"""
    server = get_model_server()
    return await server.list_adapters()


@app.post("/v1/adapters/{adapter_name}/load")
async def load_adapter(adapter_name: str):
    """Load a LoRA adapter"""
    server = get_model_server()
    success = await server.lora_manager.ensure_adapter_loaded(adapter_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to load adapter: {adapter_name}")
    return {"status": "loaded", "adapter": adapter_name}


@app.post("/v1/adapters/{adapter_name}/activate")
async def activate_adapter(adapter_name: str):
    """Activate a LoRA adapter (swap to it)"""
    server = get_model_server()
    success = await server.lora_manager.swap_adapter(adapter_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Adapter not loaded: {adapter_name}")
    return {"status": "active", "adapter": adapter_name}


@app.get("/health")
async def health_check():
    """Health check for all model services"""
    server = get_model_server()
    return await server.health_check()


def run_server(host: str = None, port: int = None):
    """Run the model orchestrator server"""
    import uvicorn

    host = host or config.vllm_host
    port = port or 8003  # Orchestrator runs on different port

    uvicorn.run(
        "inference.server:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
