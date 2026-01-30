"""
Model Serving Configuration

Central configuration for vLLM, LoRA adapters, and embedding model.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class InferenceConfig(BaseSettings):
    """Configuration for inference layer"""

    # Base Model (Mixtral 8x7B - always loaded)
    base_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.85
    max_model_len: int = 32768
    max_num_seqs: int = 256

    # LoRA Configuration
    enable_lora: bool = True
    max_loras: int = 4
    max_lora_rank: int = 64
    lora_extra_vocab_size: int = 256

    # Embedding Model
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_device: str = "cuda"
    embedding_batch_size: int = 32

    # Paths
    model_cache_path: Path = Path("/root/.cache/huggingface")
    adapter_path: Path = Path("/adapters")

    # Server Configuration
    vllm_host: str = "0.0.0.0"
    vllm_port: int = 8000
    embedding_port: int = 8000

    # Core LoRA Adapters (ship with platform)
    core_adapters: dict = {
        "ctax": {
            "name": "ctax-lora",
            "path": "adapters/ctax-lora",
            "description": "German tax specialist adapter"
        },
        "law": {
            "name": "law-lora",
            "path": "adapters/law-lora",
            "description": "Legal/contract analysis adapter"
        },
        "tender": {
            "name": "tender-lora",
            "path": "adapters/tender-lora",
            "description": "RFP/tender processing adapter"
        }
    }

    model_config = {
        "env_prefix": "INFERENCE_",
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields from .env
    }


# Global config instance
config = InferenceConfig()


# GPU Memory Layout (for 48GB GPU)
# ┌─────────────────────────────────────────────────┐
# │ Mixtral 8x7B base (always loaded)      ~30GB   │
# ├─────────────────────────────────────────────────┤
# │ Active LoRA (hot-swapped)              ~2GB    │
# ├─────────────────────────────────────────────────┤
# │ multilingual-e5-large                  ~2GB    │
# ├─────────────────────────────────────────────────┤
# │ Available for inference                ~14GB   │
# └─────────────────────────────────────────────────┘
