"""Structured logging for Apxoh.

Never log secrets. Never use print for library diagnostics.
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for machine consumption."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "arkhon_extra", None)
        if extra:
            payload["extra"] = extra
        return json.dumps(payload, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-8s %(name)s: %(message)s")


def configure_logging(level: str = "info", fmt: str = "text") -> None:
    """Configure the root logger."""
    normalized_level = level.upper()
    if not hasattr(logging, normalized_level):
        raise ValueError(f"unknown logging level: {level}")
    if fmt not in {"text", "json"}:
        raise ValueError(f"unknown logging format: {fmt}")

    root = logging.getLogger()
    root.setLevel(normalized_level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if fmt == "json" else TextFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return an Apxoh-scoped logger."""
    return logging.getLogger(f"arkhon.{name}")
