"""Threading utility functions."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import threading


def start_daemon_thread(target, name: str) -> threading.Thread:
    """Start a daemon thread with a given name."""
    thread = threading.Thread(target=target, daemon=True, name=name)
    thread.start()
    return thread
