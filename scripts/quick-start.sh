#!/bin/bash

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Quick start script for Volume Monitor
set -e

echo "======================================"
echo "Volume Monitor Quick Start"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install package
echo "Installing Volume Monitor..."
pip install -e .

# Configure
echo ""
echo "Running configuration wizard..."
volume-monitor --configure

# Ask about service installation
echo ""
read -p "Install as systemd service? (y/N): " install_service
if [[ "$install_service" =~ ^[Yy]$ ]]; then
    ./scripts/install-service.sh
fi

echo ""
echo "Installation complete!"
echo "Run 'volume-monitor --start' to start the monitor."