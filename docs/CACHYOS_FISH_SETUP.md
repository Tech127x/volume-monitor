# CachyOS & Fish Shell Setup Guide

This guide covers the complete setup for Volume Monitor on CachyOS with Fish shell.

## Why Fish Shell?

CachyOS defaults to Fish shell, which provides:
- **Better autocompletions** - Tab completion is more intelligent
- **Syntax highlighting** - Commands are colored as you type
- **Easier configuration** - No need for complex bashrc files
- **Modern defaults** - Sensible defaults out of the box

## Installation

### Step 1: Install Dependencies

```fish
# Install required packages
sudo pacman -S python-pipx wireplumber pipewire-pulse libnotify

# Ensure pipx is in PATH
pipx ensurepath
fish_add_path ~/.local/bin