"""
Volume Monitor for BitFocus Companion.

Real-time audio volume and device monitoring with per-application volume control.
"""

from .companion.client import CompanionTCPClient
from .config import MonitorConfig
from .monitors.app_knobs import AppKnobMonitor
from .monitors.volume import VolumeMonitor

__version__ = "1.0.0"
__author__ = "Tech127x"
__license__ = "MIT"

__all__ = [
    "MonitorConfig",
    "VolumeMonitor",
    "AppKnobMonitor",
    "CompanionTCPClient",
]
