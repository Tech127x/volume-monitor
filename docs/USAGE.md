# Volume Monitor Usage Guide

## Starting & Stopping
volume-monitor --start              # Start in background (auto-restarts if already running)
volume-monitor --start-foreground   # Start in foreground (see live logs)
volume-monitor --stop               # Stop the monitor
volume-monitor --status             # Check if running
volume-monitor --restart            # Stop and restart


## Managing Audio Devices
volume-monitor --list-devices # Show all detected audio outputs
volume-monitor --toggle # Switch to next device in your toggle list


## Managing App Volumes
volume-monitor --list-streams # Show all apps currently playing audio


## Configuration
volume-monitor --configure # Interactive setup wizard (recommended)


## Fish Shell Shortcuts
vm # volume-monitor
vms # volume-monitor --status
vml # volume-monitor --list-devices
vmt # volume-monitor --toggle
vmc # volume-monitor --configure
vma # volume-monitor --list-streams


## What You See On Your Stream Deck+

### Knob 1 — Master Volume
- Turn: Adjust system volume
- Press: Mute/unmute
- Display shows current device name and volume

### Knobs 2-4 — App Volumes
- Each knob automatically controls one app's volume
- Apps are assigned in order they start playing
- When an app closes, others shift left to fill the gap
- Volume is remembered per app — reopen at same level

## Device Toggling

Press a button mapped to `volume-monitor --toggle` to cycle through your audio devices. Configure which devices in the toggle wizard.

## Logs
tail -f ~/volume_monitor.log # View live logs
volume-monitor --start-foreground --debug # Run with verbose output


## Updating
cd ~/volume-monitor
git pull
pipx install --force --editable .
volume-monitor --start
