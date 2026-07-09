"""Structured logging configuration shared across the application."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO", app_env: str = "production") -> None:
    """Configure structlog + stdlib logging.

    Renders human-readable, colorized output in `development`; renders
    machine-parseable JSON everywhere else (staging/production/CI), so log
    aggregators get structured fields without needing dev-only tooling.

    Idempotent: safe to call multiple times (e.g. once at API startup and
    once at CLI/script startup) without duplicating handlers.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,
    )

    renderer = (
        structlog.dev.ConsoleRenderer()
        if app_env == "development"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the given module/component name."""
    return structlog.get_logger(name)
