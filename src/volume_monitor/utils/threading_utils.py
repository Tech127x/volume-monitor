"""Threading utility functions."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import threading


def start_daemon_thread(target, name: str) -> threading.Thread:
    """Start a daemon thread with a given name."""
    thread = threading.Thread(target=target, daemon=True, name=name)
    thread.start()
    return thread
