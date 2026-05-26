"""BitFocus Companion TCP client."""

def __getattr__(name):
    if name == "CompanionTCPClient":
        from .client import CompanionTCPClient
        return CompanionTCPClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")