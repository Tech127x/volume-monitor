"""Per-application volume knob monitor for Stream Deck+."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import logging
import re
import subprocess
import time

# typing imports replaced with builtins (PEP 585)
from ..audio.pactl import (
    parse_pactl_sink_inputs,
    set_pactl_sink_input_volume_percent,
)
from ..audio.pipewire import (
    clamp_volume_percent,
    ensure_stream_volume_percent,
    get_current_sink_id,
    get_default_sink_state,
    get_stream_volume_retry,
)
from ..audio.streams import (
    assign_knob_slots,
    get_wpctl_audio_streams,
)
from ..audio.volume_cache import (
    app_volume_cache_key,
    get_persisted_volume_for_props,
    load_app_volume_cache,
    save_app_volume_cache,
)
from ..companion.client import CompanionTCPClient
from ..constants import (
    DEFAULT_CONFIG,
    DEFAULT_NEW_APP_VOLUME,
    DEFAULT_SINK_TARGET,
    KNOB_APP_FIRST,
    KNOB_APP_LAST,
    KNOB_MASTER,
    PACTL_EVENT_NEW_INPUT,
    STREAM_BIND_REPUSH_COUNT,
    STREAM_BIND_REPUSH_INTERVAL,
    STREAM_SLOT_GRACE_SEC,
    STREAM_VOLUME_RESTORE_HIGH,
)
from ..monitors.base import BaseMonitor
from ..utils.normalization import (
    disambiguate_label,
    is_excluded_app,
    norm_device_name,
)
from ..utils.threading_utils import start_daemon_thread

logger = logging.getLogger(__name__)


def _apply_default_volume_for_new_app_props(props: dict[str, object], pactl_id: str) -> None:
    """Set a safe default volume for a newly seen app via its pactl sink-input.

    Called from `_on_new_sink_input` to catch apps the moment they appear,
    before PipeWire's default volume (often 100%) can be heard.
    """
    app_key = app_volume_cache_key({"props": props})
    if not app_key:
        return
    cache = load_app_volume_cache()
    if app_key not in cache:
        default_vol = DEFAULT_NEW_APP_VOLUME
        logger.info(f"New app via pactl: setting default volume to {default_vol}%")
        _ = set_pactl_sink_input_volume_percent(pactl_id, default_vol)
        cache[app_key] = default_vol
        save_app_volume_cache(cache)


class AppKnobMonitor(BaseMonitor):
    """Monitors per-app audio streams and maps them to Stream Deck+ knobs."""

    def __init__(
        self,
        client: CompanionTCPClient,
        exclude_apps: list[str] | None = None,
        poll_interval: float = 0.1,
        enable_compaction: bool = True,
        default_new_app_volume: int = DEFAULT_NEW_APP_VOLUME,
    ):
        super().__init__(client)
        exclude_apps_list = DEFAULT_CONFIG["exclude_apps"]
        assert isinstance(exclude_apps_list, list)
        self.exclude_apps = exclude_apps or exclude_apps_list
        self.poll_interval = poll_interval
        self.enable_compaction = enable_compaction
        self.default_new_app_volume = default_new_app_volume

        # State tracking
        self._slot_by_key: dict[str, int] = {}
        self._last_snapshot: tuple[object, ...] | None = None
        self._volume_by_key: dict[str, int] = {}
        self._persisted_volumes: dict[str, int] = load_app_volume_cache()
        self._last_stream_id_by_key: dict[str, str] = {}
        self._last_stream_by_key: dict[str, dict[str, object]] = {}
        self._last_seen_by_key: dict[str, float] = {}
        self._app_knob_live: dict[int, bool] = {}
        self._app_knob_armed: dict[int, bool] = {}
        self._companion_stream_id: dict[int, str] = {}
        self._previous_slot_for_key: dict[str, int] = {}

    def _knob_vars(self, knob_number: int) -> dict[str, str]:
        """Get Companion variable names for a knob."""
        return {
            "label": f"knob{knob_number}_label",
            "volume": f"knob{knob_number}_volume",
            "dial_pct": f"knob{knob_number}_dial_pct",
            "muted": f"knob{knob_number}_muted",
            "stream_id": f"knob{knob_number}_stream_id",
            "active": f"knob{knob_number}_active",
        }

    def _set_level_feedback(self, vars_map: dict[str, str], value: str) -> None:
        """Set volume level feedback variables."""
        _ = self.client.update_variable(vars_map["dial_pct"], value)
        _ = self.client.update_variable(vars_map["volume"], value)

    def _reset_knob_slot(self, vars_map: dict[str, str]) -> None:
        """Reset a knob slot to empty state."""
        _ = self._set_level_feedback(vars_map, "0")
        _ = self.client.update_variable(vars_map["stream_id"], "0")

    def _companion_volume_pct(self, stream: dict[str, object], vol: int | None) -> int | None:
        """Get volume percentage to show on Companion, masking 100% when cached lower."""
        pct = clamp_volume_percent(vol)
        cached = self._get_cached_volume(stream)

        if (
            pct is not None
            and pct >= STREAM_VOLUME_RESTORE_HIGH
            and cached is not None
            and cached < STREAM_VOLUME_RESTORE_HIGH
        ):
            return cached

        return pct

    def _push_volume_feedback(
        self,
        knob_number: int,
        stream: dict[str, object],
        vol: int | None,
    ) -> int | None:
        """Push volume feedback to Companion variables."""
        pct = self._companion_volume_pct(stream, vol)
        if pct is None:
            return None

        v = self._knob_vars(knob_number)
        s = str(pct)
        self._set_level_feedback(v, s)
        return pct

    def _schedule_stream_id_bind(
        self,
        knob_number: int,
        stream: dict[str, object],
        vol: int,
        stream_id: str,
    ) -> None:
        """Defer stream_id binding to avoid 100% flash on bind."""

        def worker() -> None:
            v = self._knob_vars(knob_number)
            pct = str(vol)

            for _ in range(STREAM_BIND_REPUSH_COUNT):
                time.sleep(STREAM_BIND_REPUSH_INTERVAL)
                _ = self._set_level_feedback(v, pct)

            _ = self.client.update_variable(v["stream_id"], stream_id)

            for _ in range(STREAM_BIND_REPUSH_COUNT // 2):
                time.sleep(STREAM_BIND_REPUSH_INTERVAL)
                _ = self._set_level_feedback(v, pct)

            logger.debug(
                f"Knob {knob_number} bound stream {stream_id} at {pct}% ({stream.get('display_name')})"
            )

        _ = start_daemon_thread(worker, f"knob-{knob_number}-stream-bind")

    def _refresh_volume(self, stream: dict[str, object]) -> None:
        """Refresh volume from system for a stream."""
        if stream.get("is_master"):
            _, muted, vol = get_default_sink_state()
        else:
            sid = stream["id"]
            assert isinstance(sid, str)
            vol, muted = get_stream_volume_retry(sid)

        if vol is not None:
            stream["volume"] = clamp_volume_percent(vol)
        stream["muted"] = muted

    def _get_cached_volume(self, stream: dict[str, object]) -> int | None:
        """Get cached volume for a stream."""
        key_val = stream.get("dedupe_key")
        if isinstance(key_val, str) and key_val in self._volume_by_key:
            return self._volume_by_key[key_val]

        app_key = app_volume_cache_key(stream)
        if app_key and app_key in self._persisted_volumes:
            return self._persisted_volumes[app_key]

        return None

    def _remember_volume(self, stream: dict[str, object]) -> None:
        """Remember volume in cache."""
        key_val = stream.get("dedupe_key")
        vol_val = stream.get("volume")
        vol = clamp_volume_percent(vol_val if isinstance(vol_val, (int, float)) else None)

        if isinstance(key_val, str) and vol is not None:
            self._volume_by_key[key_val] = vol

        app_key = app_volume_cache_key(stream)
        if app_key and vol is not None and self._persisted_volumes.get(app_key) != vol:
            self._persisted_volumes[app_key] = vol
            save_app_volume_cache(self._persisted_volumes)

    def _prepare_app_stream(self, stream: dict[str, object]) -> int | None:
        """Prepare app stream with volume restoration if needed."""
        sid_val = stream.get("id")
        sid = str(sid_val) if isinstance(sid_val, str) else None
        key_val = stream.get("dedupe_key")
        key = str(key_val) if isinstance(key_val, str) else None
        cached = self._get_cached_volume(stream)
        prev_id = self._last_stream_id_by_key.get(key) if key else None
        id_changed = prev_id is not None and prev_id != sid
        is_new_instance = bool(key and key not in self._volume_by_key)

        self._refresh_volume(stream)
        vol_val = stream.get("volume")
        wpctl_vol = clamp_volume_percent(vol_val if isinstance(vol_val, (int, float)) else None)

        if isinstance(key, str) and isinstance(sid, str):
            self._last_stream_id_by_key[key] = sid

        target = wpctl_vol
        should_consider_restore = (
            cached is not None
            and cached < STREAM_VOLUME_RESTORE_HIGH
            and sid
            and (id_changed or is_new_instance)
        )
        restore_needed = wpctl_vol is None or (
            wpctl_vol is not None and wpctl_vol >= STREAM_VOLUME_RESTORE_HIGH
        )

        if should_consider_restore and restore_needed:
            assert isinstance(sid, str)
            assert cached is not None
            target = ensure_stream_volume_percent(sid, cached)
            logger.info(
                f"App volume {stream.get('display_name')}: wpctl {wpctl_vol}% -> {target}% (stream {sid})"
            )

        if target is not None:
            stream["volume"] = target

        self._remember_volume(stream)
        return target

    def _track_streams(self, streams: list[dict[str, object]]) -> None:
        """Track stream presence and last seen times."""
        now = time.time()
        for s in streams:
            key_val = s.get("dedupe_key")
            if not isinstance(key_val, str):
                continue
            self._last_seen_by_key[key_val] = now
            self._last_stream_by_key[key_val] = s

    def _apply_slot_grace(
        self, app_slots: dict[int, dict[str, object] | None]
    ) -> dict[int, dict[str, object] | None]:
        """Keep slots briefly when streams disappear (avoid volume=0 flash)."""
        now = time.time()
        out = dict(app_slots)

        for key, slot in self._slot_by_key.items():
            if not (KNOB_APP_FIRST <= slot <= KNOB_APP_LAST):
                continue
            if out.get(slot) is not None:
                continue
            if now - self._last_seen_by_key.get(key, 0) > STREAM_SLOT_GRACE_SEC:
                continue

            ghost = self._last_stream_by_key.get(key)
            if ghost:
                out[slot] = ghost

        return out

    def _push_knob(self, knob_number: int, stream: dict[str, object] | None) -> None:
        """Push a single knob's state to Companion."""
        v = self._knob_vars(knob_number)
        is_app_knob = KNOB_APP_FIRST <= knob_number <= KNOB_APP_LAST

        if stream is None:
            _ = self._reset_knob_slot(v)
            _ = self.client.update_variable(v["label"], '""')
            _ = self.client.update_variable(v["muted"], "false")

            if is_app_knob:
                self._app_knob_live[knob_number] = False
                _ = self._companion_stream_id.pop(knob_number, None)
            else:
                _ = self.client.update_variable(v["active"], "false")
            return

        label = stream.get("label", stream["display_name"])
        target = str(stream["id"])

        if stream.get("is_master"):
            self._refresh_volume(stream)
            vol_val = stream.get("volume")
            vol = clamp_volume_percent(vol_val if isinstance(vol_val, (int, float)) else None)
            if vol is not None:
                stream["volume"] = vol
                _ = self._set_level_feedback(v, str(vol))

            _ = self.client.update_variable(v["stream_id"], target)
            _ = self.client.update_variable(v["muted"], "true" if stream.get("muted") else "false")
            _ = self.client.update_variable(v["label"], f'"{label}"')
            _ = self.client.update_variable(v["active"], "true")
            return

        # App knob
        vol = self._prepare_app_stream(stream)
        vol = self._push_volume_feedback(knob_number, stream, vol)
        if vol is not None:
            stream["volume"] = vol

        _ = self.client.update_variable(v["muted"], "true" if stream.get("muted") else "false")
        _ = self.client.update_variable(v["label"], f'"{label}"')
        self._app_knob_live[knob_number] = True

        prev_sid = self._companion_stream_id.get(knob_number)
        if prev_sid != target:
            self._companion_stream_id[knob_number] = target
            if vol is not None:
                _ = self._schedule_stream_id_bind(knob_number, stream, vol, target)
            else:
                _ = self.client.update_variable(v["stream_id"], target)
        elif vol is not None:
            _ = self.client.update_variable(v["stream_id"], target)
        else:
            _ = self.client.update_variable(v["stream_id"], target)

    def _master_stream_dict(self) -> dict[str, object]:
        """Create master stream dictionary for default sink."""
        device, muted, vol = get_default_sink_state()
        label = norm_device_name(device)
        sink_id = get_current_sink_id() or DEFAULT_SINK_TARGET

        return {
            "id": sink_id,
            "display_name": label,
            "label": label,
            "volume": clamp_volume_percent(vol),
            "muted": muted,
            "props": {},
            "is_master": True,
        }

    def _stream_snapshot(self, stream: dict[str, object] | None) -> tuple[object, ...] | None:
        """Create a lightweight snapshot of a stream for change detection."""
        if stream is None:
            return None

        if stream.get("is_master"):
            return (stream["id"], stream.get("label"), stream.get("volume"), stream.get("muted"))

        return (stream["id"], stream.get("label"), stream.get("muted"))

    def _build_snapshot(
        self, master: dict[str, object], app_slots: dict[int, dict[str, object] | None]
    ) -> tuple[object, ...]:
        """Build a full snapshot for change detection."""
        app_part = tuple(
            self._stream_snapshot(app_slots.get(i))
            for i in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1)
        )
        return (self._stream_snapshot(master), app_part)

    def update_companion(
        self, master: dict[str, object], app_slots: dict[int, dict[str, object] | None]
    ) -> None:
        """Update all Companion variables."""
        used_labels: set[str] = {str(master["label"])}

        for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
            stream = app_slots.get(knob)
            if stream is None:
                continue
            display_name_val = stream["display_name"]
            props_val = stream["props"]
            assert isinstance(display_name_val, str)
            assert isinstance(props_val, dict)
            label = disambiguate_label(display_name_val, props_val, used_labels)
            stream["label"] = label
            used_labels.add(label)

        # Check for slot changes and reset old slots
        for key, new_slot in self._slot_by_key.items():
            old_slot = self._previous_slot_for_key.get(key)
            if old_slot is not None and old_slot != new_slot:
                old_vars = self._knob_vars(old_slot)
                _ = self._reset_knob_slot(old_vars)
                _ = self.client.update_variable(old_vars["label"], '""')
                logger.debug(f"Reset knob {old_slot} (stream moved to knob {new_slot})")

        self._previous_slot_for_key = dict(self._slot_by_key)

        self._push_knob(KNOB_MASTER, master)
        for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
            self._push_knob(knob, app_slots.get(knob))

        snap = self._build_snapshot(master, app_slots)
        if snap != self._last_snapshot:
            self._last_snapshot = snap
            apps: list[str] = []
            for i in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
                slot = app_slots.get(i)
                if slot is not None:
                    apps.append(str(slot["label"]))
            logger.debug(f"Knob 1: {master['label']} | Apps: {apps or '(none)'}")

    def push_initial_state(self) -> bool:
        """Push initial state to Companion."""
        master = self._master_stream_dict()
        streams = get_wpctl_audio_streams(self.exclude_apps)
        self._track_streams(streams)
        app_slots = self._apply_slot_grace(
            assign_knob_slots(
                streams,
                self._slot_by_key,
                compact=self.enable_compaction,
            )
        )
        self.update_companion(master, app_slots)
        return True

    def _poll_loop(self) -> None:
        """Main polling loop for app knobs."""
        while self._running.is_set():
            try:
                master = self._master_stream_dict()
                streams = get_wpctl_audio_streams(self.exclude_apps)
                self._track_streams(streams)
                app_slots = self._apply_slot_grace(
                    assign_knob_slots(
                        streams,
                        self._slot_by_key,
                        compact=self.enable_compaction,
                    )
                )

                snap = self._build_snapshot(master, app_slots)
                if snap != self._last_snapshot:
                    self.update_companion(master, app_slots)
                else:
                    for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
                        s = app_slots.get(knob)
                        if not s:
                            continue
                        old_vol = s.get("volume")
                        vol = self._prepare_app_stream(s)
                        vol = self._push_volume_feedback(knob, s, vol)
                        if vol is not None and vol != old_vol:
                            s["volume"] = vol

                    m_old = master.get("volume")
                    self._refresh_volume(master)
                    m_vol_val = master.get("volume")
                    m_vol = clamp_volume_percent(
                        m_vol_val if isinstance(m_vol_val, (int, float)) else None
                    )
                    if m_vol is not None and m_vol != m_old:
                        master["volume"] = m_vol
                        _ = self.client.update_variable(
                            self._knob_vars(KNOB_MASTER)["volume"],
                            str(m_vol),
                        )

                time.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"App knob poll error: {e}")
                time.sleep(self.poll_interval)

    def _arm_app_knobs(self) -> None:
        """Set app knobs as active once, hiding empty slots via volume=0."""
        for knob in range(KNOB_APP_FIRST, KNOB_APP_LAST + 1):
            if self._app_knob_armed.get(knob):
                continue

            v = self._knob_vars(knob)
            _ = self.client.update_variable(v["active"], "true")
            _ = self._reset_knob_slot(v)
            self._app_knob_armed[knob] = True

    def _on_new_sink_input(self, pactl_id: str) -> None:
        """React to new playback streams from pactl events."""
        for entry in parse_pactl_sink_inputs():
            if entry["pactl_id"] != pactl_id:
                continue

            props_val = entry["props"]
            assert isinstance(props_val, dict)
            props: dict[str, str] = props_val
            app_name = props.get("application.name", "")

            if not app_name or is_excluded_app(app_name, self.exclude_apps):
                return

            # Apply default volume for never-before-seen apps immediately
            # This catches apps the moment they create a sink-input, before
            # they can play audio at the PipeWire default (often 100%)
            _cache_props: dict[str, object] = dict(props)
            _apply_default_volume_for_new_app_props(_cache_props, pactl_id)

            cached = get_persisted_volume_for_props(_cache_props)
            if cached is None or cached >= STREAM_VOLUME_RESTORE_HIGH:
                return

            _ = set_pactl_sink_input_volume_percent(pactl_id, cached)

            try:
                status = subprocess.run(
                    ["wpctl", "status"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=2,
                ).stdout
            except Exception:
                return

            from ..audio.streams import _parse_wpctl_status_stream_ids, parse_wpctl_inspect

            for stream_id, _wpctl_name in _parse_wpctl_status_stream_ids(status):
                insp = parse_wpctl_inspect(stream_id)
                if insp.get("application.name") != app_name:
                    continue
                if props.get("application.process.id") and insp.get(
                    "application.process.id"
                ) != props.get("application.process.id"):
                    continue

                _ = ensure_stream_volume_percent(stream_id, cached, attempts=4)
                logger.info(
                    f"pactl subscribe restore {app_name}: {cached}% (sink-input {pactl_id}, wpctl {stream_id})"
                )
                return

            logger.info(
                f"pactl subscribe restore {app_name}: {cached}% (sink-input {pactl_id}, wpctl pending)"
            )
            return

    def _pactl_subscribe_loop(self) -> None:
        """Listen for new sink-input events via pactl subscribe."""
        try:
            proc = subprocess.Popen(
                ["pactl", "subscribe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            logger.warning(f"pactl subscribe unavailable: {e}")
            return

        logger.info("pactl subscribe listening for new app audio streams")

        while self._running.is_set() and proc.stdout:
            line = proc.stdout.readline()
            if not line:
                break

            m = re.search(PACTL_EVENT_NEW_INPUT, line)
            if m:
                try:
                    self._on_new_sink_input(m.group(1))
                except Exception as e:
                    logger.debug(f"new sink-input handler: {e}")

        logger.debug("pactl subscribe loop ended")

    def start(self) -> None:
        """Start the app knob monitor."""
        logger.info(
            f"Starting knob monitor (knob {KNOB_MASTER}=default sink, knobs {KNOB_APP_FIRST}-{KNOB_APP_LAST}=apps, poll {self.poll_interval}s)"
        )
        logger.info(f"  Knob compaction: {'enabled' if self.enable_compaction else 'disabled'}")
        logger.info(f"  Default new app volume: {self.default_new_app_volume}%")

        self._running.set()
        self._arm_app_knobs()

        _ = start_daemon_thread(self._pactl_subscribe_loop, "pactl-subscribe")
        _ = start_daemon_thread(self._poll_loop, "app-knob-poll")

        _ = self.push_initial_state()

    def stop(self) -> None:
        """Stop the app knob monitor."""
        super().stop()
        logger.info("Stopped AppKnobMonitor")
