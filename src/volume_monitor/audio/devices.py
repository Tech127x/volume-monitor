"""Audio device management (listing, toggling, filtering)."""

import fnmatch
import logging
import re
import subprocess
from typing import Optional

from ..config import MonitorConfig
from ..utils.notifications import send_notification

logger = logging.getLogger(__name__)


def get_available_audio_devices() -> list[dict[str, str]]:
    """Get list of available audio output devices using wpctl."""
    devices = []

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
            elif (
                in_sinks_section
                and line
                and not line.startswith("   ")
                and "." in line
                and "[vol:" in line
            ):
                parts = line.split(".")
                if len(parts) >= 2:
                    sink_id_part = parts[0].strip()
                    rest = parts[1].strip()

                    # Extract numeric ID
                    match = re.search(r"\d+", sink_id_part)
                    if not match:
                        continue
                    sink_id = match.group()

                    # Extract device name
                    device_name = rest.split("[vol:")[0].strip()
                    device_name = re.sub(r"^\W+", "", device_name).strip()

                    if device_name:
                        devices.append({"id": sink_id, "name": device_name})

    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")

    return devices


def get_current_sink_id() -> Optional[str]:
    """Get the current default audio sink ID."""
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


def filter_devices(
    devices: list[dict[str, str]],
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
) -> list[dict[str, str]]:
    """Filter devices based on include/exclude pattern lists."""
    result = devices

    # Apply include filter
    if include_patterns:
        filtered = []
        for device in result:
            device_name = device["name"].lower()
            for pattern in include_patterns:
                if fnmatch.fnmatch(device_name, pattern.lower()):
                    filtered.append(device)
                    break
        result = filtered

    # Apply exclude filter
    if exclude_patterns:
        filtered = []
        for device in result:
            device_name = device["name"].lower()
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(device_name, pattern.lower()):
                    excluded = True
                    break
            if not excluded:
                filtered.append(device)
        result = filtered

    return result


def get_toggle_devices(config: Optional[MonitorConfig] = None) -> list[dict[str, str]]:
    """Get the list of devices for toggle, filtered by configuration."""
    if config is None:
        config = MonitorConfig.load_or_default()

    all_devices = get_available_audio_devices()
    include_patterns = config.toggle_devices
    exclude_patterns = config.exclude_devices

    if not include_patterns and not exclude_patterns:
        return all_devices

    filtered = filter_devices(all_devices, include_patterns, exclude_patterns)

    if not filtered:
        logger.warning("No devices match filter patterns, using all devices")
        return all_devices

    return filtered


def toggle_audio_device(config: Optional[MonitorConfig] = None) -> str | None:
    """Toggle to the next available audio output device.

    Returns:
        The name of the newly activated device on success, or None on failure.
    """
    devices = get_toggle_devices(config)

    if len(devices) < 2:
        logger.info("Need at least 2 audio devices to toggle")
        return None

    current_sink = get_current_sink_id()
    if not current_sink:
        logger.error("Could not determine current audio device")
        return None

    # Find current device index
    current_index = None
    for i, device in enumerate(devices):
        if device["id"] == current_sink:
            current_index = i
            break

    if current_index is None:
        logger.info(f"Current sink {current_sink} not in toggle list")
        current_index = -1

    # Calculate next device
    next_index = (current_index + 1) % len(devices)
    next_device = devices[next_index]

    try:
        _ = subprocess.run(
            ["wpctl", "set-default", next_device["id"]],
            check=True,
            timeout=5,
        )

        next_name = next_device["name"]
        logger.info(
            f"Toggled audio output: "
            f"{devices[current_index]['name'] if current_index >= 0 else 'Unknown'} -> {next_name}"
        )

        send_notification(
            "Audio Output Toggled",
            f"Switched to: {next_name}",
        )

        return next_name

    except Exception as e:
        logger.error(f"Failed to toggle audio device: {e}")
        return None
