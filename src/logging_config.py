"""Logging setup. All modules log; none use print() for status output.

Usage::

    from src.logging_config import get_logger, setup_logging

    setup_logging()  # once, at the CLI entry point
    logger = get_logger(__name__)
    logger.info("loaded %d rows", n)
"""

from __future__ import annotations

import logging

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger once. Safe to call repeatedly."""
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format=_DEFAULT_FORMAT, force=True)


def get_logger(name: str) -> logging.Logger:
    """Return a module logger (no handlers attached here)."""
    return logging.getLogger(name)
