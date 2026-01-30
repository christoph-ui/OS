"""
LoRA Adapter Manager

Hot-swap LoRA adapters on vLLM server in <1 second.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import httpx

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class LoadedAdapter:
    """Represents a loaded LoRA adapter"""
    name: str
    path: str
    loaded_at: datetime
    request_count: int = 0
    last_used: Optional[datetime] = None


class LoRAManager:
    """
    Manages LoRA adapter loading/unloading on vLLM server.

    Provides <1 second hot-swapping between adapters.
    Uses vLLM's dynamic LoRA loading API.

    Usage:
        manager = LoRAManager("http://localhost:8000")
        await manager.load_adapter("ctax", "/adapters/ctax-lora")
        await manager.swap_adapter("ctax", "law")  # <1 sec
    """

    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url.rstrip("/")
        self.loaded_adapters: Dict[str, LoadedAdapter] = {}
        self.active_adapter: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=30.0)
        self._lock = asyncio.Lock()

    async def load_adapter(self, name: str, path: str) -> bool:
        """
        Load a LoRA adapter into vLLM.

        Args:
            name: Unique identifier for the adapter
            path: Path to adapter directory (contains adapter_model.safetensors)

        Returns:
            True if loaded successfully
        """
        async with self._lock:
            if name in self.loaded_adapters:
                logger.info(f"Adapter '{name}' already loaded")
                return True

            # Check adapter path exists
            adapter_path = Path(path)
            if not adapter_path.exists():
                logger.error(f"Adapter path not found: {path}")
                return False

            try:
                # vLLM LoRA loading API
                response = await self._client.post(
                    f"{self.vllm_url}/v1/load_lora_adapter",
                    json={
                        "lora_name": name,
                        "lora_path": str(adapter_path.absolute())
                    }
                )

                if response.status_code == 200:
                    self.loaded_adapters[name] = LoadedAdapter(
                        name=name,
                        path=str(adapter_path),
                        loaded_at=datetime.utcnow()
                    )
                    logger.info(f"Loaded adapter '{name}' from {path}")
                    return True
                else:
                    logger.error(f"Failed to load adapter: {response.text}")
                    return False

            except httpx.HTTPError as e:
                logger.error(f"HTTP error loading adapter: {e}")
                return False

    async def unload_adapter(self, name: str) -> bool:
        """
        Unload a LoRA adapter from vLLM.

        Args:
            name: Adapter identifier

        Returns:
            True if unloaded successfully
        """
        async with self._lock:
            if name not in self.loaded_adapters:
                logger.warning(f"Adapter '{name}' not loaded")
                return True

            try:
                response = await self._client.post(
                    f"{self.vllm_url}/v1/unload_lora_adapter",
                    json={"lora_name": name}
                )

                if response.status_code == 200:
                    del self.loaded_adapters[name]
                    if self.active_adapter == name:
                        self.active_adapter = None
                    logger.info(f"Unloaded adapter '{name}'")
                    return True
                else:
                    logger.error(f"Failed to unload adapter: {response.text}")
                    return False

            except httpx.HTTPError as e:
                logger.error(f"HTTP error unloading adapter: {e}")
                return False

    async def swap_adapter(self, to_adapter: str) -> bool:
        """
        Swap to a different LoRA adapter (<1 second).

        This is the core operation for MCP switching.
        vLLM keeps multiple LoRAs loaded and switches between them instantly.

        Args:
            to_adapter: Adapter to switch to

        Returns:
            True if swapped successfully
        """
        async with self._lock:
            if to_adapter not in self.loaded_adapters:
                logger.error(f"Adapter '{to_adapter}' not loaded. Load it first.")
                return False

            # Update tracking
            adapter = self.loaded_adapters[to_adapter]
            adapter.request_count += 1
            adapter.last_used = datetime.utcnow()
            self.active_adapter = to_adapter

            logger.debug(f"Swapped to adapter '{to_adapter}'")
            return True

    async def list_adapters(self) -> List[Dict]:
        """
        List all loaded adapters.

        Returns:
            List of adapter info dicts
        """
        return [
            {
                "name": adapter.name,
                "path": adapter.path,
                "loaded_at": adapter.loaded_at.isoformat(),
                "request_count": adapter.request_count,
                "last_used": adapter.last_used.isoformat() if adapter.last_used else None,
                "is_active": adapter.name == self.active_adapter
            }
            for adapter in self.loaded_adapters.values()
        ]

    async def get_active_adapter(self) -> Optional[str]:
        """Get the currently active adapter name"""
        return self.active_adapter

    async def ensure_adapter_loaded(self, name: str) -> bool:
        """
        Ensure an adapter is loaded, loading from config if needed.

        Args:
            name: Adapter name (must be in config.core_adapters)

        Returns:
            True if adapter is available
        """
        if name in self.loaded_adapters:
            return True

        # Check if it's a core adapter
        if name in config.core_adapters:
            adapter_config = config.core_adapters[name]
            adapter_path = config.adapter_path / adapter_config["path"]
            return await self.load_adapter(name, str(adapter_path))

        logger.error(f"Unknown adapter: {name}")
        return False

    async def load_core_adapters(self) -> int:
        """
        Pre-load all core adapters on startup.

        Returns:
            Number of adapters loaded
        """
        loaded = 0
        for name, adapter_config in config.core_adapters.items():
            adapter_path = config.adapter_path / adapter_config["path"]
            if adapter_path.exists():
                if await self.load_adapter(name, str(adapter_path)):
                    loaded += 1
            else:
                logger.warning(f"Core adapter path not found: {adapter_path}")

        logger.info(f"Loaded {loaded}/{len(config.core_adapters)} core adapters")
        return loaded

    async def health_check(self) -> Dict:
        """Check LoRA manager health"""
        try:
            response = await self._client.get(f"{self.vllm_url}/health")
            vllm_healthy = response.status_code == 200
        except:
            vllm_healthy = False

        return {
            "vllm_healthy": vllm_healthy,
            "loaded_adapters": len(self.loaded_adapters),
            "active_adapter": self.active_adapter,
            "adapters": list(self.loaded_adapters.keys())
        }

    async def close(self):
        """Cleanup resources"""
        await self._client.aclose()


# Singleton instance
_lora_manager: Optional[LoRAManager] = None


def get_lora_manager(vllm_url: str = None) -> LoRAManager:
    """Get or create the LoRA manager singleton"""
    global _lora_manager
    if _lora_manager is None:
        url = vllm_url or f"http://localhost:{config.vllm_port}"
        _lora_manager = LoRAManager(url)
    return _lora_manager
