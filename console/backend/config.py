"""
Console Backend Configuration
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class ConsoleConfig(BaseSettings):
    """Configuration for console backend"""

    # Server - Updated to port 4010
    host: str = "0.0.0.0"
    port: int = 4010
    debug: bool = True
    testing: bool = False  # Set to True for test mode with mocks

    # CORS - Updated for 40XX ports (will be loaded from env if set)
    cors_origins: List[str] = [
        "http://localhost:4020",
        "http://localhost:4010",
        "http://localhost:4000",
    ]

    # Platform - Updated for 40XX ports
    lakehouse_path: Path = Path("/home/christoph.bertsch/0711/data/lakehouse")
    vllm_url: str = "http://localhost:4030"
    embedding_url: str = "http://localhost:4040"

    # WebSocket
    ws_heartbeat_interval: int = 30

    # Logging
    log_level: str = "INFO"

    # AI APIs
    mistral_api_key: str = ""
    minio_url: str = "http://localhost:4050"
    minio_access_key: str = "0711admin"
    minio_secret_key: str = "0711secret"

    model_config = {
        "env_prefix": "CONSOLE_",
        "env_file": "console/backend/.env",
        "extra": "ignore"
    }


config = ConsoleConfig()
