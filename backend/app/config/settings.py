"""Environment-driven application settings."""

from enum import StrEnum
from enum import Enum
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants.http import (
    HEADER_CORRELATION_ID,
    HEADER_PROCESS_TIME,
    HEADER_REQUEST_ID,
)
from app.core import metadata


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Typed configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = metadata.APP_NAME
    app_version: str = metadata.VERSION
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    api_v2_prefix: str = "/api/v2"

    database_url: str = (
        "postgresql+asyncpg://personaai:personaai_password@localhost:5432/personaai"
    )
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_connect_timeout_seconds: float = 2.0

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    cors_expose_headers: list[str] = Field(
        default_factory=lambda: [
            HEADER_CORRELATION_ID,
            HEADER_PROCESS_TIME,
            HEADER_REQUEST_ID,
        ]
    )

    log_level: LogLevel = LogLevel.INFO
    log_file: str = "logs/personaai.log"
    log_json: bool = True

    ollama_base_url: str = "http://localhost:11434"
    ollama_health_path: str = "/api/tags"
    health_check_timeout_seconds: float = 1.0

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> Any:
        """Support deployment-style debug values from host environments."""
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value in {"release", "production", "prod"}:
                return False
            if normalized_value in {"debug", "development", "dev"}:
                return True
        return value

    @field_validator(
        "cors_origins",
        "cors_allow_methods",
        "cors_allow_headers",
        "cors_expose_headers",
        mode="before",
    )
    @classmethod
    def parse_csv_list(cls, value: Any) -> Any:
        """Support comma-separated values from environment variables."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_development(self) -> bool:
        """Return whether the application is running in development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Return whether the application is running in testing."""
        return self.environment == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production."""
        return self.environment == Environment.PRODUCTION
