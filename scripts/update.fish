#!/usr/bin/env fish

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Volume Monitor Update Script (Fish)
# Use this to update an existing installation

set -l GREEN (set_color green)
set -l YELLOW (set_color yellow)
set -l BLUE (set_color blue)
set -l NC (set_color normal)

echo "$BLUE========================================$NC"
echo "$BLUE  Volume Monitor Updater$NC"
echo "$BLUE========================================$NC"
echo ""

# Check if pipx is available
if not command -v pipx &>/dev/null
    echo "Error: pipx is not installed."
    echo "Install with: sudo pacman -S python-pipx"
    exit 1
end

# Check if volume-monitor is installed
if not pipx list 2>/dev/null | grep -q "volume-monitor"
    echo "Volume Monitor is not installed via pipx."
    echo "Run the install script first: fish install.fish"
    exit 1
end

# Stop the running monitor
echo "$YELLOW Stopping running instance...$NC"
pkill -f volume-monitor 2>/dev/null; and echo "  Stopped."; or echo "  No running instance found."

# Update from current directory
echo "$YELLOW Updating package...$NC"
pipx install --force --editable . 2>&1 | grep -v "already seems"

# Restart
echo "$YELLOW Restarting...$NC"
volume-monitor --start

echo ""
echo "$GREEN========================================$NC"
echo "$GREEN  Update Complete!$NC"
echo "$GREEN========================================$NC"
echo ""
echo "Check status: volume-monitor --status"
echo "View logs: tail -f ~/volume_monitor.log"