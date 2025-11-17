"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # OPA
    OPA_URL: str = "http://opa:8181"
    OPA_TIMEOUT: int = 5

    # Security
    ENROLLMENT_TOKEN_SECRET: str = "change-me-in-production"
    CERT_VALIDITY_DAYS: int = 90
    CA_CERT_VALIDITY_DAYS: int = 3650

    # Rate Limiting
    RATE_LIMIT_ENROLLMENTS: str = "5/minute"
    RATE_LIMIT_CONNECTIONS: str = "100/minute"
    RATE_LIMIT_HEALTH: str = "10/minute"

    # Health Check
    HEALTH_CHECK_MAX_AGE_MINUTES: int = 5

    # Observability
    LOG_LEVEL: str = "INFO"
    METRICS_PORT: int = 9090

    # API
    API_TITLE: str = "EdgeMesh Control Plane"
    API_VERSION: str = "1.0.0"
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()
