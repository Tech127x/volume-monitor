#!/usr/bin/env python3
"""Generate Fish shell completions for volume-monitor dynamically."""
import sys
from pathlib import Path

FISH_COMPLETIONS_DIR = Path.home() / ".config" / "fish" / "completions"
COMPLETIONS_FILE = FISH_COMPLETIONS_DIR / "volume-monitor.fish"


def get_audio_devices() -> list[str]:
    """Get list of audio device names for completions."""
    devices = []
    try:
        import subprocess
        result = subprocess.run(
            ["wpctl", "status"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        
        in_sinks = False
        for line in result.stdout.splitlines():
            if "Sinks:" in line:
                in_sinks = True
                continue
            if "Sources:" in line:
                break
            if in_sinks and line.strip() and not line.startswith(" "):
                # Extract device name
                parts = line.split(".", 1)
                if len(parts) > 1:
                    name = parts[1].split("[vol:")[0].strip()
                    if name and not name.startswith("*"):
                        devices.append(name)
    except Exception:
        pass
    
    return devices


def generate_fish_completions() -> str:
    """Generate the complete fish completion script."""
    return f'''# Fish completions for volume-monitor
# Auto-generated for CachyOS

function __fish_volume_monitor_needs_command
    set -l cmd (commandline -opc)
    test (count $cmd) -eq 1
end

function __fish_volume_monitor_no_subcommand
    set -l cmd (commandline -opc)
    set -l subcommands start stop restart status
    for sub in $subcommands
        if contains -- $sub $cmd
            return 1
        end
    end
    return 0
end

function __fish_volume_monitor_devices
    wpctl status 2>/dev/null | \\
        grep -A 50 "Sinks:" | \\
        grep "^\\s*[0-9]" | \\
        string match -rg '\\d+\\.\\s+(.+?)\\s+\\[' | \\
        string trim
end

# Disable file completion by default
complete -c volume-monitor -f

# Main commands (mutually exclusive group)
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s s -l start -d 'Start monitor in background (daemon mode)'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s f -l start-foreground -d 'Start monitor in foreground'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s k -l stop -d 'Stop running monitor'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s r -l restart -d 'Restart the monitor'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s S -l status -d 'Check if monitor is running'

# Configuration and info
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s c -l configure -d 'Run interactive configuration wizard'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s l -l list-devices -d 'List all audio output devices'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -l list-streams -d 'List per-app audio streams'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s t -l toggle -d 'Toggle between audio output devices'

# Device management
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s i -l include -d 'Add device to toggle list (supports wildcards)' \\
    -x -a '(__fish_volume_monitor_devices)'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s x -l exclude -d 'Exclude device from toggle list (supports wildcards)' \\
    -x -a '(__fish_volume_monitor_devices)'
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s R -l reset-devices -d 'Clear device filter list'

# Debug
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s d -l debug -d 'Enable verbose debug logging'

# Help
complete -c volume-monitor -n '__fish_volume_monitor_needs_command' \\
    -s h -l help -d 'Show help message'
'''


def install_completions() -> bool:
    """Install fish completions to user's config directory."""
    try:
        FISH_COMPLETIONS_DIR.mkdir(parents=True, exist_ok=True)
        completions = generate_fish_completions()
        COMPLETIONS_FILE.write_text(completions)
        print(f"✅ Fish completions installed to: {COMPLETIONS_FILE}")
        return True
    except Exception as e:
        print(f"❌ Failed to install completions: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install_completions()
    else:
        print(generate_fish_completions())