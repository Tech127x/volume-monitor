"""PipeWire/wpctl interaction functions."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import logging
import re
import subprocess
import time
from typing import Optional

from ..constants import DEFAULT_SINK_TARGET

logger = logging.getLogger(__name__)


def clamp_volume_percent(vol: int | float | None) -> Optional[int]:
    """Clamp volume to 0-100 range for Companion compatibility."""
    if vol is None:
        return None
    return max(0, min(100, int(round(vol))))


def volume_percent_from_wpctl_value(value: float) -> int:
    """Convert wpctl volume value (0.0-1.0+boost) to percentage."""
    pct = value * 100.0 if value <= 2.0 else value
    return clamp_volume_percent(pct) or 0


def parse_wpctl_volume_output(output: str) -> tuple[Optional[int], bool]:
    """Parse 'wpctl get-volume' output string."""
    output = output.strip()
    muted = "[MUTED]" in output
    parts = output.split()

    if len(parts) < 2:
        return None, muted

    raw = parts[1].rstrip("%")
    try:
        value = float(raw)
    except ValueError:
        return None, muted

    return volume_percent_from_wpctl_value(value), muted


def get_stream_volume(stream_id: str) -> tuple[Optional[int], bool]:
    """Get volume for a specific stream."""
    try:
        res = subprocess.run(
            ["wpctl", "get-volume", str(stream_id)],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )
        return parse_wpctl_volume_output(res.stdout)
    except Exception as e:
        logger.debug(f"Failed to get volume for stream {stream_id}: {e}")

    return None, False


def get_stream_volume_retry(
    stream_id: str, attempts: int = 5, delay: float = 0.04
) -> tuple[Optional[int], bool]:
    """Get stream volume with retries for newly created nodes."""
    vol: Optional[int] = None
    muted: bool = False

    for attempt in range(attempts):
        vol, muted = get_stream_volume(stream_id)
        if vol is not None:
            return vol, muted
        if attempt < attempts - 1:
            time.sleep(delay)

    return vol, muted


def set_stream_volume_percent(stream_id: str, percent: int) -> bool:
    """Set stream volume (capped at 100%)."""
    pct = clamp_volume_percent(percent)
    if pct is None:
        return False

    try:
        _ = subprocess.run(
            ["wpctl", "set-volume", str(stream_id), f"{pct}%", "-l", "1.0"],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )
        return True
    except Exception as e:
        logger.debug(f"wpctl set-volume {stream_id} {pct}% failed: {e}")
        return False


def ensure_stream_volume_percent(
    stream_id: str,
    percent: int,
    tolerance: int = 2,
    attempts: int = 12,
) -> int:
    """Set stream volume and verify it's applied."""
    target = clamp_volume_percent(percent) or 0

    for attempt in range(attempts):
        set_stream_volume_percent(stream_id, target)
        delay = 0.02 + attempt * 0.015
        time.sleep(delay)

        vol, _ = get_stream_volume(stream_id)
        if vol is not None and abs(vol - target) <= tolerance:
            return vol

    return target


def get_default_sink_state() -> tuple[Optional[str], bool, Optional[int]]:
    """Get description, muted state, and volume for the default sink."""
    device = None
    muted = False
    vol = None

    try:
        # Get device description
        res = subprocess.run(
            ["wpctl", "inspect", DEFAULT_SINK_TARGET],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )

        for line in res.stdout.splitlines():
            if "device.description" in line or "node.description" in line:
                if '"' in line:
                    device = line.split('"')[1]
                elif "=" in line:
                    device = line.split("=", 1)[1].strip()
                if device:
                    break

        # Get volume
        res = subprocess.run(
            ["wpctl", "get-volume", DEFAULT_SINK_TARGET],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )

        if res.returncode == 0:
            vol, muted = parse_wpctl_volume_output(res.stdout)

    except Exception as e:
        logger.error(f"Default sink state fetch error: {e}")

    return device, muted, vol


def get_current_sink_id() -> Optional[str]:
    """Get the numeric ID of the current default sink."""
    try:
        result = subprocess.run(
            ["wpctl", "status"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

        lines = result.stdout.split("\n")
        in_sinks_section = False

        for line in lines:
            line = line.strip()
            if "Sinks:" in line:
                in_sinks_section = True
                continue
            elif in_sinks_section and "Sources:" in line:
                break
            elif in_sinks_section and "*" in line and "[vol:" in line:
                clean_line = line.replace("*", "").strip()
                parts = clean_line.split(".")
                if len(parts) >= 1:
                    match = re.search(r"\d+", parts[0].strip())
                    if match:
                        return match.group()

        return None
    except Exception as e:
        logger.error(f"Error getting current sink: {e}")
        return None


def extract_numeric_id(text: str) -> Optional[str]:
    """Extract numeric ID from a string."""
    match = re.search(r"\d+", text)
    return match.group() if match else None
