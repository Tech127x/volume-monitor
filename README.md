# 🎛️ Volume Monitor for BitFocus Companion

Real-time audio control at your fingertips -- finally, a volume knob that just works.

You're sitting at your computer, headphones on. A new browser tab blasts audio at 100%. You scramble for the volume control. Your Bluetooth headphones disconnected and now audio is coming out of the wrong speakers. You have three apps playing sound and no way to control them individually.

Volume Monitor fixes all of this. It connects your Linux audio system directly to your Stream Deck+, turning those beautiful knobs into intelligent, app-aware volume controls that adapt to whatever you're doing.

---

## ✨ What Makes This Different?

### 🎯 It Knows What's Playing
Volume Monitor doesn't just control "the volume" -- it sees every app making sound. Firefox playing YouTube? That's Knob 2. Spotify in the background? Knob 3. Discord call comes in? Knob 4. Each app gets its own knob, automatically. Close an app and the others shift left to fill the gap. It's like having a dedicated mixing board for your desktop.

### 🔄 Never Get Blasted Again
New app you've never opened before? It starts at 50% volume -- not 100%. No more panic-reaching for the mute button. Close an app and reopen it later? It remembers exactly where you left it. Firefox always comes back at 32% because that's where you like it. Every app remembers its own level.

### 🎧 Switch Devices Instantly
Headphones, speakers, HDMI output, Bluetooth earbuds -- Volume Monitor sees them all. Press one button on your Stream Deck (or run one command) and your audio jumps to the next device. Walking away from your desk? One tap switches from speakers to headphones. Desktop notifications confirm every switch so you always know where your audio is going.

### 🐟 Built for CachyOS, Loves All Shells
First-class Fish shell support with tab completions, handy aliases (vm, vms, vml, vmt), and automatic PATH configuration. But don't worry bash and zsh users -- it all works beautifully for you too. The installer auto-detects your shell and sets everything up.

### ⚡ Real-Time, Always
30ms polling means volume changes appear on your Stream Deck instantly. Not "pretty fast" -- instantly. Turn a physical knob on a Stream Deck+ and watch the volume change before your finger leaves the dial.

---

## 🚀 Quick Install

Fish Shell (CachyOS default):
```
  sudo pacman -S python-pipx wireplumber pipewire-pulse libnotify
  pipx ensurepath
  fish_add_path ~/.local/bin
  git clone https://github.com/Tech127x/volume-monitor.git
  cd volume-monitor
  fish install.fish
```

Bash / Zsh:
```
  sudo pacman -S python-pipx wireplumber pipewire-pulse libnotify
  pipx ensurepath
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  git clone https://github.com/Tech127x/volume-monitor.git
  cd volume-monitor
  ./install.sh
```
That's it. The installer handles everything -- pipx setup, shell configuration, Fish completions, optional systemd service, and walks you through your first configuration.

### Systemd Service (Auto-Start on Boot)

  scripts/install-service.sh

Installs a user-level systemd service that starts Volume Monitor automatically when you log in.
View logs: journalctl --user -u volume-monitor -f

---

## 🎮 Usage -- So Simple You'll Forget It's Running

  volume-monitor --start          Start in background
  volume-monitor --status         Check if running
  volume-monitor --list-devices   See all your audio devices
  volume-monitor --toggle         Switch to next audio device
  volume-monitor --list-streams   See what apps are making sound
  volume-monitor --configure      Change any setting interactively

Fish Shell Aliases:

  vm     volume-monitor
  vms    volume-monitor --status
  vml    volume-monitor --list-devices
  vmt    volume-monitor --toggle
  vmc    volume-monitor --configure
  vma    volume-monitor --list-streams

---

## 📋 What You'll See On Your Stream Deck+

Knob 1 -- Master Volume
Shows your current audio device name and volume. Turn it to adjust everything. Press to mute/unmute. When you switch audio devices, the name updates automatically and you get a desktop notification.

Knobs 2-4 -- Per-App Volume (Optional)
Each knob auto-assigns to an app that's playing audio. The display shows the app name and current volume. Turn to adjust just that app. Close the app and the remaining apps shift left -- your most important stuff stays on the leftmost knobs.

Examples: Brave: YouTube, Spotify, Discord, any Steam/Proton game

Built-In Smarts:

Ghost stream protection: Brave sometimes creates temporary audio streams that disappear after 13 seconds. Volume Monitor ignores them so you never see phantom entries.

Volume memory: Close Firefox at 64% and reopen it -- it comes back at 64%. Every app remembers its level individually.

Safe defaults: Brand new apps start at 50% volume. Never get startled by a surprise 100% blast again.

---

## 🔧 Configuration

Run the friendly interactive wizard:

  volume-monitor --configure

It walks you through:
  🔵 Bluetooth check — reminds you to connect devices before scanning
  🔌 Companion connection — IP and port settings
  🔔 Notifications — desktop alerts when devices switch
  🔄 Toggle setup — pick which devices to cycle through
  🎛️ App knobs — enable/disable, set default volume for new apps
  📋 Companion variable guide — shows exactly which variables to create

Config is stored at ~/.volume_monitor_config.json

### Systemd Service (Optional)

  bash scripts/install-service.sh

Enables auto-start on login so Volume Monitor is always running.

---

## 🎛️ Stream Deck+ Variable Setup

Create these Custom Variables in Companion:

Knob 1 -- Master:
  knob1_label, knob1_volume, knob1_dial_pct, knob1_muted, knob1_stream_id, knob1_active

Knobs 2-4 -- Per-App (optional):
  knob2_label through knob4_label
  knob2_volume through knob4_volume
  knob2_dial_pct through knob4_dial_pct
  knob2_muted through knob4_muted
  knob2_stream_id through knob4_stream_id

---

## 📊 Requirements

  Python 3.9+, pipx, WirePlumber, pipewire-pulse, libnotify (optional)

---

## 🆘 Troubleshooting

  No devices: systemctl --user status pipewire
  Companion won't connect: Check TCP API on port 16759
  Volume not updating: volume-monitor --start-foreground --debug
  Command not found (Fish): fish_add_path ~/.local/bin
  Command not found (Bash): export PATH="$HOME/.local/bin:$PATH"

---

## 📦 Updating

  cd ~/volume-monitor
  git pull
  pipx install --force --editable .
  volume-monitor --start

## 🗑️ Uninstall

  fish uninstall.fish

## 📚 Documentation

- [Configuration Guide](docs/CONFIGURATION.md) — All settings explained
- [Usage Guide](docs/USAGE.md) — Commands and workflows
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Common issues and fixes
- [CachyOS Fish Setup](docs/CACHYOS_FISH_SETUP.md) — Fish-specific install notes
- [Companion Setup](docs/COMPANION_SETUP.md) — Variable setup for Stream Deck+
- [Contributing](CONTRIBUTING.md) — How to help improve the project

## 📝 License

  MIT -- use it, modify it, share it... Just give credit!

---

Made with ❤️ for the CachyOS community, Bitfocus Companion users, and Stream Deck enthusiasts everywhere!
