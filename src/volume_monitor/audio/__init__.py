"""Audio subsystem interactions (PipeWire, PulseAudio)."""
from .pipewire import (
    get_default_sink_state,
    get_current_sink_id,
    get_stream_volume,
    get_stream_volume_retry,
    set_stream_volume_percent,
    ensure_stream_volume_percent,
    parse_wpctl_volume_output,
    volume_percent_from_wpctl_value,
    clamp_volume_percent,
)
from .streams import (
    get_wpctl_audio_streams,
    stream_display_name,
    stream_dedupe_key,
    assign_knob_slots,
)
from .devices import (
    get_available_audio_devices,
    get_toggle_devices,
    toggle_audio_device,
    filter_devices,
)
from .pactl import (
    parse_pactl_sink_inputs,
    set_pactl_sink_input_volume_percent,
)
from .volume_cache import (
    get_persisted_volume_for_props,
    app_volume_cache_key,
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