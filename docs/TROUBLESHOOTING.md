# Troubleshooting

## No Audio Devices Detected

```
systemctl --user status pipewire
wpctl status
```

## Companion Won't Connect
Open Companion → Settings → TCP API

Ensure TCP API is Enabled on port 16759

Verify IP matches your config

## Volume Not Updating On Stream Deck

# Check if monitor is running
volume-monitor --status

# View live logs
tail -f ~/volume_monitor.log

# Run in foreground with debug
volume-monitor --start-foreground --debug
Command Not Found
Fish Shell
fish
fish_add_path ~/.local/bin
echo 'fish_add_path ~/.local/bin' >> ~/.config/fish/config.fish
exec fish

export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Ghost Duplicate Streams (Brave/Chromium)
Brave and Chromium browsers sometimes create temporary audio streams on YouTube that disappear after ~13 seconds. This is a known browser bug. If you see duplicate entries briefly, they will clear automatically.

# App Knobs Not Showing
Ensure enable_app_knobs is true in config

Create all required Companion variables (knob2_* through knob4_*)

Check excluded apps list doesn't include your app

# Clean Reinstall

volume-monitor --stop
pipx uninstall volume-monitor
rm -f ~/.volume_monitor_config.json ~/volume_monitor.log
rm -rf ~/.config/volume_monitor
cd ~/volume-monitor
pipx install --force --editable .
volume-monitor --configure
volume-monitor --start
