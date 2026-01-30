"""
0711 Model Serving Layer

Provides:
- Mixtral 8x7B base model (always loaded via vLLM)
- LoRA adapter hot-swapping (<1 second)
- Embedding model (multilingual-e5-large)

Architecture:
┌─────────────────────────────────────────────────────────────┐
│  MODEL SERVING (inference/)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  vLLM Server (:8000)                                │   │
│  │  - Mixtral 8x7B-Instruct (always loaded)            │   │
│  │  - LoRA adapters (hot-swappable)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Embedding Server (:8002)                           │   │
│  │  - multilingual-e5-large                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Model Orchestrator (:8003)                         │   │
│  │  - Unified API for generate/embed                   │   │
│  │  - LoRA management                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Usage:
    from inference import ModelServer, get_model_server

    server = get_model_server()

    # Generate with LoRA adapter
    response = await server.generate(
        prompt="What is the VAT rate?",
        adapter="ctax"  # Hot-swap to tax adapter
    )

    # Generate embeddings
    embeddings = await server.embed(["Hello", "World"])
"""

from .config import config, InferenceConfig
from .lora_manager import LoRAManager, get_lora_manager
from .embedding_server import EmbeddingService, get_embedding_service
from .server import ModelServer, get_model_server

__version__ = "1.0.0"

__all__ = [
    # Config
    "config",
    "InferenceConfig",
    # LoRA Management
    "LoRAManager",
    "get_lora_manager",
    # Embedding
    "EmbeddingService",
    "get_embedding_service",
    # Unified Server
    "ModelServer",
    "get_model_server",
]
