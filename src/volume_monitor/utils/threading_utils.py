"""Threading utility functions."""

import threading


def start_daemon_thread(target, name: str) -> threading.Thread:
    """Start a daemon thread with a given name."""
    thread = threading.Thread(target=target, daemon=True, name=name)
    thread.start()
    return thread
