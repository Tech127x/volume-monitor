"""Logging configuration for Volume Monitor."""
import logging
import sys
from pathlib import Path

from .constants import LOG_FILE


def setup_logger(debug: bool = False) -> logging.Logger:
    """Configure and return the root logger."""
    root = logging.getLogger()
    
    # Avoid duplicate handlers
    if root.handlers:
        return root
    
    level = logging.DEBUG if debug else logging.INFO
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    fmt = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # File handler
    fh = logging.FileHandler(LOG_FILE, mode="a")
    fh.setFormatter(fmt)
    fh.setLevel(level)
    
    # Stream handler
    sh = logging.StreamHandler(sys.stderr if debug else sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(level)
    
    root.setLevel(level)
    root.addHandler(fh)
    root.addHandler(sh)
    
    return root


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)