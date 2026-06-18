#!/usr/bin/env fish

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Volume Monitor Uninstallation Script (Fish Shell)

set -l RED (set_color red)
set -l GREEN (set_color green)
set -l YELLOW (set_color yellow)
set -l NC (set_color normal)

echo "$YELLOW Uninstalling Volume Monitor...$NC"
echo ""

# Stop and remove systemd service if exists
if systemctl --user is-active volume-monitor.service &>/dev/null
    echo "  Stopping systemd service..."
    systemctl --user stop volume-monitor.service
    systemctl --user disable volume-monitor.service
end

set -l SERVICE_FILE "$HOME/.config/systemd/user/volume-monitor.service"
if test -f "$SERVICE_FILE"
    echo "  Removing systemd service file..."
    rm -f "$SERVICE_FILE"
    systemctl --user daemon-reload
end

# Stop any running instances
if pgrep -f "volume-monitor" > /dev/null
    echo "  Stopping running instances..."
    pkill -f "volume-monitor" 2>/dev/null; or true
end

# Uninstall via pipx
if command -v pipx >/dev/null 2>&1
    if pipx list 2>/dev/null | grep -q "volume-monitor"
        echo "  Uninstalling package..."
        pipx uninstall volume-monitor
    end
end

# Clean up files
echo "  Cleaning up files..."
rm -f "$HOME/.volume_monitor_config.json"
rm -f "$HOME/volume_monitor.log"
rm -f "$HOME/.volume_monitor_app_volumes.json"
rm -rf "$HOME/.config/volume_monitor"

# Remove PID file if exists
set -l XDG_RUNTIME_DIR (echo $XDG_RUNTIME_DIR; or echo "/run/user/"(id -u))
rm -f "$XDG_RUNTIME_DIR/volume_monitor.pid"

# Remove Fish shell configurations
set -l FISH_CONFIG "$HOME/.config/fish/config.fish"
if test -f "$FISH_CONFIG"
    echo ""
    echo "$YELLOW Cleaning Fish shell configuration...$NC"
    
    # Create backup
    cp "$FISH_CONFIG" "$FISH_CONFIG.bak"
    echo "  Backed up config to config.fish.bak"
    
    # Remove Volume Monitor lines
    sed -i '/# Added by Volume Monitor installer/d' "$FISH_CONFIG"
    sed -i '/# Volume Monitor aliases/d' "$FISH_CONFIG"
    sed -i '/alias vm=/d' "$FISH_CONFIG"
    sed -i '/alias vms=/d' "$FISH_CONFIG"
    sed -i '/alias vml=/d' "$FISH_CONFIG"
    sed -i '/alias vmt=/d' "$FISH_CONFIG"
    sed -i '/alias vmc=/d' "$FISH_CONFIG"
    sed -i '/alias vma=/d' "$FISH_CONFIG"
    sed -i '/fish_add_path ~\/.local\/bin/d' "$FISH_CONFIG"
    
    echo "  Removed Volume Monitor aliases"
end

# Remove fish completions
set -l COMPLETIONS_FILE "$HOME/.config/fish/completions/volume-monitor.fish"
if test -f "$COMPLETIONS_FILE"
    rm -f "$COMPLETIONS_FILE"
    echo "  Removed Fish completions"
end

# Ask about prompt removal
set -l PROMPT_FILE "$HOME/.config/fish/functions/fish_prompt.fish"
if test -f "$PROMPT_FILE"
    echo ""
    echo "$YELLOW Volume Monitor prompt integration detected.$NC"
    read -P "Remove custom prompt? (y/N): " -l remove_prompt
    
    if test "$remove_prompt" = "y" -o "$remove_prompt" = "Y"
        rm -f "$PROMPT_FILE"
        # Restore backup if exists
        if test -f "$PROMPT_FILE.bak"
            mv "$PROMPT_FILE.bak" "$PROMPT_FILE"
            echo "  Restored backup prompt"
        end
        echo "  Removed Volume Monitor prompt integration"
    end
end

echo ""
echo "$GREEN Volume Monitor has been uninstalled.$NC"
echo ""
echo "Note: Your fish config was backed up to config.fish.bak"
echo ""
echo "Restart your shell: exec fish"