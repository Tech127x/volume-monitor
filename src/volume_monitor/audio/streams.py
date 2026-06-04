"""PipeWire audio stream management."""

import logging
import re
import subprocess
import time
from pathlib import Path

# typing imports replaced with builtins (PEP 585)
from ..constants import (
    BROWSER_STREAM_MIN_AGE,
    DEFAULT_CONFIG,
    DEFAULT_NEW_APP_VOLUME,
    INSPECT_PROP_RE,
    KNOB_APP_FIRST,
    KNOB_APP_LAST,
    MULTI_INSTANCE_APPS,
    STEAM_LAUNCHER_BINARIES,
    STREAM_VOLUME_RESTORE_HIGH,
    WPCTL_STREAM_LINE_RE,
)
from ..utils.normalization import (
    is_excluded_app,
    normalize_name,
    prettify_game_name,
)
from .pactl import parse_pactl_sink_inputs
from .pipewire import (
    clamp_volume_percent,
    ensure_stream_volume_percent,
    get_stream_volume_retry,
)
from .volume_cache import (
    app_volume_cache_key,
    get_persisted_volume_for_props,
    load_app_volume_cache,
    save_app_volume_cache,
)

logger = logging.getLogger(__name__)

# Early restore tracking
EARLY_RESTORED_STREAM_IDS: set[str] = set()

# Track stream appearance times for deduplication
_stream_first_seen: dict[str, float] = {}


def _is_wpctl_stream_child_line(line: str) -> bool:
    """Check if a line is a child of a stream entry."""
    return "output_" in line or " > " in line or "[1.6." in line


def _parse_wpctl_status_stream_ids(status_text: str) -> list[tuple[str, str]]:
    """Parse stream IDs and names from wpctl status output."""
    found: list[tuple[str, str]] = []
    in_audio = False
    in_streams = False

    for line in status_text.splitlines():
        if line.startswith("Audio"):
            in_audio = True
            in_streams = False
            continue
        if line.startswith("Video"):
            in_audio = False
            in_streams = False
            continue
        if not in_audio:
            continue
        if "└─ Streams:" in line:
            in_streams = True
            continue
        if not in_streams:
            continue
        if _is_wpctl_stream_child_line(line):
            continue

        m = re.match(WPCTL_STREAM_LINE_RE, line)
        if not m:
            continue

        stream_id, wpctl_name = m.group(1), m.group(2).strip()
        if not wpctl_name or wpctl_name.endswith("input"):
            continue

        found.append((stream_id, wpctl_name))

    return found


def parse_wpctl_inspect(stream_id: str) -> dict[str, str]:
    """Parse wpctl inspect output for stream properties."""
    props: dict[str, str] = {}

    try:
        res = subprocess.run(
            ["wpctl", "inspect", str(stream_id)],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )

        for line in res.stdout.splitlines():
            m = re.match(INSPECT_PROP_RE, line)
            if m:
                props[m.group(1)] = m.group(2)

    except Exception as e:
        logger.debug(f"wpctl inspect {stream_id} failed: {e}")

    return props


def stream_display_name(stream_id: str, props: dict[str, str], wpctl_name: str) -> str:
    """Generate a human-readable display name for a stream."""
    app_name = props.get("application.name", "").strip()
    binary = props.get("application.process.binary", "").strip()
    media_name = props.get("media.name", "").strip()
    binary_base = Path(binary).name.lower() if binary else ""

    # Check for Steam/Proton/Wine games
    is_steam_like = (
        any(x in app_name.lower() for x in ("steam", "proton", "wine", "gamescope"))
        or binary_base in STEAM_LAUNCHER_BINARIES
    )

    if is_steam_like and binary_base and binary_base not in STEAM_LAUNCHER_BINARIES:
        return prettify_game_name(binary)

    if app_name:
        # For browsers, include media name if available
        if _is_multi_instance_app(app_name) and media_name:
            short_media = media_name if len(media_name) <= 30 else media_name[:27] + "..."
            return f"{app_name}: {short_media}"
        return app_name

    return wpctl_name.strip() or f"Stream {stream_id}"


def _is_multi_instance_app(app_name: str) -> bool:
    """Check if an app is known to create multiple stream instances per tab/window."""
    app_lower = normalize_name(app_name)
    return any(browser in app_lower for browser in MULTI_INSTANCE_APPS)


def stream_dedupe_key(stream_id: str, props: dict[str, str]) -> str:
    """Create a unique key for stream deduplication.

    For multi-instance apps (browsers), use the actual stream ID to ensure
    each distinct stream gets its own knob.
    """
    app_name = props.get("application.name", "").strip()

    if _is_multi_instance_app(app_name):
        return f"stream:{stream_id}"

    return f"app:{normalize_name(app_name)}"


def _build_stream_entry(
    stream_id: str,
    wpctl_name: str,
    props: dict[str, str],
    exclude_apps: list[str] | None = None,
    pactl_id: str | None = None,
) -> dict[str, object]:
    """Build a stream entry dictionary with volume and metadata."""
    exclude_apps_list = DEFAULT_CONFIG["exclude_apps"]
    assert isinstance(exclude_apps_list, list)
    exclude_apps = exclude_apps or exclude_apps_list

    app_name = props.get("application.name", wpctl_name)

    # Apply default volume for never-before-seen apps
    _apply_default_volume_for_new_app(stream_id, props)

    # Apply persisted volume for newly created streams
    early_vol = _apply_persisted_volume_on_stream_create(
        stream_id, props, pactl_id=pactl_id, exclude_apps=exclude_apps
    )

    vol, muted = get_stream_volume_retry(stream_id)
    if early_vol is not None:
        vol = early_vol

    display = stream_display_name(stream_id, props, wpctl_name)

    return {
        "id": stream_id,
        "app_name": app_name,
        "display_name": display,
        "volume": clamp_volume_percent(vol),
        "muted": muted,
        "props": props,
        "dedupe_key": stream_dedupe_key(stream_id, props),
    }


def _apply_default_volume_for_new_app(stream_id: str, props: dict[str, str]) -> None:
    """Apply a safe default volume for apps never seen before."""
    _cache_stream: dict[str, object] = {"props": props}
    app_key = app_volume_cache_key(_cache_stream)
    if not app_key:
        return

    cache = load_app_volume_cache()

    if app_key not in cache:
        default_vol = DEFAULT_CONFIG.get("default_new_app_volume", DEFAULT_NEW_APP_VOLUME)
        assert isinstance(default_vol, int)
        logger.info(
            f"New app detected: {props.get('application.name', 'Unknown')} - "
            + f"setting default volume to {default_vol}%"
        )
        _ = ensure_stream_volume_percent(stream_id, default_vol, attempts=4)
        cache[app_key] = default_vol
        save_app_volume_cache(cache)


def _apply_persisted_volume_on_stream_create(
    stream_id: str,
    props: dict[str, str],
    pactl_id: str | None = None,
    exclude_apps: list[str] | None = None,
) -> int | None:
    """Apply saved volume level when a new stream is created."""
    from .pactl import set_pactl_sink_input_volume_percent
    from .pipewire import ensure_stream_volume_percent

    exclude_apps_list = DEFAULT_CONFIG["exclude_apps"]
    assert isinstance(exclude_apps_list, list)
    exclude_apps = exclude_apps or exclude_apps_list

    app_name = props.get("application.name", "")
    if not app_name or is_excluded_app(app_name, exclude_apps):
        return None

    if stream_id in EARLY_RESTORED_STREAM_IDS:
        return None

    _cache_props: dict[str, object] = dict(props)
    cached = get_persisted_volume_for_props(_cache_props)
    if cached is None:
        return None

    if cached < STREAM_VOLUME_RESTORE_HIGH:
        if pactl_id:
            _ = set_pactl_sink_input_volume_percent(pactl_id, cached)

        vol = ensure_stream_volume_percent(stream_id, cached, attempts=6)
        EARLY_RESTORED_STREAM_IDS.add(stream_id)

        logger.info(
            f"Restored volume for {app_name}: -> {vol}% "
            + f"(wpctl {stream_id}, pactl {pactl_id or '-'})"
        )

        return vol

    return None


def get_wpctl_audio_streams(exclude_apps: list[str] | None = None) -> list[dict[str, object]]:
    """Get all open PipeWire playback streams.

    For multi-instance apps (browsers):
    - Streams must exist for BROWSER_STREAM_MIN_AGE seconds before being shown
    - This filters out temporary ghost streams (~13s lifetime) created by Brave/Chromium
    - Real persistent streams are shown after the settling period
    """
    exclude_apps_list = DEFAULT_CONFIG["exclude_apps"]
    assert isinstance(exclude_apps_list, list)
    exclude_apps = exclude_apps or exclude_apps_list
    streams: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    # Get wpctl status
    try:
        status = subprocess.run(
            ["wpctl", "status"],
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        ).stdout
    except Exception as e:
        logger.error(f"wpctl status failed: {e}")
        status = ""

    # Parse streams from status
    candidates: list[tuple[str, str, dict[str, str]]] = []
    for stream_id, wpctl_name in _parse_wpctl_status_stream_ids(status):
        props = parse_wpctl_inspect(stream_id)

        if props.get("media.class") and "Stream/Output/Audio" not in props.get("media.class", ""):
            continue

        app_name = props.get("application.name", wpctl_name)
        if is_excluded_app(app_name, exclude_apps):
            continue

        candidates.append((stream_id, wpctl_name, props))

    now = time.time()

    # Track first seen time for each stream ID
    for stream_id, wpctl_name, props in candidates:
        app_name = props.get("application.name", wpctl_name)

        if stream_id not in _stream_first_seen:
            _stream_first_seen[stream_id] = now

        age = now - _stream_first_seen[stream_id]

        if _is_multi_instance_app(app_name):
            # Browser streams: require minimum age before showing
            # Ghost streams created by Brave/Chromium on YouTube last ~13 seconds
            # Only real playback streams survive past this threshold
            if age < 0:
                logger.debug(
                    f"Browser stream settling: {app_name} ID={stream_id} "
                    + f"age={age:.1f}s (needs {BROWSER_STREAM_MIN_AGE:.0f}s)"
                )
                continue

        if stream_id not in seen_ids:
            seen_ids.add(stream_id)
            streams.append(_build_stream_entry(stream_id, wpctl_name, props, exclude_apps))

    # Clean up entries for streams that no longer exist
    current_ids = {c[0] for c in candidates}
    expired = [k for k in _stream_first_seen if k not in current_ids]
    for k in expired:
        _ = _stream_first_seen.pop(k, None)

    # pactl fallback
    wpctl_ids = {s["id"] for s in streams}
    pactl_inputs = parse_pactl_sink_inputs()
    status_ids = _parse_wpctl_status_stream_ids(status)

    for entry in pactl_inputs:
        props_val = entry["props"]
        assert isinstance(props_val, dict)
        pactl_props: dict[str, str] = props_val
        app_name = pactl_props.get("application.name", "")
        if not app_name or is_excluded_app(app_name, exclude_apps):
            continue
        pid = pactl_props.get("application.process.id", "")
        matched_id = None
        for stream_id, _wpctl_name in status_ids:
            if stream_id in wpctl_ids:
                continue
            insp = parse_wpctl_inspect(stream_id)
            if insp.get("application.name") != app_name:
                continue
            if pid and insp.get("application.process.id") != pid:
                continue
            matched_id = stream_id
            break
        if matched_id and matched_id not in seen_ids:
            # Check age for browser streams found via pactl
            if _is_multi_instance_app(app_name):
                if matched_id not in _stream_first_seen:
                    _stream_first_seen[matched_id] = now
                if now - _stream_first_seen[matched_id] < 0:
                    continue

            seen_ids.add(matched_id)
            insp = parse_wpctl_inspect(matched_id)
            pactl_id_val = entry.get("pactl_id")
            pactl_id_str: str | None = pactl_id_val if isinstance(pactl_id_val, str) else None
            streams.append(
                _build_stream_entry(matched_id, app_name, insp, exclude_apps, pactl_id=pactl_id_str)
            )
            wpctl_ids.add(matched_id)

    logger.debug(f"Stream count: {len(streams)} (candidates: {len(candidates)})")
    return streams


def assign_knob_slots(
    active_streams: list[dict[str, object]],
    slot_by_key: dict[str, int],
    first_slot: int = KNOB_APP_FIRST,
    last_slot: int = KNOB_APP_LAST,
    compact: bool = True,
) -> dict[int, dict[str, object] | None]:
    """Assign streams to knob slots stably by dedupe_key."""
    active_keys = {str(s["dedupe_key"]) for s in active_streams}

    # Remove dead slots
    for key, slot in list(slot_by_key.items()):
        if key not in active_keys or slot < first_slot or slot > last_slot:
            del slot_by_key[key]

    used_slots = set(slot_by_key.values())
    stream_by_key: dict[str, dict[str, object]] = {str(s["dedupe_key"]): s for s in active_streams}

    # Assign new streams to free slots
    for stream in active_streams:
        key = str(stream["dedupe_key"])
        if key not in slot_by_key:
            free = [i for i in range(first_slot, last_slot + 1) if i not in used_slots]
            if not free:
                break
            slot = free[0]
            slot_by_key[key] = slot
            used_slots.add(slot)

    slots: dict[int, dict[str, object] | None] = {i: None for i in range(first_slot, last_slot + 1)}
    for key, slot_idx in slot_by_key.items():
        if first_slot <= slot_idx <= last_slot and key in stream_by_key:
            slots[slot_idx] = stream_by_key[key]

    if compact:
        slots = _compact_slots(slots, slot_by_key, first_slot, last_slot, stream_by_key)

    return slots


def _compact_slots(
    slots: dict[int, dict[str, object] | None],
    slot_by_key: dict[str, int],
    first_slot: int,
    last_slot: int,
    stream_by_key: dict[str, dict[str, object]],
) -> dict[int, dict[str, object] | None]:
    """Shift streams left to fill gaps in knob assignments."""
    occupied = sorted([s for s in range(first_slot, last_slot + 1) if slots.get(s) is not None])

    if not occupied:
        return slots

    expected = list(range(first_slot, first_slot + len(occupied)))
    if occupied == expected:
        return slots

    new_slots: dict[int, dict[str, object] | None] = {
        i: None for i in range(first_slot, last_slot + 1)
    }
    new_slot_by_key = {}

    target_slot = first_slot
    for old_slot in occupied:
        stream = slots[old_slot]
        if stream is None:
            continue

        new_slots[target_slot] = stream

        key_val = stream.get("dedupe_key")
        if key_val:
            new_slot_by_key[str(key_val)] = target_slot

        if old_slot != target_slot:
            logger.info(
                f"Compacting: {stream.get('display_name', 'Unknown')} "
                + f"moved from knob {old_slot} to knob {target_slot}"
            )

        target_slot += 1

    slot_by_key.clear()
    slot_by_key.update(new_slot_by_key)

    return new_slots
