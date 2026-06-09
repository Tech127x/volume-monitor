"""Configuration management with validation."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import ipaddress
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .constants import CONFIG_FILE, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    """Validated configuration for Volume Monitor."""

    companion_ip: str = Field(default="127.0.0.1", description="Companion server IP address")
    companion_port: int = Field(
        default=16759,
        ge=1024,
        le=65535,
        description="Companion TCP port",
    )
    device_id: str = Field(
        default="python_volume_monitor", description="Device identifier for Companion"
    )
    volume_var: str = Field(
        default="volume_value", description="Companion variable name for volume"
    )
    mute_var: str = Field(
        default="volume_muted", description="Companion variable name for mute state"
    )
    device_var: str = Field(
        default="current_device", description="Companion variable name for device name"
    )
    poll_interval: float = Field(
        default=0.03,
        ge=0.01,
        le=1.0,
        description="Polling interval in seconds",
    )
    notify_on_switch: bool = Field(
        default=True,
        description="Show desktop notification on device switch",
    )
    notify_sound: str = Field(
        default="/usr/share/sounds/gnome/default/alerts/bark.ogg",
        description="Path to notification icon file",
    )
    toggle_devices: list[str] = Field(
        default_factory=list, description="Device patterns to include in toggle"
    )
    exclude_devices: list[str] = Field(
        default_factory=list, description="Device patterns to exclude from toggle"
    )
    enable_app_knobs: bool = Field(default=False, description="Enable per-app volume knobs")
    exclude_apps: list[str] = Field(
        default_factory=lambda: [
            "plasmashell",
            "libcanberra",
            "wireplumber",
            "wpctl",
            "kwin_wayland",
            "xdg-desktop-portal",
            "chromium input",
            "pipewire",
        ],
        description="App patterns to exclude from knobs",
    )
    app_knob_poll_interval: float = Field(
        default=0.1,
        ge=0.05,
        le=1.0,
        description="App knob polling interval in seconds",
    )
    default_new_app_volume: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Default volume for never-before-seen apps (0-100)",
    )

    @field_validator("companion_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IP address format."""
        try:
            _ = ipaddress.ip_address(v)
            return v
        except ValueError:
            # Allow hostnames too
            if v and not v.startswith(("-", ".")):
                return v
            raise ValueError(f"Invalid IP address or hostname: {v}") from None

    def save(self, path: Path | None = None) -> bool:
        """Save configuration to file."""
        target = path or CONFIG_FILE
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _ = target.write_text(self.model_dump_json(indent=2))
            logger.info(f"Configuration saved to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @classmethod
    def load(cls, path: Path | None = None) -> "MonitorConfig":
        """Load configuration from file, falling back to defaults."""
        target = path or CONFIG_FILE
        if target.exists():
            try:
                data: dict[str, Any] = json.loads(target.read_text())
                # Merge with defaults for any missing keys
                merged = {**DEFAULT_CONFIG, **data}
                return cls(**merged)
            except Exception as e:
                logger.warning(f"Config load failed: {e}, using defaults")
        return cls()

    @classmethod
    def load_or_default(cls) -> "MonitorConfig":
        """Load config or return default instance."""
        return cls.load()
