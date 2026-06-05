#!/bin/bash
# Install Volume Monitor as a systemd user service
set -e

echo "Installing Volume Monitor systemd service..."

SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/volume-monitor.service" "$SERVICE_DIR/volume-monitor.service"

# Adjust the ExecStart path if volume-monitor is in PATH
if ! command -v volume-monitor &>/dev/null; then
    sed -i "s|%h/.local/bin/volume-monitor|$HOME/.local/bin/volume-monitor|g" "$SERVICE_DIR/volume-monitor.service"
fi

echo "Service file installed at $SERVICE_DIR/volume-monitor.service"

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable volume-monitor.service
systemctl --user start volume-monitor.service

echo "Service installed and started!"
echo ""
echo "Useful commands:"
echo "  systemctl --user status volume-monitor"
echo "  systemctl --user stop volume-monitor"
echo "  systemctl --user restart volume-monitor"
echo "  journalctl --user -u volume-monitor -f"
