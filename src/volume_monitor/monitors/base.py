"""Base monitor class with common functionality."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import logging
import threading
from abc import ABC, abstractmethod

from ..companion.client import CompanionTCPClient

logger = logging.getLogger(__name__)


class BaseMonitor(ABC):
    """Abstract base class for monitors.

    Provides common threading primitives (running event, lock) and
    a default stop() implementation. Subclasses must implement
    start() and push_initial_state().
    """

    def __init__(self, client: CompanionTCPClient):
        self.client = client
        self._running = threading.Event()
        self._lock = threading.Lock()

    @abstractmethod
    def push_initial_state(self) -> bool:
        """Push initial state to Companion."""
        ...

    @abstractmethod
    def start(self) -> None:
        """Start the monitor."""
        ...

    def stop(self) -> None:
        """Stop the monitor."""
        self._running.clear()
        logger.info(f"Stopped {self.__class__.__name__}")
