"""Application-wide constants and defaults."""
from pathlib import Path

# Version
VERSION = "1.1.0"

# File paths
CONFIG_FILE = Path.home() / ".volume_monitor_config.json"
LOG_FILE = Path.home() / "volume_monitor.log"
APP_VOLUME_CACHE_FILE = Path.home() / ".volume_monitor_app_volumes.json"

# Default configuration
DEFAULT_CONFIG = {
    "companion_ip": "127.0.0.1",
    "companion_port": 16759,
    "device_id": "python_volume_monitor",
    "volume_var": "volume_value",
    "mute_var": "volume_muted",
    "device_var": "current_device",
    "poll_interval": 0.03,
    "notify_on_switch": True,
    "notify_sound": "/usr/share/sounds/gnome/default/alerts/bark.ogg",
    "toggle_devices": [],
    "exclude_devices": [],
    "enable_app_knobs": False,
    "exclude_apps": [
        "plasmashell",
        "libcanberra",
        "wireplumber",
        "wpctl",
        "kwin_wayland",
        "xdg-desktop-portal",
        "chromium input",
        "pipewire",
    ],
    "app_knob_poll_interval": 0.1,
    # NEW: Safety features
    "default_new_app_volume": 50,  # Default volume for never-before-seen apps (0-100)
    "stream_dedup_window": 2.0,     # Seconds to wait before showing duplicate streams
    "enable_knob_compaction": True, # Move streams left when a knob frees up
}

# Browser ghost stream suppression (seconds)
# Ghost streams created by Brave/Chromium on YouTube last ~13 seconds
# Real playback streams persist indefinitely
BROWSER_STREAM_MIN_AGE = 10.0  # Minimum age before a browser stream is shown

# Stream Deck+ knob layout
KNOB_MASTER = 1
KNOB_APP_FIRST = 2
KNOB_APP_LAST = 4

# PipeWire target
DEFAULT_SINK_TARGET = "@DEFAULT_AUDIO_SINK@"

# Volume management
STREAM_VOLUME_RESTORE_HIGH = 95
STREAM_SLOT_GRACE_SEC = 0.5
STREAM_VOLUME_ENSURE_ATTEMPTS = 12
STREAM_BIND_REPUSH_COUNT = 8
STREAM_BIND_REPUSH_INTERVAL = 0.05

# NEW: Default volume for unknown apps
DEFAULT_NEW_APP_VOLUME = 50  # Safer than 100%

# NEW: Stream deduplication
STREAM_DEDUP_WINDOW = 2.0  # Seconds to suppress duplicate streams
STREAM_DEDUP_SIMILARITY_THRESHOLD = 0.9  # How similar names must be to dedupe

# Steam/game launcher binaries
STEAM_LAUNCHER_BINARIES = frozenset({
    "steam",
    "steam.exe",
    "reaper",
    "gamescope",
    "wine",
    "wine64",
    "wine64-preloader",
    "wineserver",
})

# Notification defaults
DEFAULT_NOTIFICATION_TIMEOUT = 3000

# Regex patterns
WPCTL_STREAM_LINE_RE = r"^\s+(\d+)\.\s+(.+?)\s*$"
INSPECT_PROP_RE = r"^\s*\*?\s*([\w.]+)\s*=\s*\"(.*)\"\s*$"
PACTL_SINK_INPUT_RE = r"^Sink Input #(\d+)"
PACTL_EVENT_NEW_INPUT = r"Event 'new' on sink-input #(\d+)"

# Browsers known to create multiple stream instances per tab
MULTI_INSTANCE_APPS = [
    "brave",
    "brave-browser",
    "chromium",
    "chrome",
    "google-chrome",
    "msedge",
    "opera",
    "vivaldi",
    "firefox",
    "firefox-esr",
]
