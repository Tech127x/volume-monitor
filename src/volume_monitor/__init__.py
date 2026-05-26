"""
Volume Monitor for BitFocus Companion.

Real-time audio volume and device monitoring with per-application volume control.
"""

__version__ = "1.0.0"
__author__ = "Tech127x"
__license__ = "MIT"

# Lazy imports to avoid circular dependencies
def get_VolumeMonitor():
    from .monitors.volume import VolumeMonitor
    return VolumeMonitor

def get_AppKnobMonitor():
    from .monitors.app_knobs import AppKnobMonitor
    return AppKnobMonitor

def get_CompanionTCPClient():
    from .companion.client import CompanionTCPClient
    return CompanionTCPClient

# For backwards compatibility
def __getattr__(name):
    if name == "MonitorConfig":
        from .config import MonitorConfig
        return MonitorConfig
    if name == "VolumeMonitor":
        from .monitors.volume import VolumeMonitor
        return VolumeMonitor
    if name == "AppKnobMonitor":
        from .monitors.app_knobs import AppKnobMonitor
        return AppKnobMonitor
    if name == "CompanionTCPClient":
        from .companion.client import CompanionTCPClient
        return CompanionTCPClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")