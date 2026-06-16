"""Desktop notification utilities."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def send_notification(title: str, body: str, icon_file: str = "") -> bool:
    """Send a desktop notification using notify-send."""
    try:
        cmd = ["notify-send", title, body]
        if icon_file and os.path.exists(icon_file):
            cmd += ["--icon", icon_file]

        _ = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as e:
        logger.debug(f"Notification failed: {e}")
        return False
