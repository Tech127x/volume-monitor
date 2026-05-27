# BitFocus Companion Setup Guide

## Required Variables

Create these **Custom Variables** in Companion's Variables tab:

### Knob 1 — Master Volume

| Variable | Type | Purpose |
|----------|------|---------|
| `knob1_label` | String | Device name shown on display |
| `knob1_volume` | String | Volume number (0-100) |
| `knob1_dial_pct` | String | Controls dial ring position |
| `knob1_muted` | Boolean | Mute indicator |
| `knob1_stream_id` | String | Internal (can be hidden) |
| `knob1_active` | Boolean | Device connected indicator |

### Knobs 2-4 — Per-App Volume

Create the same set for knobs 2, 3, and 4:

| Variable | Purpose |
|----------|---------|
| `knob2_label` through `knob4_label` | App name |
| `knob2_volume` through `knob4_volume` | Volume number |
| `knob2_dial_pct` through `knob4_dial_pct` | Dial ring |
| `knob2_muted` through `knob4_muted` | Mute state |
| `knob2_stream_id` through `knob4_stream_id` | Internal |

## Button Setup Example

### Master Volume Knob

1. Add a **Knob** action
2. Set dial to use variable: `$(custom:knob1_dial_pct)`
3. Set display text to: `$(custom:knob1_label)\n$(custom:knob1_volume)%`
4. Add press action: Mute toggle (use `knob1_muted`)

### App Volume Knob

1. Add a **Knob** action
2. Set dial to use variable: `$(custom:knob2_dial_pct)`
3. Set display text to: `$(custom:knob2_label)\n$(custom:knob2_volume)%`
4. Add press action: Mute toggle (use `knob2_muted`)

### Toggle Device Button

1. Add a **Button** action
2. Set to run: `volume-monitor --toggle`
3. Display: `$(custom:knob1_label)`

## Displaying -- for Zero Volume

In Companion, use a boolean expression in your button text:

$(custom:knob2_volume) "0"?"−−":(custom:knob2_volume) "0"?"−−":(custom:knob2_volume)
