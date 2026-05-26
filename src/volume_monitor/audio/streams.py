"""PipeWire audio stream management."""
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..constants import (
    WPCTL_STREAM_LINE_RE,
    INSPECT_PROP_RE,
    DEFAULT_CONFIG,
    KNOB_APP_FIRST,
    KNOB_APP_LAST,
    STEAM_LAUNCHER_BINARIES,
    STREAM_DEDUP_WINDOW,
    DEFAULT_NEW_APP_VOLUME,
    STREAM_VOLUME_RESTORE_HIGH,
    MULTI_INSTANCE_APPS,
    BROWSER_STREAM_MIN_AGE,
)
from ..utils.normalization import (
    normalize_name,
    prettify_game_name,
    disambiguate_label,
    is_excluded_app,
)
from .pipewire import (
    get_stream_volume_retry,
    set_stream_volume_percent,
    ensure_stream_volume_percent,
    clamp_volume_percent,
)
from .pactl import parse_pactl_sink_inputs
from .volume_cache import (
    load_app_volume_cache,
    save_app_volume_cache,
    app_volume_cache_key,
    get_persisted_volume_for_props,
)

logger = logging.getLogger(__name__)

# Early restore tracking
EARLY_RESTORED_STREAM_IDS: set[str] = set()

# Track stream appearance times for deduplication
_stream_first_seen: Dict[str, float] = {}


def _is_wpctl_stream_child_line(line: str) -> bool:
    """Check if a line is a child of a stream entry."""
    return "output_" in line or " > " in line or "[1.6." in line


def _parse_wpctl_status_stream_ids(status_text: str) -> List[Tuple[str, str]]:
    """Parse stream IDs and names from wpctl status output."""
    found: List[Tuple[str, str]] = []
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


def parse_wpctl_inspect(stream_id: str) -> Dict[str, str]:
    """Parse wpctl inspect output for stream properties."""
    props: Dict[str, str] = {}

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


def stream_display_name(stream_id: str, props: Dict[str, str], wpctl_name: str) -> str:
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


def stream_dedupe_key(stream_id: str, props: dict) -> str:
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
    props: dict,
    exclude_apps: Optional[List[str]] = None,
    pactl_id: Optional[str] = None,
) -> dict:
    """Build a stream entry dictionary with volume and metadata."""
    exclude_apps = exclude_apps or DEFAULT_CONFIG["exclude_apps"]

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


def _apply_default_volume_for_new_app(stream_id: str, props: dict) -> None:
    """Apply a safe default volume for apps never seen before."""
    app_key = app_volume_cache_key({"props": props})
    if not app_key:
        return

    cache = load_app_volume_cache()

    if app_key not in cache:
        default_vol = DEFAULT_CONFIG.get("default_new_app_volume", DEFAULT_NEW_APP_VOLUME)
        logger.info(
            f"New app detected: {props.get('application.name', 'Unknown')} - "
            f"setting default volume to {default_vol}%"
        )
        ensure_stream_volume_percent(stream_id, default_vol, attempts=4)
        cache[app_key] = default_vol
        save_app_volume_cache(cache)


def _apply_persisted_volume_on_stream_create(
    stream_id: str,
    props: dict,
    pactl_id: Optional[str] = None,
    exclude_apps: Optional[List[str]] = None,
) -> Optional[int]:
    """Apply saved volume level when a new stream is created."""
    from .pipewire import ensure_stream_volume_percent
    from .pactl import set_pactl_sink_input_volume_percent

    exclude_apps = exclude_apps or DEFAULT_CONFIG["exclude_apps"]

    app_name = props.get("application.name", "")
    if not app_name or is_excluded_app(app_name, exclude_apps):
        return None

    if stream_id in EARLY_RESTORED_STREAM_IDS:
        return None

    cached = get_persisted_volume_for_props(props)
    if cached is None:
        return None

    if cached < STREAM_VOLUME_RESTORE_HIGH:
        if pactl_id:
            set_pactl_sink_input_volume_percent(pactl_id, cached)

        vol = ensure_stream_volume_percent(stream_id, cached, attempts=6)
        EARLY_RESTORED_STREAM_IDS.add(stream_id)

        logger.info(
            f"Restored volume for {app_name}: -> {vol}% "
            f"(wpctl {stream_id}, pactl {pactl_id or '-'})"
        )

        return vol

    return None


def get_wpctl_audio_streams(
    exclude_apps: Optional[List[str]] = None
) -> List[dict]:
    """Get all open PipeWire playback streams.

    For multi-instance apps (browsers):
    - Streams must exist for BROWSER_STREAM_MIN_AGE seconds before being shown
    - This filters out temporary ghost streams (~13s lifetime) created by Brave/Chromium
    - Real persistent streams are shown after the settling period
    """
    exclude_apps = exclude_apps or DEFAULT_CONFIG["exclude_apps"]
    streams: List[dict] = []
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
    candidates: List[Tuple[str, str, dict]] = []
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
            if age < BROWSER_STREAM_MIN_AGE:
                logger.debug(
                    f"Browser stream settling: {app_name} ID={stream_id} "
                    f"age={age:.1f}s (needs {BROWSER_STREAM_MIN_AGE:.0f}s)"
                )
                continue

        if stream_id not in seen_ids:
            seen_ids.add(stream_id)
            streams.append(_build_stream_entry(stream_id, wpctl_name, props, exclude_apps))

    # Clean up entries for streams that no longer exist
    current_ids = {c[0] for c in candidates}
    expired = [k for k in _stream_first_seen if k not in current_ids]
    for k in expired:
        _stream_first_seen.pop(k, None)

    # pactl fallback
    wpctl_ids = {s["id"] for s in streams}
    pactl_inputs = parse_pactl_sink_inputs()
    status_ids = _parse_wpctl_status_stream_ids(status)

    for entry in pactl_inputs:
        props = entry["props"]
        app_name = props.get("application.name", "")
        if not app_name or is_excluded_app(app_name, exclude_apps):
            continue
        pid = props.get("application.process.id", "")
        matched_id = None
        for stream_id, wpctl_name in status_ids:
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
                if now - _stream_first_seen[matched_id] < BROWSER_STREAM_MIN_AGE:
                    continue

            seen_ids.add(matched_id)
            insp = parse_wpctl_inspect(matched_id)
            streams.append(
                _build_stream_entry(
                    matched_id, app_name, insp, exclude_apps,
                    pactl_id=entry.get("pactl_id")
                )
            )
            wpctl_ids.add(matched_id)

    logger.debug(f"Stream count: {len(streams)} (candidates: {len(candidates)})")
    return streams


def assign_knob_slots(
    active_streams: List[dict],
    slot_by_key: Dict[str, int],
    first_slot: int = KNOB_APP_FIRST,
    last_slot: int = KNOB_APP_LAST,
    compact: bool = True,
) -> Dict[int, Optional[dict]]:
    """Assign streams to knob slots stably by dedupe_key."""
    active_keys = {s["dedupe_key"] for s in active_streams}

    # Remove dead slots
    for key, slot in list(slot_by_key.items()):
        if key not in active_keys or slot < first_slot or slot > last_slot:
            del slot_by_key[key]

    used_slots = set(slot_by_key.values())
    stream_by_key = {s["dedupe_key"]: s for s in active_streams}

    # Assign new streams to free slots
    for stream in active_streams:
        key = stream["dedupe_key"]
        if key not in slot_by_key:
            free = [i for i in range(first_slot, last_slot + 1) if i not in used_slots]
            if not free:
                break
            slot = free[0]
            slot_by_key[key] = slot
            used_slots.add(slot)

    slots = {i: None for i in range(first_slot, last_slot + 1)}
    for key, slot_idx in slot_by_key.items():
        if first_slot <= slot_idx <= last_slot and key in stream_by_key:
            slots[slot_idx] = stream_by_key[key]

    if compact:
        slots = _compact_slots(slots, slot_by_key, first_slot, last_slot, stream_by_key)

    return slots


def _compact_slots(
    slots: Dict[int, Optional[dict]],
    slot_by_key: Dict[str, int],
    first_slot: int,
    last_slot: int,
    stream_by_key: Dict[str, dict],
) -> Dict[int, Optional[dict]]:
    """Shift streams left to fill gaps in knob assignments."""
    occupied = sorted(
        [s for s in range(first_slot, last_slot + 1) if slots.get(s) is not None]
    )

    if not occupied:
        return slots

    expected = list(range(first_slot, first_slot + len(occupied)))
    if occupied == expected:
        return slots

    new_slots = {i: None for i in range(first_slot, last_slot + 1)}
    new_slot_by_key = {}

    target_slot = first_slot
    for old_slot in occupied:
        stream = slots[old_slot]
        if stream is None:
            continue

        new_slots[target_slot] = stream

        key = stream.get("dedupe_key")
        if key:
            new_slot_by_key[key] = target_slot

        if old_slot != target_slot:
            logger.info(
                f"Compacting: {stream.get('display_name', 'Unknown')} "
                f"moved from knob {old_slot} to knob {target_slot}"
            )

        target_slot += 1

    slot_by_key.clear()
    slot_by_key.update(new_slot_by_key)

    return new_slots