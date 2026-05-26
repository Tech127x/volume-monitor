"""Configuration management with validation."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
import ipaddress

from .constants import CONFIG_FILE, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    """Validated configuration for Volume Monitor."""
    
    companion_ip: str = Field(
        default=DEFAULT_CONFIG["companion_ip"],
        description="Companion server IP address"
    )
    companion_port: int = Field(
        default=DEFAULT_CONFIG["companion_port"],
        ge=1024,
        le=65535,
        description="Companion TCP port"
    )
    device_id: str = Field(
        default=DEFAULT_CONFIG["device_id"],
        description="Device identifier for Companion"
    )
    volume_var: str = Field(
        default=DEFAULT_CONFIG["volume_var"],
        description="Companion variable name for volume"
    )
    mute_var: str = Field(
        default=DEFAULT_CONFIG["mute_var"],
        description="Companion variable name for mute state"
    )
    device_var: str = Field(
        default=DEFAULT_CONFIG["device_var"],
        description="Companion variable name for device name"
    )
    poll_interval: float = Field(
        default=DEFAULT_CONFIG["poll_interval"],
        ge=0.01,
        le=1.0,
        description="Polling interval in seconds"
    )
    notify_on_switch: bool = Field(
        default=DEFAULT_CONFIG["notify_on_switch"],
        description="Show desktop notification on device switch"
    )
    notify_sound: str = Field(
        default=DEFAULT_CONFIG["notify_sound"],
        description="Path to notification sound file"
    )
    toggle_devices: List[str] = Field(
        default_factory=list,
        description="Device patterns to include in toggle"
    )
    exclude_devices: List[str] = Field(
        default_factory=list,
        description="Device patterns to exclude from toggle"
    )
    enable_app_knobs: bool = Field(
        default=DEFAULT_CONFIG["enable_app_knobs"],
        description="Enable per-app volume knobs"
    )
    exclude_apps: List[str] = Field(
        default_factory=lambda: DEFAULT_CONFIG["exclude_apps"].copy(),
        description="App patterns to exclude from knobs"
    )
    app_knob_poll_interval: float = Field(
        default=DEFAULT_CONFIG["app_knob_poll_interval"],
        ge=0.05,
        le=1.0,
        description="App knob polling interval in seconds"
    )
    default_new_app_volume: int = Field(
        default=DEFAULT_CONFIG.get("default_new_app_volume", 50),
        ge=0,
        le=100,
        description="Default volume for never-before-seen apps (0-100)"
    )
    
    @field_validator("companion_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            # Allow hostnames too
            if v and not v.startswith(("-", ".")):
                return v
            raise ValueError(f"Invalid IP address or hostname: {v}")
    
    def save(self, path: Optional[Path] = None) -> bool:
        """Save configuration to file."""
        target = path or CONFIG_FILE
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.model_dump_json(indent=2))
            logger.info(f"Configuration saved to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "MonitorConfig":
        """Load configuration from file, falling back to defaults."""
        target = path or CONFIG_FILE
        if target.exists():
            try:
                data = json.loads(target.read_text())
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


def interactive_config_cli():
    """Entry point for interactive configuration."""
    from .cli_utils import interactive_configure
    interactive_configure()
