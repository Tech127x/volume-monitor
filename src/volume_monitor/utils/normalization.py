"""Name normalization utilities."""
import os
import re
from pathlib import Path


def normalize_name(s: str) -> str:
    """Normalize a string for comparison."""
    return " ".join(s.strip().split()).lower()


def norm_device_name(dev: str | None) -> str:
    """Normalize device name for display."""
    if not dev:
        return "Unknown"
    
    n = normalize_name(dev)
    
    # Known device name mappings
    device_map = {
        "g8": "Sound Blaster G8",
        "q30": "soundcore Q30",
        "sound blaster": "Sound Blaster G8",
    }
    
    for pattern, replacement in device_map.items():
        if pattern in n:
            return replacement
    
    # Strip parenthetical suffixes
    for sep in [" (", " on ", " – "]:
        if sep in dev:
            return dev.split(sep)[0].strip()
    
    return dev.strip()


def prettify_game_name(binary: str) -> str:
    """Convert a binary name to a prettified game name."""
    stem = Path(binary).stem
    stem = re.sub(r"\.exe$", "", stem, flags=re.I)
    stem = stem.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in stem.split())


def disambiguate_label(label: str, props: dict, used: set) -> str:
    """Create a unique label when there are duplicates."""
    if label not in used:
        return label
    
    media = props.get("media.name", "").strip()
    if media:
        short = media if len(media) <= 28 else media[:25] + "..."
        candidate = f"{label} — {short}"
        if candidate not in used:
            return candidate
    
    n = 2
    while f"{label} ({n})" in used:
        n += 1
    return f"{label} ({n})"


def is_excluded_app(app_name: str, exclude_apps: list) -> bool:
    """Check if an app name matches any exclusion patterns."""
    n = normalize_name(app_name)
    for pattern in exclude_apps:
        p = normalize_name(pattern)
        if p and (p in n or n in p):
            return True
    return False