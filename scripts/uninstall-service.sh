#!/bin/bash

# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor
# Uninstall Volume Monitor systemd service
set -e

echo "Uninstalling Volume Monitor systemd service..."

systemctl --user stop volume-monitor.service 2>/dev/null || true
systemctl --user disable volume-monitor.service 2>/dev/null || true

SERVICE_FILE="$HOME/.config/systemd/user/volume-monitor.service"
rm -f "$SERVICE_FILE"

systemctl --user daemon-reload

echo "Service uninstalled."