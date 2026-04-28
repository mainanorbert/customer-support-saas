"""Configure application logging.

Creates a logs directory and sets up root logging with:
- Rotating file handler for DEBUG+ messages.
- Console handler for INFO+ messages.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path


def setup_logging(*, log_dir: str | Path = "logs") -> logging.Logger:
    """Configure root logging once and return the root logger."""
    logger = logging.getLogger()
    if logger.handlers:
        return logger

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger