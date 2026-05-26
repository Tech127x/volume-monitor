"""Monitor classes for volume and app knob tracking."""

# These are imported lazily to avoid circular imports
def get_VolumeMonitor():
    from .volume import VolumeMonitor
    return VolumeMonitor

def get_AppKnobMonitor():
    from .app_knobs import AppKnobMonitor
    return AppKnobMonitor

# Allow direct imports
def __getattr__(name):
    if name == "VolumeMonitor":
        from .volume import VolumeMonitor
        return VolumeMonitor
    if name == "AppKnobMonitor":
        from .app_knobs import AppKnobMonitor
        return AppKnobMonitor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")