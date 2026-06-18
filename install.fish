#!/usr/bin/env fish

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Volume Monitor Installation Script (Fish Shell)
# Installs via pipx for easy management
# 

# Colors for output
set -l RED (set_color red)
set -l GREEN (set_color green)
set -l YELLOW (set_color yellow)
set -l BLUE (set_color blue)
set -l BOLD (set_color --bold)
set -l NC (set_color normal)

echo "$BLUE======================================$NC"
echo "$BLUE  Volume Monitor Installation$NC"
echo "$BLUE======================================$NC"
echo ""

# Function to check if a command exists
function command_exists
    command -v $argv[1] >/dev/null 2>&1
end

# Function to print status
function print_status
    if test $argv[1] -eq 0
        echo "  $GREEN✓$NC $argv[2]"
    else
        echo "  $RED✗$NC $argv[2]"
    end
end

# Detect shell and set config file
set -l SHELL_CONFIG ""
switch (basename $SHELL)
    case fish
        set SHELL_CONFIG "$HOME/.config/fish/config.fish"
    case bash
        set SHELL_CONFIG "$HOME/.bashrc"
    case zsh
        set SHELL_CONFIG "$HOME/.zshrc"
    case '*'
        set SHELL_CONFIG "$HOME/.profile"
end

echo "$YELLOWDetected shell: $(basename $SHELL)$NC"
echo ""

# Check for required system packages
echo "$YELLOWChecking system requirements...$NC"

set -l REQUIRED_COMMANDS wpctl pactl python3
set -l MISSING_COMMANDS

for cmd in $REQUIRED_COMMANDS
    if command_exists $cmd
        print_status 0 "$cmd found"
    else
        print_status 1 "$cmd not found"
        set -a MISSING_COMMANDS $cmd
    end
end

# Check for optional notify-send
if command_exists notify-send
    print_status 0 "notify-send found"
else
    print_status 1 "notify-send not found (notifications disabled)"
end

# Check for wpctl specifically (part of wireplumber)
if not command_exists wpctl
    echo ""
    echo "$RED Error: wpctl not found. Please install wireplumber:$NC"
    echo "  sudo pacman -S wireplumber"
    exit 1
end

# Check for pactl specifically (part of pipewire-pulse)
if not command_exists pactl
    echo ""
    echo "$RED Error: pactl not found. Please install pipewire-pulse:$NC"
    echo "  sudo pacman -S pipewire-pulse"
    exit 1
end

echo ""

# Check for pipx
echo "$YELLOWChecking for pipx...$NC"
if not command_exists pipx
    echo "$RED pipx is not installed.$NC"
    echo ""
    echo "pipx is required to install Volume Monitor."
    echo ""
    
    if test -f /etc/arch-release
        echo "Install pipx with:"
        echo "  sudo pacman -S python-pipx"
        echo ""
        echo "Then run:"
        echo "  pipx ensurepath"
        echo ""
        
        # For fish shell, add pipx path
        if test (basename $SHELL) = "fish"
            echo "For Fish shell, add pipx to PATH:"
            echo "  fish_add_path ~/.local/bin"
            echo "  # Or add to config.fish:"
            echo "  echo 'set -gx PATH ~/.local/bin \$PATH' >> ~/.config/fish/config.fish"
        end
    else
        echo "Install pipx from: https://pipx.pypa.io/stable/installation/"
    end
    
    exit 1
end

print_status 0 "pipx is installed"

# Check if pipx path is in PATH
if not echo $PATH | grep -q ".local/bin"
    echo ""
    echo "$YELLOW Adding ~/.local/bin to PATH...$NC"
    
    # Ensure pipx path is added
    pipx ensurepath
    
    # Fish-specific path handling
    if test (basename $SHELL) = "fish"
        # Create fish config directory if it doesn't exist
        mkdir -p ~/.config/fish
        
        # Add to fish config if not already there
        if not grep -q "~/.local/bin" ~/.config/fish/config.fish 2>/dev/null
            echo "" >> ~/.config/fish/config.fish
            echo "# Added by Volume Monitor installer" >> ~/.config/fish/config.fish
            echo "fish_add_path ~/.local/bin" >> ~/.config/fish/config.fish
            echo "" >> ~/.config/fish/config.fish
        end
        
        echo "$YELLOW Please run: exec fish (or restart your terminal)$NC"
    end
end

echo ""

# Install Volume Monitor
echo "$YELLOWInstalling Volume Monitor...$NC"

# Check if we're in the package directory
if not test -f "pyproject.toml"
    echo "$RED Error: pyproject.toml not found.$NC"
    echo "Please run this script from the Volume Monitor package directory."
    exit 1
end

# Install via pipx
echo "  Installing package..."
pipx install --force --editable .

if test $status -eq 0
    print_status 0 "Package installed successfully"
else
    print_status 1 "Package installation failed"
    exit 1
end

echo ""

# Post-installation setup
echo "$YELLOWPost-installation setup...$NC"

# Ensure log directory exists
mkdir -p ~/.config/volume_monitor
print_status 0 "Created config directory"

# Check if configuration exists
if not test -f "$HOME/.volume_monitor_config.json"
    echo ""
    echo "$YELLOWNo configuration found. Running configuration wizard...$NC"
    
    # Ensure volume-monitor is available
    if command_exists volume-monitor
        volume-monitor --configure
    else
        echo "$RED Cannot find volume-monitor command. Please restart your shell and run:$NC"
        echo "  volume-monitor --configure"
    end
end

print_status 0 "Configuration ready"

echo ""

# Ask about service installation
echo "$YELLOWService Installation$NC"
echo ""
echo "You can optionally install Volume Monitor as a systemd service"
echo "to start automatically on login."
echo ""

read -P "Install as systemd service? (y/N): " -l install_service

if test "$install_service" = "y" -o "$install_service" = "Y"
    # Create systemd service
    set -l SERVICE_DIR "$HOME/.config/systemd/user"
    mkdir -p $SERVICE_DIR
    
    # Find pipx binary location
    set -l VOLUME_MONITOR_BIN (which volume-monitor 2>/dev/null; or echo "$HOME/.local/bin/volume-monitor")
    
    # Create service file using fish's heredoc-like syntax
    echo "[Unit]
Description=Volume Monitor for BitFocus Companion
After=pipewire.service pipewire-pulse.service
Wants=pipewire.service

[Service]
Type=simple
ExecStart=$VOLUME_MONITOR_BIN --start-foreground
Restart=on-failure
RestartSec=5
Environment=\"PATH=$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin\"
Environment=\"XDG_RUNTIME_DIR=/run/user/%U\"

[Install]
WantedBy=default.target" > "$SERVICE_DIR/volume-monitor.service"
    
    systemctl --user daemon-reload
    systemctl --user enable volume-monitor.service
    systemctl --user start volume-monitor.service
    
    print_status 0 "Systemd service installed and started"
    
    echo ""
    echo "$BLUE Service commands:$NC"
    echo "  systemctl --user status volume-monitor  # Check status"
    echo "  systemctl --user stop volume-monitor    # Stop service"
    echo "  systemctl --user restart volume-monitor # Restart service"
    echo "  journalctl --user -u volume-monitor -f  # View logs"
else
    echo ""
    echo "$BLUE To start Volume Monitor manually:$NC"
    echo "  volume-monitor --start              # Start in background"
    echo "  volume-monitor --start-foreground   # Start in foreground"
end

echo ""
echo "$GREEN======================================$NC"
echo "$GREEN  Installation Complete!$NC"
echo "$GREEN======================================$NC"
echo ""
echo "$BLUE Quick commands:$NC"
echo "  volume-monitor --status         # Check if running"
echo "  volume-monitor --list-devices   # List audio devices"
echo "  volume-monitor --list-streams   # List app streams"
echo "  volume-monitor --toggle         # Switch audio device"
echo "  volume-monitor --configure      # Reconfigure"
echo "  volume-monitor --help           # Show all options"
echo ""

# Fish-specific aliases suggestion
if test (basename $SHELL) = "fish"
    echo "$BLUE Fish shell aliases (add to config.fish):$NC"
    echo "  alias vm='volume-monitor'"
    echo "  alias vms='volume-monitor --status'"
    echo "  alias vml='volume-monitor --list-devices'"
    echo "  alias vmt='volume-monitor --toggle'"
end

echo ""
echo "$BLUE Uninstall:$NC"
echo "  pipx uninstall volume-monitor"
echo ""