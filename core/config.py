"""
Platform Configuration

Central configuration for the 0711 Platform.
"""

from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings


class PlatformConfig(BaseSettings):
    """
    Configuration for 0711 Platform.

    Can be set via environment variables with PLATFORM_ prefix.
    """

    # Deployment
    deployment_type: str = "managed"  # managed, self_hosted, or development

    # Paths (use CustomerPaths for customer-specific paths)
    lakehouse_path: Path = Path("/data/lakehouse")
    adapter_path: Path = Path("/data/adapters")
    upload_path: Path = Path("/data/uploads")

    # Model Serving
    vllm_url: str = "http://localhost:8001"
    embedding_url: str = "http://localhost:8002"
    model_orchestrator_url: str = "http://localhost:8003"

    # Model Configuration
    base_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    embedding_model: str = "intfloat/multilingual-e5-large"

    # Core MCPs
    core_mcps: List[str] = ["ctax", "law", "tender"]
    auto_load_core_mcps: bool = True

    # Ingestion
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 200

    # Performance
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 120

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "PLATFORM_",
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields from .env (fixes validation errors)
    }


# Global config instance
config = PlatformConfig()
