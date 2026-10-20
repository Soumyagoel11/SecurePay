"""Structured logging helpers (no sensitive data)."""

import logging


def get_logger(name="securepay"):
    return logging.getLogger(name)


def log_event(app_logger, event, **kwargs):
    """Log an event with a structured, non-sensitive payload.

    Passwords, JWT secrets and raw token values must NEVER be passed here.
    """
    safe = {k: v for k, v in kwargs.items() if k not in ("password", "token", "secret")}
    extra = " ".join(f"{k}={v}" for k, v in safe.items())
    app_logger.info(f"EVENT[{event}] {extra}")
