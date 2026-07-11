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

    jwt_secret_key: str = "supersecretkeyforpersonaaijwtgenerationandverificationtobeoverridden"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    credential_encryption_secret: str = (
        "change-me-in-production-credential-encryption-secret"
    )

    google_client_id: str = "246599226169-je0tu4he1h3ohj08rnml9eraak9f1hjp.apps.googleusercontent.com"
    google_client_secret: str = "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"
    google_redirect_uri: str = "http://localhost:8000/api/v1/connectors/gmail/callback"
    chrome_extension_redirect_url: str = "chrome-extension://ibbehiejdggjhmdbeafhdmbjidhgkkcf/callback.html"

    gmail_max_concurrent_requests: int = 10
    gmail_max_retries: int = 5
    gmail_initial_backoff_seconds: float = 1.0
    gmail_max_backoff_seconds: float = 30.0


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
    ollama_model: str = "llama3.2"
    ollama_health_path: str = "/api/tags"
    health_check_timeout_seconds: float = 1.0

    groq_api_key: str | None = None
    ai_provider: str = "groq"
    ai_model: str = "llama3-8b-8192"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> Any:
        """Support deployment-style debug values from host environments."""
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value in {
                "release",
                "production",
                "prod",
                "false",
                "0",
                "no",
                "off",
                "warn",
                "warning",
            }:
                return False
            if normalized_value in {
                "debug",
                "development",
                "dev",
                "true",
                "1",
                "yes",
                "on",
            }:
                return True
            return False
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
