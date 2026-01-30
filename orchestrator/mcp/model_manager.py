"""
Model Manager
Smart loading/unloading of models with LRU eviction
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import OrderedDict
import asyncio
import logging

from mcps.sdk.types import ModelSpec

logger = logging.getLogger(__name__)


@dataclass
class LoadedModel:
    """A model currently loaded in GPU memory"""
    spec: ModelSpec
    loaded_at: datetime
    last_used: datetime
    memory_gb: float
    request_count: int = 0
    vllm_model_id: Optional[str] = None


class ModelManager:
    """
    Manages model loading/unloading with smart GPU memory management

    Strategy:
    - Load models on-demand when MCPs need them
    - Keep frequently-used models in memory (hot models)
    - Evict least-recently-used models when memory is full (LRU)
    - Use LoRA for fast model swapping (~1-2 seconds vs ~10 seconds for full models)
    - Track usage patterns to pre-warm popular models

    Example:
        manager = ModelManager(
            vllm_url="http://localhost:8000",
            gpu_memory_gb=80.0,  # A100 80GB
            reserved_memory_gb=8.0  # Reserve for KV cache
        )

        # Ensure model is loaded
        await manager.ensure_loaded(model_spec)

        # Use model via vLLM
        response = await vllm_client.generate(...)
    """

    def __init__(
        self,
        vllm_url: str,
        gpu_memory_gb: float = 80.0,
        reserved_memory_gb: float = 8.0,
        enable_lru_eviction: bool = True
    ):
        """
        Initialize Model Manager

        Args:
            vllm_url: URL of vLLM server
            gpu_memory_gb: Total GPU memory available
            reserved_memory_gb: Memory to reserve for KV cache
            enable_lru_eviction: Enable automatic LRU eviction
        """
        self.vllm_url = vllm_url
        self.gpu_memory_gb = gpu_memory_gb
        self.reserved_memory_gb = reserved_memory_gb
        self.available_memory_gb = gpu_memory_gb - reserved_memory_gb
        self.enable_lru_eviction = enable_lru_eviction

        # Loaded models (OrderedDict for LRU)
        self.loaded_models: OrderedDict[str, LoadedModel] = OrderedDict()

        # Lock for thread-safe operations
        self._load_lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "models_loaded": 0,
            "models_evicted": 0,
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        logger.info(
            f"ModelManager initialized: {self.available_memory_gb}GB available "
            f"({gpu_memory_gb}GB total, {reserved_memory_gb}GB reserved)"
        )

    async def ensure_loaded(self, spec: ModelSpec) -> bool:
        """
        Ensure a model is loaded and ready

        Args:
            spec: Model specification

        Returns:
            True if model is loaded and ready

        Raises:
            MemoryError: If cannot free enough memory
        """
        async with self._load_lock:
            # Already loaded?
            if spec.name in self.loaded_models:
                model = self.loaded_models[spec.name]
                model.last_used = datetime.now(timezone.utc)
                model.request_count += 1

                # Move to end (most recently used)
                self.loaded_models.move_to_end(spec.name)

                self.stats["cache_hits"] += 1
                self.stats["total_requests"] += 1

                logger.debug(f"Model {spec.name} already loaded (cache hit)")
                return True

            # Not loaded - need to load
            self.stats["cache_misses"] += 1
            self.stats["total_requests"] += 1

            memory_needed = spec.memory_required_gb()
            logger.info(f"Loading model {spec.name} ({memory_needed:.1f}GB)")

            # Check if we have enough memory
            if not self._has_memory(memory_needed):
                if not self.enable_lru_eviction:
                    raise MemoryError(
                        f"Insufficient GPU memory for {spec.name} "
                        f"({memory_needed:.1f}GB needed, "
                        f"{self._available_memory():.1f}GB free)"
                    )

                # Evict LRU models until we have space
                evicted = await self._evict_until_space(memory_needed)
                logger.info(
                    f"Evicted {len(evicted)} models to load {spec.name}: "
                    f"{', '.join(evicted)}"
                )

            # Load the model
            success = await self._load_model(spec)

            if success:
                self.loaded_models[spec.name] = LoadedModel(
                    spec=spec,
                    loaded_at=datetime.now(timezone.utc),
                    last_used=datetime.now(timezone.utc),
                    memory_gb=memory_needed
                )
                self.stats["models_loaded"] += 1

                logger.info(
                    f"✓ Loaded {spec.name} "
                    f"({memory_needed:.1f}GB, "
                    f"{self._memory_used():.1f}/{self.available_memory_gb:.1f}GB used, "
                    f"{len(self.loaded_models)} models loaded)"
                )

            return success

    def _has_memory(self, required_gb: float) -> bool:
        """Check if we have enough GPU memory"""
        available = self._available_memory()
        return available >= required_gb

    def _available_memory(self) -> float:
        """Calculate available GPU memory"""
        used = self._memory_used()
        return self.available_memory_gb - used

    def _memory_used(self) -> float:
        """Total GPU memory used by loaded models"""
        return sum(m.memory_gb for m in self.loaded_models.values())

    async def _evict_until_space(self, required_gb: float) -> List[str]:
        """
        Evict LRU models until we have enough space

        Args:
            required_gb: Memory needed

        Returns:
            List of evicted model names

        Raises:
            MemoryError: If cannot free enough space
        """
        evicted = []

        while not self._has_memory(required_gb) and self.loaded_models:
            # Get least recently used (first in OrderedDict)
            lru_name = next(iter(self.loaded_models))
            lru_model = self.loaded_models[lru_name]

            # Unload
            await self._unload_model(lru_model.spec)
            del self.loaded_models[lru_name]

            evicted.append(lru_name)
            self.stats["models_evicted"] += 1

            logger.info(
                f"Evicted LRU model: {lru_name} "
                f"(loaded {lru_model.loaded_at.isoformat()}, "
                f"used {lru_model.request_count} times)"
            )

        # Check if we have enough space now
        if not self._has_memory(required_gb):
            raise MemoryError(
                f"Cannot free enough memory. "
                f"Need {required_gb:.1f}GB, have {self._available_memory():.1f}GB"
            )

        return evicted

    async def _load_model(self, spec: ModelSpec) -> bool:
        """
        Load a model into vLLM

        Args:
            spec: Model specification

        Returns:
            True if loaded successfully
        """
        try:
            if spec.lora_adapter:
                # Fast LoRA loading (~1-2 seconds)
                logger.info(f"Loading LoRA adapter: {spec.lora_adapter}")
                await self._load_lora(spec)
            else:
                # Full model loading (~5-10 seconds for 3-7B models)
                logger.info(f"Loading full model: {spec.name}")
                await self._load_full_model(spec)

            return True

        except Exception as e:
            logger.error(f"Failed to load {spec.name}: {e}", exc_info=True)
            return False

    async def _load_lora(self, spec: ModelSpec):
        """Load LoRA adapter (fast path)"""
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.vllm_url}/v1/lora/load",
                json={
                    "lora_name": spec.name,
                    "lora_path": spec.lora_adapter,
                    "base_model": spec.base_model
                }
            )
            response.raise_for_status()

            logger.debug(f"LoRA {spec.name} loaded successfully")

    async def _load_full_model(self, spec: ModelSpec):
        """Load full model (slower path)"""
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.vllm_url}/v1/models/load",
                json={
                    "model_name": spec.name,
                    "model_path": spec.file_path,
                    "quantization": spec.quantization,
                    "gpu_memory_utilization": 0.9,
                    "max_model_len": spec.context_length
                }
            )
            response.raise_for_status()

            logger.debug(f"Model {spec.name} loaded successfully")

    async def _unload_model(self, spec: ModelSpec):
        """Unload a model to free GPU memory"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.vllm_url}/v1/models/unload",
                    json={"model_name": spec.name}
                )

            logger.debug(f"Model {spec.name} unloaded")

        except Exception as e:
            logger.warning(f"Error unloading {spec.name}: {e}")

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.loaded_models.keys())

    def get_stats(self) -> Dict:
        """Get current memory and usage stats"""
        models_info = []
        for name, model in self.loaded_models.items():
            models_info.append({
                "name": name,
                "type": model.spec.type.value,
                "memory_gb": model.memory_gb,
                "requests": model.request_count,
                "loaded_at": model.loaded_at.isoformat(),
                "last_used": model.last_used.isoformat(),
                "is_lora": model.spec.lora_adapter is not None
            })

        return {
            "gpu_memory": {
                "total_gb": self.gpu_memory_gb,
                "available_gb": self.available_memory_gb,
                "used_gb": self._memory_used(),
                "free_gb": self._available_memory(),
                "utilization_pct": (self._memory_used() / self.available_memory_gb) * 100
            },
            "models": {
                "loaded": len(self.loaded_models),
                "details": models_info
            },
            "stats": self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0
                else 0.0
            )
        }

    async def preload_models(self, specs: List[ModelSpec]):
        """Pre-load a list of models (warm cache)"""
        logger.info(f"Pre-loading {len(specs)} models...")

        for spec in specs:
            try:
                await self.ensure_loaded(spec)
            except Exception as e:
                logger.warning(f"Failed to preload {spec.name}: {e}")

    async def shutdown(self):
        """Shutdown and cleanup"""
        logger.info("Shutting down ModelManager...")

        # Unload all models
        for spec in list(self.loaded_models.values()):
            await self._unload_model(spec.spec)

        self.loaded_models.clear()
        logger.info("ModelManager shutdown complete")
