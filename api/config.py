"""
Configuration management for 0711 Control Plane
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "0711 Control Plane"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_prefix: str = "/api"

    # Database
    database_url: str = "postgresql://0711:password@localhost:5432/0711_control"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days

    # Stripe
    stripe_secret_key: str
    stripe_public_key: str
    stripe_webhook_secret: str

    # Email
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from_email: str = "noreply@0711.io"
    smtp_from_name: str = "0711 Intelligence"

    # Frontend URLs
    website_url: str = "http://localhost:3000"
    admin_url: str = "http://localhost:3001"

    # Storage
    invoice_storage_path: str = "/var/0711/invoices"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:4000",
        "http://localhost:4020",
        "http://localhost:4010",
        "http://127.0.0.1:4000",
        "http://127.0.0.1:4020",
        "https://0711.io",
        "https://admin.0711.io"
    ]

    # Integration with Next.js Expert Network
    nextjs_url: str = "http://localhost:3000"
    webhook_secret: str = "change_this_in_production"
    fastapi_api_key: str = "change_this_in_production"

    # vLLM
    vllm_url: str = "http://localhost:8000"

    # MinIO
    minio_url: str = "http://localhost:9000"
    minio_access_key: str = "0711_admin"
    minio_secret_key: str = "0711_minio_password"

    # Anthropic Claude
    anthropic_api_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields from .env
    )


settings = Settings()
