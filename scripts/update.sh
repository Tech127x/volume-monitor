#!/bin/bash
# Volume Monitor Update Script
# Use this to update an existing installation

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Volume Monitor Updater${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if pipx is available
if ! command -v pipx &>/dev/null; then
    echo "Error: pipx is not installed."
    echo "Install with: sudo pacman -S python-pipx"
    exit 1
fi

# Check if volume-monitor is installed
if ! pipx list 2>/dev/null | grep -q "volume-monitor"; then
    echo "Volume Monitor is not installed via pipx."
    echo "Run the install script first: ./install.sh"
    exit 1
fi

# Stop the running monitor
echo -e "${YELLOW}Stopping running instance...${NC}"
pkill -f volume-monitor 2>/dev/null && echo "  Stopped." || echo "  No running instance found."

# Update from current directory
echo -e "${YELLOW}Updating package...${NC}"
pipx install --force --editable . 2>&1 | grep -v "already seems"

# Restart
echo -e "${YELLOW}Restarting...${NC}"
volume-monitor --start

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Check status: volume-monitor --status"
echo "View logs: tail -f ~/volume_monitor.log"