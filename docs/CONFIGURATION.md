# Configuration Reference

All settings are stored in `~/.volume_monitor_config.json`.

## Complete Options

| Option | Default | Description |
|--------|---------|-------------|
| `companion_ip` | `127.0.0.1` | Companion server address |
| `companion_port` | `16759` | Companion TCP port |
| `device_id` | `python_volume_monitor` | Device identifier |
| `volume_var` | `volume_value` | Companion variable for volume |
| `mute_var` | `volume_muted` | Companion variable for mute |
| `device_var` | `current_device` | Companion variable for device name |
| `poll_interval` | `0.03` | How often to check volume (seconds) |
| `notify_on_switch` | `true` | Show desktop notification on device switch |
| `toggle_devices` | `[]` | Device patterns to include (empty = all) |
| `exclude_devices` | `[]` | Device patterns to exclude |
| `enable_app_knobs` | `false` | Enable per-app volume knobs |
| `exclude_apps` | `[...]` | Apps to hide from knobs |
| `app_knob_poll_interval` | `0.1` | App knob polling rate |
| `default_new_app_volume` | `50` | Volume for never-seen apps (0-100) |

## Example Config

```json
{
    "companion_ip": "127.0.0.1",
    "companion_port": 16759,
    "notify_on_switch": true,
    "toggle_devices": ["Sound Blaster*", "*Q30*"],
    "exclude_devices": ["*HDMI*"],
    "enable_app_knobs": true,
    "default_new_app_volume": 50
}
Device Patterns
Use wildcards to match device names:

"Sound Blaster*" — matches "Sound Blaster G8", "Sound Blaster X4", etc.

"*HDMI*" — matches any device with "HDMI" in the name

"*" — matches everything
