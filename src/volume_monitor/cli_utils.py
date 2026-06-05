"""CLI utility functions for device listing, configuration, etc."""

import fnmatch
import logging
import sys
from collections.abc import Callable
from typing import cast

from .audio.devices import (
    get_available_audio_devices,
    get_current_sink_id,
    toggle_audio_device,
)
from .audio.pipewire import get_default_sink_state, get_stream_volume_retry
from .audio.streams import assign_knob_slots, get_wpctl_audio_streams
from .config import MonitorConfig
from .constants import (
    CONFIG_FILE,
    DEFAULT_SINK_TARGET,
    KNOB_APP_FIRST,
    KNOB_APP_LAST,
    KNOB_MASTER,
)
from .utils.normalization import norm_device_name


def _detect_companion_host() -> str:
    """Auto-detect Companion host, preferring a local or mDNS address."""
    import socket

    # Try localhost first (most common)
    try:
        socket.getaddrinfo("127.0.0.1", 16759)
        return "127.0.0.1"
    except OSError:
        pass

    # Try mDNS hostname (Companion advertises via Bonjour)
    for hostname in ["companion.local", "companion"]:
        try:
            socket.getaddrinfo(hostname, 16759)
            logger.info(f"Auto-detected Companion at {hostname}")
            return hostname
        except OSError:
            continue

    # Fall back to localhost
    return "127.0.0.1"


logger = logging.getLogger(__name__)


# ─── Helper Functions ────────────────────────────────────────────────


def _print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("─" * 55)
    print(f"  {title}")
    print("─" * 55)
    print()


def _confirm(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def _input_with_default(prompt: str, default: str) -> str:
    """Ask for input with a default value."""
    response = input(f"  {prompt} [{default}]: ").strip()
    return response if response else default


# ─── Companion Variable Helpers ───────────────────────────────────────


def _print_companion_setup_guide(enable_app_knobs: bool) -> None:
    """Print clear instructions for Companion variable setup."""
    _print_header("📋 BitFocus Companion Setup Guide")

    print("""
  To use Volume Monitor, you need to create these variables
  in BitFocus Companion. Open Companion in your browser,
  go to the "Variables" tab, and create each one listed below.

  ⚠️  All variables should be created as type: CUSTOM VARIABLE
""")

    # Master knob variables
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │  KNOB 1 — Master Volume (Default Audio Sink)    │")
    print("  ├─────────────────────────────────────────────────┤")
    print("  │  knob1_label        (displays device name)      │")
    print("  │  knob1_volume       (displays volume number)    │")
    print("  │  knob1_dial_pct     (drives the dial position)  │")
    print("  │  knob1_muted        (true/false mute state)     │")
    print("  │  knob1_stream_id    (internal ID — can hide)    │")
    print("  │  knob1_active       (true when device present)  │")
    print("  └─────────────────────────────────────────────────┘")

    if enable_app_knobs:
        print()
        print("  ┌─────────────────────────────────────────────────┐")
        print("  │  KNOBS 2–4 — Per-App Volume (Auto-Assigned)     │")
        print("  ├─────────────────────────────────────────────────┤")
        for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
            print(f"  │  knob{knob}_label        (displays app name)       │")
            print(f"  │  knob{knob}_volume       (displays volume number)  │")
            print(f"  │  knob{knob}_dial_pct     (drives the dial)         │")
            print(f"  │  knob{knob}_muted        (true/false mute state)   │")
            print(f"  │  knob{knob}_stream_id    (internal ID — can hide)  │")
            if knob < KNOB_APP_LAST:
                print("  │                                                   │")
        print("  └─────────────────────────────────────────────────┘")
        print()
        print("  💡 Apps are assigned automatically to the first")
        print("     available knob (2, then 3, then 4). When an app")
        print("     closes, the remaining apps shift left to fill")
        print("     the gap — keeping your most-used apps on the")
        print("     leftmost knobs.")

    print()
    print("  After creating the variables, map them to your")
    print("  Stream Deck+ knobs in Companion's Button layout.")
    print()

    if not _confirm(
        "Press Enter when you've set up these variables (or skip if already done)", default=True
    ):
        print("\n  You can set up Companion variables later.")
        print("  Run 'volume-monitor --configure' again to see this guide.")
    print()


# ─── Bluetooth Reminder ──────────────────────────────────────────────


def _bluetooth_reminder() -> None:
    """Remind user to connect bluetooth devices before scanning."""
    _print_header("🔵 Bluetooth Device Check")

    print("""
  Before we scan for audio devices, please make sure
  all your Bluetooth audio devices are:

    1. Powered ON
    2. Connected to your computer
    3. Working (you can hear audio through them)

  Take a moment now to connect any Bluetooth devices
  you want Volume Monitor to detect.
""")

    try:
        _ = input("\n  Press Enter when all devices are connected and ready...")
    except KeyboardInterrupt:
        print("\n\n  Configuration cancelled.")
        print("  Connect your devices and run 'volume-monitor --configure' again.")
        sys.exit(0)

    print("\n  ✓ Ready! Scanning for devices...\n")


# ─── Toggle Device Selection ─────────────────────────────────────────


def _configure_toggle_devices(config: MonitorConfig) -> None:
    """Simple, clear toggle device configuration."""
    _print_header("🔄 Audio Output Toggle Setup")

    print("""
  Volume Monitor can cycle through your audio devices
  when you run 'volume-monitor --toggle' or press a
  button mapped to toggle on your Stream Deck.

  For example: Headphones → Speakers → SPDIF
""")

    if not _confirm("Enable device toggling?", default=True):
        config.toggle_devices = []
        config.exclude_devices = []
        print("\n  ✓ Device toggling disabled.")
        return

    print()
    print("  How would you like to set up device toggling?")
    print()
    print("    [1] Use ALL devices (simple — just works)")
    print("    [2] Pick specific devices to include")
    print("    [3] Exclude specific devices (use all except...)")

    choice = input("\n  Choose an option [1]: ").strip() or "1"

    # Get devices (only when needed)
    devices = get_available_audio_devices()
    current_sink = get_current_sink_id()

    if not devices:
        print("\n  ⚠️  No audio devices detected.")
        return

    if choice == "1":
        config.toggle_devices = []
        config.exclude_devices = []
        print(f"\n  ✓ All {len(devices)} device(s) will be used for toggling.")

    elif choice == "2":
        # Show devices
        print(f"\n  Found {len(devices)} audio device(s):\n")
        for i, device in enumerate(devices, 1):
            marker = " ← CURRENT" if device["id"] == current_sink else ""
            print(f"    {i}. {device['name']}{marker}")

        print("\n  Enter the numbers of devices to INCLUDE")
        print("  (comma-separated, e.g.: 1,3)\n")
        selected = input("  Include devices: ").strip()

        if selected:
            patterns: list[str] = []
            for item in selected.split(","):
                item = item.strip()
                if item.isdigit():
                    idx = int(item) - 1
                    if 0 <= idx < len(devices):
                        name = devices[idx]["name"]
                        patterns.append(f"{name.split()[0]}*")
                        print(f"    ✓ {devices[idx]['name']}")

            if patterns:
                config.toggle_devices = patterns
                config.exclude_devices = []
                print(f"\n  ✓ {len(patterns)} device(s) included in toggle cycle.")
            else:
                print("\n  ⚠️  No valid devices selected. Using all devices.")
                config.toggle_devices = []
                config.exclude_devices = []

    elif choice == "3":
        # Show devices
        print(f"\n  Found {len(devices)} audio device(s):\n")
        for i, device in enumerate(devices, 1):
            marker = " ← CURRENT" if device["id"] == current_sink else ""
            print(f"    {i}. {device['name']}{marker}")

        print("\n  Enter the numbers of devices to EXCLUDE")
        print("  (comma-separated, e.g.: 2)\n")
        selected = input("  Exclude devices: ").strip()

        if selected:
            patterns = []
            for item in selected.split(","):
                item = item.strip()
                if item.isdigit():
                    idx = int(item) - 1
                    if 0 <= idx < len(devices):
                        name = devices[idx]["name"]
                        patterns.append(f"{name.split()[0]}*")
                        print(f"    ✗ {devices[idx]['name']}")

            if patterns:
                config.toggle_devices = []
                config.exclude_devices = patterns
                remaining = len(devices) - len(patterns)
                print(
                    f"\n  ✓ {len(patterns)} device(s) excluded. {remaining} device(s) remain in toggle cycle."
                )
            else:
                print("\n  ⚠️  No valid devices selected. Using all devices.")
                config.toggle_devices = []
                config.exclude_devices = []


# ─── App Knob Configuration ──────────────────────────────────────────


def _configure_app_knobs(config: MonitorConfig) -> None:
    """Configure per-app volume knobs with clear Companion setup instructions."""
    _print_header("🎛️  Per-App Volume Knobs (Stream Deck+)")

    print("""
  Volume Monitor can assign each open audio application
  to its own knob on your Stream Deck+ (knobs 2, 3, and 4).

  For example:
    Knob 2 → Brave: YouTube
    Knob 3 → Spotify
    Knob 4 → Discord

  Each app's volume is remembered — when you close and
  reopen an app, it returns to its previous level.

  New apps start at 50% volume (configurable) so you
  never get blasted by 100% volume unexpectedly.
""")

    if not _confirm("Enable per-app volume knobs?", default=True):
        config.enable_app_knobs = False
        print("\n  ✓ Per-app knobs disabled. Only master volume (knob 1) will be used.")
        return

    config.enable_app_knobs = True

    # Default volume for new apps
    print()
    print("  When a brand-new app is detected (never seen before),")
    print("  what volume should it start at?")
    print()
    print("    50% — Safe default (recommended for headphones)")
    print("    75% — Moderate")
    print("   100% — Full volume (original behavior)")
    print()

    vol_choice = input("  Default volume for new apps [50]: ").strip()
    if vol_choice.isdigit():
        config.default_new_app_volume = max(0, min(100, int(vol_choice)))
    else:
        config.default_new_app_volume = 50

    print(f"\n  ✓ New apps will start at {config.default_new_app_volume}% volume.")

    # Excluded apps
    print()
    print("  Some system apps create audio streams you probably")
    print("  don't want on your Stream Deck (notification sounds,")
    print("  system beeps, etc.).")
    print()
    print("  Currently excluded:")
    for app in config.exclude_apps:
        print(f"    • {app}")

    if _confirm("\n  Edit the exclusion list?", default=False):
        print("\n  Enter app names to exclude (one per line, empty to finish):")
        new_excludes: list[str] = []
        while True:
            app = input("    > ").strip()
            if not app:
                break
            new_excludes.append(app)

        if new_excludes:
            config.exclude_apps = new_excludes
            print(f"\n  ✓ {len(new_excludes)} app(s) excluded.")

    # Show Companion variables needed
    print()
    if _confirm("Show Companion variable setup guide for app knobs?", default=True):
        _print_companion_setup_guide(enable_app_knobs=True)


# ─── Main Configuration Wizard ───────────────────────────────────────


def interactive_configure(start_callback: Callable[[MonitorConfig], None] | None = None):
    """Interactive configuration wizard with clear, simple flow.

    Args:
        start_callback: Optional callable accepting a MonitorConfig to start
                        the monitor. When None, instructions are printed instead.
    """
    config = MonitorConfig.load_or_default()

    print()
    print("╔═══════════════════════════════════════════════════╗")
    print("║     🎛️  Volume Monitor Configuration Wizard       ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    print("  This wizard will guide you through setting up")
    print("  Volume Monitor for your system.")
    print()
    print("  You can run this anytime to change settings.")
    print("  All settings are saved to ~/.volume_monitor_config.json")

    # Step 1: Bluetooth reminder
    _bluetooth_reminder()

    # Step 2: Companion connection
    _print_header("🔌 Companion Connection")

    current_ip = config.companion_ip
    current_port = config.companion_port

    # Auto-detect Companion on the network
    detected = _detect_companion_host()
    if detected != current_ip:
        print(f"  ℹ️  Auto-detected Companion at {detected}")
        if _confirm(f"Use {detected} instead of {current_ip}?", default=True):
            current_ip = detected
            config.companion_ip = detected

    print("  Volume Monitor connects to BitFocus Companion")
    print("  to send volume data to your Stream Deck.")
    print()
    print("  Current settings:")
    print(f"    IP Address: {current_ip}")
    print(f"    TCP Port:   {current_port}")
    print()

    if _confirm("Change connection settings?", default=False):
        new_ip = _input_with_default("Companion IP address", current_ip)
        config.companion_ip = new_ip

        port_input = input(f"  Companion TCP Port [{current_port}]: ").strip()
        if port_input.isdigit():
            config.companion_port = int(port_input)
        else:
            config.companion_port = current_port

        print(f"\n  ✓ Connecting to {config.companion_ip}:{config.companion_port}")

    # Step 3: Variable names (simplified - most users don't need to change)
    _print_header("📝 Companion Variable Names")
    print("  Volume Monitor uses these variable names in Companion.")
    print("  Most users can keep the defaults.\n")
    print(f"    Volume variable:  {config.volume_var}")
    print(f"    Mute variable:    {config.mute_var}")
    print(f"    Device variable:  {config.device_var}")

    if _confirm("\n  Change variable names?", default=False):
        config.volume_var = _input_with_default("Volume variable name", config.volume_var)
        config.mute_var = _input_with_default("Mute variable name", config.mute_var)
        config.device_var = _input_with_default("Device variable name", config.device_var)

    # Step 4: Notifications
    _print_header("🔔 Notifications")

    notify_current = "ON" if config.notify_on_switch else "OFF"
    print("  Volume Monitor can show a desktop notification")
    print("  when the audio output device changes.")
    print(f"\n  Currently: {notify_current}")

    if _confirm("Show notifications on device switch?", default=config.notify_on_switch):
        config.notify_on_switch = True
        print("  ✓ Notifications enabled.")
    else:
        config.notify_on_switch = False
        print("  ✓ Notifications disabled.")

    # Step 5: Toggle devices
    _configure_toggle_devices(config)

    # Step 6: App knobs
    _configure_app_knobs(config)

    # Step 7: Companion setup guide (if app knobs disabled, still show master knob)
    if not config.enable_app_knobs and _confirm(
        "\n  Show Companion variable setup guide for master volume?", default=True
    ):
        _print_companion_setup_guide(enable_app_knobs=False)

    # Step 8: Save
    _print_header("💾 Save Configuration")

    if config.save():
        print("  ✓ Configuration saved successfully!")
        print(f"    File: {CONFIG_FILE}")
    else:
        print("  ✗ Failed to save configuration.")
        return

    # Summary
    _print_header("📋 Configuration Summary")
    print(f"  Companion:    {config.companion_ip}:{config.companion_port}")
    print(f"  Notifications: {'ON' if config.notify_on_switch else 'OFF'}")
    print(
        f"  Toggle devices: {len(config.toggle_devices) if config.toggle_devices else 'All'} included"
        + f"{', ' + str(len(config.exclude_devices)) + ' excluded' if config.exclude_devices else ''}"
    )
    print(f"  Per-app knobs: {'ON' if config.enable_app_knobs else 'OFF'}")
    if config.enable_app_knobs:
        print(f"  New app volume: {config.default_new_app_volume}%")
        print("  Knob compaction: ON (apps shift left)")
    print()
    print("  Run 'volume-monitor --start' to begin monitoring.")
    print("  Run 'volume-monitor --configure' to change settings.")
    print()

    # Ask about starting/restarting
    if start_callback is not None:
        if _confirm("Volume Monitor is running. Restart to apply new settings?", default=True):
            print("\n  Restarting Volume Monitor...")
            start_callback(config)
            print("  ✓ Restarted with new settings.")
        else:
            print("\n  Settings saved. Changes will apply on next restart.")
            print("  Restart with: volume-monitor --restart")
    else:
        if _confirm("Start Volume Monitor now?", default=True):
            print("\n  Starting Volume Monitor...")
            print("  Start manually with: volume-monitor --start")
        else:
            print("\n  Start manually with: volume-monitor --start")


# ─── Other utility functions ─────────────────────────────────────────


def list_devices_command():
    """List all available audio devices with their IDs."""
    devices = get_available_audio_devices()
    config = MonitorConfig.load_or_default()
    current_sink = get_current_sink_id()

    print("\nAvailable Audio Output Devices:")
    print("=" * 50)

    for i, device in enumerate(devices):
        current_marker = " (CURRENT)" if device["id"] == current_sink else ""

        is_included = True
        if config.toggle_devices:
            is_included = any(
                fnmatch.fnmatch(device["name"].lower(), pattern.lower())
                for pattern in config.toggle_devices
            )
        if is_included and config.exclude_devices:
            is_excluded = any(
                fnmatch.fnmatch(device["name"].lower(), pattern.lower())
                for pattern in config.exclude_devices
            )
            if is_excluded:
                is_included = False

        filtered_marker = " ✓" if is_included else " ✗"

        print(f"{i + 1:2d}. {device['id']:3s} - {device['name']}{current_marker}{filtered_marker}")

    if config.toggle_devices or config.exclude_devices:
        print(f"\nInclude patterns: {config.toggle_devices or 'None (all)'}")
        print(f"Exclude patterns: {config.exclude_devices or 'None'}")
        print("✓ = Included in toggle, ✗ = Excluded from toggle")
    else:
        print("\nNo filters configured - using all devices")

    print()


def list_streams_command():
    """List open per-app audio streams."""
    config = MonitorConfig.load_or_default()
    exclude = config.exclude_apps
    streams = get_wpctl_audio_streams(exclude)

    device, muted, vol = get_default_sink_state()
    label = norm_device_name(device)
    mute_str = " [MUTED]" if muted else ""
    vol_str = f" ({vol}%)" if vol is not None else ""
    sink_id = get_current_sink_id() or DEFAULT_SINK_TARGET

    print("\nKnob assignments (Stream Deck +)")
    print("=" * 60)
    print(f"  Knob {KNOB_MASTER} (master): {label}{mute_str}{vol_str}")
    print(f"        wpctl target: {sink_id}")
    print(f"\n  Knobs {KNOB_APP_FIRST}-{KNOB_APP_LAST} (apps, auto-assigned):")

    if not streams:
        print("    (no app streams open)")
        app_slots = {}
    else:
        app_slots = assign_knob_slots(streams, {})
        for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
            s = app_slots.get(knob)
            if s is None:
                print(f"    Knob {knob}: (empty)")
                continue

            stream_id = str(s.get("id", ""))
            if s.get("volume") is None:
                vol_result, muted_result = get_stream_volume_retry(stream_id)
                s["volume"] = vol_result
                s["muted"] = muted_result

            mute_str = " [MUTED]" if s.get("muted") else ""
            vol_val = s.get("volume")
            vol_str = f" ({vol_val}%)" if vol_val is not None else ""
            disp_name = str(s.get("display_name", ""))
            print(f"    Knob {knob}: {disp_name}{mute_str}{vol_str}  [stream {stream_id}]")

            props = s.get("props")
            if isinstance(props, dict):
                media = cast("dict[str, object]", props).get("media.name")
                if media:
                    print(f"              media: {str(media)[:60]}")

        assigned_keys: set[str] = set()
        for i in app_slots:
            slot_stream = app_slots.get(i)
            if slot_stream is not None:
                key = slot_stream.get("dedupe_key")
                if key is not None:
                    assigned_keys.add(str(key))
        unassigned = [s for s in streams if str(s.get("dedupe_key", "")) not in assigned_keys]
        if unassigned:
            print("\n  Waiting for a free knob:")
            for s in unassigned:
                disp_name = str(s.get("display_name", ""))
                stream_id = str(s.get("id", ""))
                print(f"    {disp_name}  [stream {stream_id}]")

    print(f"\nExcluded app patterns: {exclude}")
    print()


def toggle_device_command() -> None:
    """Toggle audio output device."""
    result = toggle_audio_device()
    if result:
        print(f"Switched to: {result}")
    else:
        print("Failed to toggle audio device")
        print("Need at least 2 audio devices configured. Run: volume-monitor --configure")


def update_device_list_command(action: str, pattern: str):
    """Update device filter lists in config."""
    config = MonitorConfig.load_or_default()

    if action == "include":
        if pattern not in config.toggle_devices:
            config.toggle_devices.append(pattern)
            _ = config.save()
            print(f"Added '{pattern}' to include list")
        else:
            print(f"'{pattern}' is already in include list")
    elif action == "exclude":
        if pattern not in config.exclude_devices:
            config.exclude_devices.append(pattern)
            _ = config.save()
            print(f"Added '{pattern}' to exclude list")
        else:
            print(f"'{pattern}' is already in exclude list")

    list_devices_command()


def reset_device_list_command():
    """Clear all device filter lists."""
    config = MonitorConfig.load_or_default()
    config.toggle_devices = []
    config.exclude_devices = []
    _ = config.save()
    print("All device filters cleared - will use all available devices")
    list_devices_command()
