#!/bin/sh

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Volume Monitor Installation Script
# Auto-detects shell and runs appropriate installer

# Detect current shell
detect_shell() {
    if [ -n "$SHELL" ]; then
        basename "$SHELL"
    elif [ -n "$FISH_VERSION" ]; then
        echo "fish"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    else
        echo "sh"
    fi
}

SHELL_TYPE=$(detect_shell)

echo "Detected shell: $SHELL_TYPE"
echo ""

case "$SHELL_TYPE" in
    fish)
        echo "Running Fish shell installer..."
        if command -v fish >/dev/null 2>&1; then
            fish install.fish
        else
            echo "Error: Fish shell not found. Please run: fish install.fish"
            exit 1
        fi
        ;;
    bash|zsh|sh)
        echo "Running POSIX shell installer..."
        if [ -f "install-posix.sh" ]; then
            sh install-posix.sh
        else
            echo "Error: install-posix.sh not found"
            exit 1
        fi
        ;;
    *)
        echo "Unknown shell: $SHELL_TYPE"
        echo "Please run the appropriate installer:"
        echo "  For Fish:  fish install.fish"
        echo "  For Bash:  bash install-posix.sh"
        exit 1
        ;;
esac