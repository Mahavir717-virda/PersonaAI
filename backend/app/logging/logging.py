"""Structured logging configuration."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config.settings import Settings


class StructuredFormatter(logging.Formatter):
    """Format log records as JSON for machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a log record as a compact JSON object."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for attribute in (
            "correlation_id",
            "duration_ms",
            "request_id",
            "user_id",
        ):
            value = getattr(record, attribute, None)
            if value is not None:
                payload[attribute] = value
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure console and file logging for the application."""
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter_name = "structured" if settings.log_json else "standard"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {"()": StructuredFormatter},
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_name,
                    "level": settings.log_level.value,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": settings.log_file,
                    "formatter": formatter_name,
                    "level": settings.log_level.value,
                    "maxBytes": 10_485_760,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": settings.log_level.value,
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["console", "file"],
                    "level": settings.log_level.value,
                    "propagate": False,
                },
            },
        }
    )
