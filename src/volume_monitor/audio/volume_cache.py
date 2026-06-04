"""Persistent volume cache for per-application volume levels."""

import json
import logging

from ..constants import APP_VOLUME_CACHE_FILE
from ..utils.normalization import normalize_name
from .pipewire import clamp_volume_percent

logger = logging.getLogger(__name__)


def load_app_volume_cache() -> dict[str, int]:
    """Load persisted per-app volume levels."""
    try:
        if APP_VOLUME_CACHE_FILE.exists():
            data = json.loads(APP_VOLUME_CACHE_FILE.read_text())
            out: dict[str, int] = {}
            for k, v in data.items():
                pct = clamp_volume_percent(v)
                if pct is not None:
                    out[normalize_name(k)] = pct
            return out
    except Exception as e:
        logger.debug(f"load app volume cache: {e}")

    return {}


def save_app_volume_cache(cache: dict[str, int]) -> None:
    """Save per-app volume levels to disk."""
    try:
        _ = APP_VOLUME_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.debug(f"save app volume cache: {e}")


def app_volume_cache_key(stream: dict[str, object]) -> str | None:
    """Get cache key for a stream's application."""
    raw_props = stream.get("props")
    props = raw_props if isinstance(raw_props, dict) else {}
    app_name = props.get("application.name") or stream.get("app_name") or stream.get("display_name")
    return normalize_name(str(app_name)) if app_name else None


def get_persisted_volume_for_props(props: dict[str, object]) -> int | None:
    """Get persisted volume for given stream properties."""
    app_key = app_volume_cache_key({"props": props})
    if not app_key:
        return None
    return load_app_volume_cache().get(app_key)
