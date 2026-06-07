# Volume Monitor — Companion Module

Display per-app icons on your Stream Deck+ based on Volume Monitor's knob labels.

## Method 1 (recommended) — Image Library + Expressions

No module needed — pure Companion. For each knob button:

1. Upload icons to Companion's **Image Library** and rename each one's **name** field to match the app (e.g. `floorp`, `brave`, `spotify`)
2. On the button, add a **Local Variable**:  
   - Local variable type: `internal:evaluate expression`
   - Name: `app_name`  
   - Expression: `toLowerCase(replaceAll(split($(custom:knob2_label), ": ")[0], '"', ''))`  
3. In the button's **Style → Image** tab, set **Content > Image > expression** to:
   ```
   getVariable('image', $(local:app_name))
   ```

Done. Companion pulls the image from its own library by name. No module, no filesystem.

## Method 2 — Companion Module (filesystem icons)

For users who prefer PNG files on disk or want to avoid expressions:

1. [Install the module](#installation)
2. Create the config file so the module knows where your icons live:
   ```bash
   echo '{"path": "'$HOME'/.volume-monitor-icons"}' > ~/.config/companion/volume-monitor-icons-path.json
   ```
3. Drop PNGs named after each app into `~/.volume-monitor-icons/`:
   ```
   ~/.volume-monitor-icons/
   ├── floorp.png
   ├── brave.png
   ├── firefox.png
   ├── spotify.png
   └── ...
   ```
   The directory is auto-created if it doesn't exist.
4. Add a **Show app icon for Knob 2** feedback to any button.

Icons are checked first from your custom directory, then from the module's bundled `icons/` folder.

### Installation

```bash
cp -r companion-module-volume-monitor ~/.config/companion/v5.0/modules/
cd ~/.config/companion/v5.0/modules/companion-module-volume-monitor
npm install --omit=dev
```

Enable developer mode in Companion's config (`~/.config/companion/config.json`):
```json
{
  "enable_developer": true,
  "dev_modules_path": "/home/sean/.config/companion/v5.0/modules"
}
```

Then restart Companion.
