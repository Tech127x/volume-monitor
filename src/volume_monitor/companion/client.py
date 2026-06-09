"""TCP client for BitFocus Companion API."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import contextlib
import logging
import socket
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class CompanionTCPClient:
    """TCP client for communicating with BitFocus Companion."""

    def __init__(self, host: str, port: int, device_id: str):
        self.host = host
        self.port = port
        self.device_id = device_id
        self.sock: Optional[socket.socket] = None
        self.lock = threading.Lock()
        self.connected = threading.Event()

    def connect(self, max_wait: float = 5.0) -> bool:
        """Connect to Companion with retry logic."""
        start = time.time()

        while not self.connected.is_set():
            if time.time() - start > max_wait:
                logger.warning(f"Connection timeout after {max_wait}s")
                return False

            try:
                with self.lock:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.settimeout(1.0)
                    self.sock.connect((self.host, self.port))
                    self.sock.settimeout(None)
                    self.connected.set()

                    # Register device
                    self._send(
                        f"ADD-DEVICE DEVICEID={self.device_id} "
                        f'PRODUCT_NAME="Python Volume Monitor"\n'
                    )

                    logger.info(f"Connected to Companion at {self.host}:{self.port}")
                return True

            except Exception as e:
                logger.warning(f"Connection failed: {e}. Retrying...")
                self.disconnect()
                time.sleep(1)

        return True

    def _send(self, cmd: str) -> bool:
        """Send raw command to Companion."""
        try:
            if self.sock and self.connected.is_set():
                self.sock.sendall(cmd.encode("utf-8"))
                return True
        except Exception:
            pass

        self.connected.clear()
        return False

    def send_command(self, cmd: str) -> bool:
        """Send a command, reconnecting if necessary."""
        if self.connected.is_set():
            return self._send(cmd)

        if self.connect():
            return self._send(cmd)

        return False

    def update_variable(self, name: str, value: str) -> bool:
        """Update a Companion custom variable."""
        return self.send_command(f"CUSTOM-VARIABLE {name} SET-VALUE {value}\n")

    def disconnect(self) -> None:
        """Disconnect from Companion."""
        if self.sock:
            with contextlib.suppress(Exception):
                self.sock.close()

        self.sock = None
        self.connected = threading.Event()
        logger.info("Disconnected from Companion")
