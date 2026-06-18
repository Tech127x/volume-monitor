"""Volume monitor for default audio sink."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import logging
import time
from typing import Optional

from ..audio.pipewire import (
    clamp_volume_percent,
    get_default_sink_state,
)
from ..companion.client import CompanionTCPClient
from ..monitors.base import BaseMonitor
from ..utils.normalization import norm_device_name
from ..utils.notifications import send_notification
from ..utils.threading_utils import start_daemon_thread

logger = logging.getLogger(__name__)


class VolumeMonitor(BaseMonitor):
    """Monitors default sink volume and device changes."""

    def __init__(
        self,
        client: CompanionTCPClient,
        volume_var: str,
        mute_var: str,
        device_var: str,
        notify_enabled: bool = True,
        notify_sound: str = "",
        poll_interval: float = 0.03,
    ):
        super().__init__(client)
        self.volume_var = volume_var
        self.mute_var = mute_var
        self.device_var = device_var
        self.notify_enabled = notify_enabled
        self.notify_sound = notify_sound
        self.poll_interval = poll_interval

        # State tracking
        self._last_vol: int = -1
        self._last_muted: bool = False
        self._last_dev: str = ""
        self._last_t: float = 0.0

    def _norm_dev(self, dev: str) -> str:
        return norm_device_name(dev)

    def update_companion(
        self,
        vol: Optional[int],
        muted: bool,
        dev: Optional[str],
    ) -> None:
        if vol is None:
            return

        friendly = self._norm_dev(dev) if dev else "Unknown"

        with self._lock:
            now = time.time()
            if now - self._last_t < 0.02:
                return

            vol = clamp_volume_percent(vol)
            if vol is None:
                return

            if vol != self._last_vol:
                _ = self.client.update_variable(self.volume_var, str(vol))
                self._last_vol = vol

            if muted != self._last_muted:
                _ = self.client.update_variable(self.mute_var, "true" if muted else "false")
                self._last_muted = muted

            if self._last_dev != friendly:
                _ = self.client.update_variable(self.device_var, f'"{friendly}"')
                self._last_dev = friendly

                if self.notify_enabled and friendly != "Unknown":
                    _ = send_notification(
                        "🔊 Audio Output Switched",
                        f"Changed to: {friendly}",
                        self.notify_sound,
                    )

            self._last_t = now

    def push_initial_state(self) -> bool:
        try:
            dev, muted, vol = get_default_sink_state()
            if dev and vol is not None:
                self.update_companion(vol, muted, dev)
                return True
        except Exception as e:
            logger.error(f"Initial state push failed: {e}")
        return False

    def _poll_loop(self) -> None:
        last_dev = None
        last_muted = None
        last_vol = None

        while self._running.is_set():
            try:
                dev, muted, vol = get_default_sink_state()
                if (
                    dev
                    and vol is not None
                    and (dev != last_dev or vol != last_vol or muted != last_muted)
                ):
                    self.update_companion(vol, muted, dev)
                    last_dev = dev
                    last_muted = muted
                    last_vol = vol
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(self.poll_interval)

    def start(self) -> None:
        logger.info("Starting audio monitor (polling mode)...")
        self._running.set()
        _ = start_daemon_thread(self._poll_loop, "volume-poll")
        if not self.push_initial_state():
            logger.warning("Initial state read failed — continuing in degraded mode")

    def stop(self) -> None:
        super().stop()
        logger.info("Stopped VolumeMonitor")
