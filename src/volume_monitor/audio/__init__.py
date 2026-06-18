"""Audio subsystem interactions (PipeWire, PulseAudio)."""

from .devices import (
    filter_devices,
    get_available_audio_devices,
    get_toggle_devices,
    toggle_audio_device,
)
from .pactl import (
    parse_pactl_sink_inputs,
    set_pactl_sink_input_volume_percent,
)
from .pipewire import (
    clamp_volume_percent,
    ensure_stream_volume_percent,
    get_current_sink_id,
    get_default_sink_state,
    get_stream_volume,
    get_stream_volume_retry,
    parse_wpctl_volume_output,
    set_stream_volume_percent,
    volume_percent_from_wpctl_value,
)
from .streams import (
    assign_knob_slots,
    get_wpctl_audio_streams,
    stream_dedupe_key,
    stream_display_name,
)
from .volume_cache import (
    app_volume_cache_key,
    get_persisted_volume_for_props,
    load_app_volume_cache,
    save_app_volume_cache,
)

__all__ = [
    "get_default_sink_state",
    "get_current_sink_id",
    "get_stream_volume",
    "get_stream_volume_retry",
    "set_stream_volume_percent",
    "ensure_stream_volume_percent",
    "parse_wpctl_volume_output",
    "volume_percent_from_wpctl_value",
    "clamp_volume_percent",
    "get_wpctl_audio_streams",
    "stream_display_name",
    "stream_dedupe_key",
    "assign_knob_slots",
    "get_available_audio_devices",
    "get_toggle_devices",
    "toggle_audio_device",
    "filter_devices",
    "parse_pactl_sink_inputs",
    "set_pactl_sink_input_volume_percent",
    "get_persisted_volume_for_props",
    "app_volume_cache_key",
    "load_app_volume_cache",
    "save_app_volume_cache",
]
