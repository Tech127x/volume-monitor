# Volume Monitor for BitFocus Companion

Real-time audio volume and device monitoring for BitFocus Companion on Linux systems using PipeWire/PulseAudio.

Designed for CachyOS with first-class Fish shell support.

## Features

- **Real-time volume monitoring** with configurable polling (30ms default)
- **Device switching detection** with desktop notifications
- **Per-application volume control** for Stream Deck+ knobs (2-4)
- **Automatic volume restoration** for frequently-restarted apps (Firefox, games)
- **Systemd service integration** for automatic startup
- **Fish shell completions and aliases** for quick commands
- **Comprehensive CLI** for management and configuration

## Quick Install

### Fish Shell (CachyOS default)

```fish
# 1. Install pipx (one-time)
sudo pacman -S python-pipx
pipx ensurepath
fish_add_path ~/.local/bin

# 2. Install Volume Monitor
git clone https://github.com/Tech127x/volume-monitor.git
cd volume-monitor
fish install.fish