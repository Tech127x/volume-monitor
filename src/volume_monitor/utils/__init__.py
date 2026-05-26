"""Utility functions for Volume Monitor."""

def __getattr__(name):
    if name == "normalize_name":
        from .normalization import normalize_name
        return normalize_name
    if name == "norm_device_name":
        from .normalization import norm_device_name
        return norm_device_name
    if name == "prettify_game_name":
        from .normalization import prettify_game_name
        return prettify_game_name
    if name == "get_pid_file":
        from .process import get_pid_file
        return get_pid_file
    if name == "is_running":
        from .process import is_running
        return is_running
    if name == "cleanup_pid_file":
        from .process import cleanup_pid_file
        return cleanup_pid_file
    if name == "send_notification":
        from .notifications import send_notification
        return send_notification
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")