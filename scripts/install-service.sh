#!/bin/bash
# Install Volume Monitor as a systemd user service
set -e

echo "Installing Volume Monitor systemd service..."

SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/volume-monitor.service" << 'EOF'
[Unit]
Description=Volume Monitor for BitFocus Companion
After=pipewire.service pipewire-pulse.service
Wants=pipewire.service

[Service]
Type=simple
ExecStart=volume-monitor --start-foreground
Restart=on-failure
RestartSec=5
Environment="PATH=/usr/bin:/bin:/usr/sbin:/sbin"

[Install]
WantedBy=default.target
EOF

echo "Service file created at $SERVICE_DIR/volume-monitor.service"

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