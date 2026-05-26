"""Process management utilities."""
import os
import signal
from pathlib import Path


def get_pid_file() -> Path:
    """Get the appropriate PID file location."""
    xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    run_dir = Path(xdg)
    
    if run_dir.exists() and os.access(run_dir, os.W_OK):
        return run_dir / "volume_monitor.pid"
    
    cfg_dir = Path.home() / ".config" / "volume_monitor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "volume_monitor.pid"


def is_running(pid_file: Path | None = None) -> bool:
    """Check if the monitor is already running."""
    pf = pid_file or get_pid_file()
    
    if not pf.exists():
        return False
    
    try:
        pid = int(pf.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, PermissionError):
        pf.unlink(missing_ok=True)
        return False


def cleanup_pid_file(pid_file: Path | None = None) -> None:
    """Remove the PID file."""
    pf = pid_file or get_pid_file()
    pf.unlink(missing_ok=True)