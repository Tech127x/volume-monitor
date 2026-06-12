"""Command-line interface for Volume Monitor."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import argparse
import atexit
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .cli_utils import (
    interactive_configure,
    list_devices_command,
    list_streams_command,
    reset_device_list_command,
    toggle_device_command,
    update_device_list_command,
)
from .companion.client import CompanionTCPClient
from .config import MonitorConfig
from .fish_support import (
    detect_shell,
    ensure_path_in_shell_config,
    is_fish_shell,
)
from .logging_setup import setup_logger
from .monitors.app_knobs import AppKnobMonitor
from .monitors.volume import VolumeMonitor
from .utils.process import cleanup_pid_file, get_pid_file, is_running

logger: logging.Logger = logging.getLogger(__name__)


def get_pipx_environment() -> dict[str, str]:
    """Get environment variables for pipx execution."""
    env = os.environ.copy()

    # Ensure local bin is in PATH for pipx
    local_bin = Path.home() / ".local" / "bin"
    if str(local_bin) not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"

    # Ensure XDG_RUNTIME_DIR is set
    if "XDG_RUNTIME_DIR" not in env:
        env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

    # Fish-specific environment
    if is_fish_shell():
        env["SHELL"] = os.environ.get("SHELL", "/usr/bin/fish")

    return env


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="volume-monitor",
        description=f"BitFocus Companion Volume & Device Monitor v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "-c",
        "--configure",
        action="store_true",
        help="Run interactive configuration wizard",
    )
    parser.add_argument(
        "--generate-completions",
        action="store_true",
        help="Generate shell completions (Fish/Bash/Zsh)",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--start",
        action="store_true",
        help="Start monitor in background (daemon mode)",
    )
    group.add_argument(
        "-f",
        "--start-foreground",
        action="store_true",
        help="Start monitor in foreground",
    )
    group.add_argument(
        "-k",
        "--stop",
        action="store_true",
        help="Stop running monitor",
    )
    group.add_argument(
        "-r",
        "--restart",
        action="store_true",
        help="Restart the monitor",
    )
    group.add_argument(
        "-S",
        "--status",
        action="store_true",
        help="Check if monitor is running",
    )

    parser.add_argument(
        "-t",
        "--toggle",
        action="store_true",
        help="Toggle between available audio output devices",
    )
    parser.add_argument(
        "-l",
        "--list-devices",
        action="store_true",
        help="List all available audio output devices",
    )
    parser.add_argument(
        "--list-streams",
        action="store_true",
        help="List open per-app audio streams (for Stream Deck+ knobs)",
    )
    parser.add_argument(
        "-i",
        "--include",
        metavar="DEVICE",
        help="Add device to toggle list (supports wildcards)",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        metavar="DEVICE",
        help="Remove device from toggle list (supports wildcards)",
    )
    parser.add_argument(
        "-R",
        "--reset-devices",
        action="store_true",
        help="Clear custom device list and use all devices",
    )

    return parser


def find_executable() -> str:
    """Find the volume-monitor executable path."""
    # Check if we're running via pipx
    if sys.executable:
        venv_bin = Path(sys.executable).parent
        executable = venv_bin / "volume-monitor"
        if executable.exists():
            return str(executable)

    # Fallback to system path
    return sys.argv[0]


def run_foreground(config: MonitorConfig) -> None:
    """Run the monitor in the foreground."""
    global logger
    logger = setup_logger()

    # Log shell info
    shell = detect_shell()
    logger.info(f"Starting monitor in foreground (PID {os.getpid()})")
    logger.info(f"Shell: {shell}")
    logger.info(f"PID file: {get_pid_file()}")

    client = CompanionTCPClient(
        config.companion_ip,
        config.companion_port,
        config.device_id,
    )

    monitor = VolumeMonitor(
        client,
        config.volume_var,
        config.mute_var,
        config.device_var,
        config.notify_on_switch,
        config.notify_sound,
        config.poll_interval,
    )

    app_knob_monitor = None
    if config.enable_app_knobs:
        app_knob_monitor = AppKnobMonitor(
            client,
            exclude_apps=config.exclude_apps,
            poll_interval=config.app_knob_poll_interval,
        )

    def shutdown() -> None:
        monitor.stop()
        if app_knob_monitor:
            app_knob_monitor.stop()
        client.disconnect()
        cleanup_pid_file()
        logger.info("Monitor stopped cleanly.")

    _ = atexit.register(shutdown)

    def signal_handler(sig: int, _frame: object) -> None:
        logger.info(f"Signal {sig} received — stopping")
        monitor.stop()
        sys.exit(0)

    try:
        logger.info("Connecting to Companion...")
        if not client.connect(max_wait=5):
            logger.warning("Could not connect — will retry")
        else:
            logger.info("Connected")

        _ = signal.signal(signal.SIGTERM, signal_handler)
        _ = signal.signal(signal.SIGINT, signal_handler)

        monitor.start()

        if app_knob_monitor:
            app_knob_monitor.start()
            logger.info("Per-app knobs enabled")

        logger.info("Monitor running (Ctrl+C to stop)")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C")
        shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        shutdown()
        sys.exit(1)


def start_daemon(_config: MonitorConfig) -> None:
    """Start the monitor as a background daemon.

    If already running, automatically restart instead.
    """
    global logger
    logger = setup_logger()

    if is_running():
        logger.info("Monitor is already running — restarting to apply any changes...")
        stop_monitor()
        time.sleep(0.5)

    # Check shell and ensure PATH
    if is_fish_shell():
        _ = ensure_path_in_shell_config()
        logger.info("Fish shell detected - ensuring PATH configuration")

    executable = find_executable()
    env = get_pipx_environment()

    try:
        child = subprocess.Popen(
            [sys.executable, executable, "--start-foreground"],
            env=env,
            start_new_session=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        pid_file = get_pid_file()
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        _ = pid_file.write_text(str(child.pid))

        logger.info(f"PID file: {pid_file}")
        logger.info(f"Monitor started (PID: {child.pid})")

        if is_fish_shell():
            logger.info("Check status: volume-monitor --status")
            logger.info("Or use alias: vms")
        else:
            logger.info("Check status: volume-monitor --status")

        logger.info("View logs: tail -f ~/volume_monitor.log")

    except Exception as e:
        cleanup_pid_file()
        logger.error(f"Failed to start: {e}")


def stop_monitor() -> None:
    """Stop a running monitor."""
    global logger
    logger = setup_logger()

    if not is_running():
        logger.info("Monitor is not running")
        return

    pid_file = get_pid_file()
    pid = int(pid_file.read_text().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)

        if not is_running():
            cleanup_pid_file()
            logger.info("Monitor stopped.")
        else:
            logger.warning("Monitor did not stop cleanly.")
            if is_fish_shell():
                logger.info("Try: kill -9 " + str(pid))
    except ProcessLookupError:
        cleanup_pid_file()
        logger.info("Process not found, cleaned up PID file.")


def check_status() -> None:
    """Check and report monitor status."""
    logger = setup_logger()
    shell = detect_shell()

    if is_running():
        pid_file = get_pid_file()
        pid = pid_file.read_text().strip()
        logger.info(f"Monitor is running (PID: {pid})")

        # Check systemd service if available
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-enabled", "volume-monitor.service"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                logger.info("Systemd service: enabled")
            else:
                logger.info("Systemd service: not enabled")
        except Exception:
            pass

        logger.info(f"Shell: {shell}")
        logger.info("Log file: ~/volume_monitor.log")
        logger.info("Config file: ~/.volume_monitor_config.json")

        # Fish-specific info
        if shell == "fish":
            logger.info("Fish aliases: vm, vms, vml, vmt, vmc, vma")
    else:
        logger.info("Monitor is NOT running")

        if shell == "fish":
            logger.info("Start with: volume-monitor --start")
            logger.info("Or use alias: vm --start")


def generate_shell_completions() -> None:
    """Generate shell completion scripts."""
    shell = detect_shell()
    logger = logging.getLogger(__name__)

    if shell == "fish":
        logger.info("Generating Fish shell completions...")
        from .fish_support import install_fish_completions

        if install_fish_completions():
            logger.info("Fish completions installed to ~/.config/fish/completions/")
            logger.info("Restart your shell or run: exec fish")
        else:
            logger.error("Failed to install Fish completions")
    else:
        logger.info(f"Shell completions for {shell} are generated automatically by pipx")
        logger.info("Restart your shell or source your config file")


def main() -> None:
    """Main entry point."""
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)

        # Show shell-specific quick start
        shell = detect_shell()
        print()
        print("Quick start:")
        if shell == "fish":
            print("  volume-monitor --start       # Start monitoring")
            print("  # Or use aliases:")
            print("  vm --start                    # Start monitoring")
            print("  vms                           # Check status")
            print("  vmc                           # Configure")
        else:
            print("  volume-monitor --start       # Start monitoring")
            print("  volume-monitor --configure   # First-time setup")

        print("  volume-monitor --help        # Show all options")
        sys.exit(0)

    args = parser.parse_args()

    # Handle shell completion generation
    if args.generate_completions:
        generate_shell_completions()
        return

    # Handle commands that don't need config
    if args.configure:
        interactive_configure(start_callback=lambda cfg: start_daemon(cfg))  # type: ignore[no-untyped-call]
        return

    if args.list_devices:
        list_devices_command()  # type: ignore[no-untyped-call]
        return

    if args.list_streams:
        list_streams_command()  # type: ignore[no-untyped-call]
        return

    if args.include:
        update_device_list_command("include", args.include)
        return

    if args.exclude:
        update_device_list_command("exclude", args.exclude)
        return

    if args.reset_devices:
        reset_device_list_command()  # type: ignore[no-untyped-call]
        return

    if args.toggle:
        toggle_device_command()  # type: ignore[no-untyped-call]
        return

    # Handle process management commands
    config = MonitorConfig.load_or_default()

    if args.restart:
        logger = setup_logger(debug=args.debug)
        logger.info("Restarting monitor...")
        stop_monitor()
        args.start = True

    if args.start:
        start_daemon(config)
        return

    if args.start_foreground:
        _ = setup_logger(debug=args.debug)
        run_foreground(config)
        return

    if args.stop:
        stop_monitor()
        return

    if args.status:
        check_status()
        return
