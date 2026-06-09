#!/bin/bash

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Uninstall Volume Monitor systemd service
set -e

echo "Uninstalling Volume Monitor systemd service..."

systemctl --user stop volume-monitor.service 2>/dev/null || true
systemctl --user disable volume-monitor.service 2>/dev/null || true

SERVICE_FILE="$HOME/.config/systemd/user/volume-monitor.service"
rm -f "$SERVICE_FILE"

systemctl --user daemon-reload

echo "Service uninstalled."