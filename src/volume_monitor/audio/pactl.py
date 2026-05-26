"""PulseAudio pactl interaction functions."""
import logging
import re
import subprocess
from typing import Dict, List, Optional

from ..constants import PACTL_SINK_INPUT_RE, PACTL_EVENT_NEW_INPUT
from ..utils.normalization import normalize_name
from .pipewire import clamp_volume_percent
from .volume_cache import get_persisted_volume_for_props

logger = logging.getLogger(__name__)


def parse_pactl_sink_inputs() -> List[dict]:
    """Parse active sink-inputs from pactl."""
    entries: List[dict] = []
    current: dict = {}
    
    try:
        res = subprocess.run(
            ["pactl", "list", "sink-inputs"],
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
    except Exception as e:
        logger.debug(f"pactl list sink-inputs failed: {e}")
        return entries
    
    for line in res.stdout.splitlines():
        m = re.match(PACTL_SINK_INPUT_RE, line)
        if m:
            if current:
                entries.append(current)
            current = {"pactl_id": m.group(1), "props": {}}
            continue
        
        if not current or "=" not in line:
            continue
        
        key, _, val = line.strip().partition(" = ")
        current["props"][key.strip()] = val.strip().strip('"')
    
    if current:
        entries.append(current)
    
    return entries


def set_pactl_sink_input_volume_percent(pactl_id: str, percent: int) -> bool:
    """Set volume for a pactl sink input."""
    pct = clamp_volume_percent(percent)
    if pct is None:
        return False
    
    try:
        subprocess.run(
            ["pactl", "set-sink-input-volume", str(pactl_id), f"{pct}%"],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )
        return True
    except Exception as e:
        logger.debug(f"pactl set-sink-input-volume {pactl_id} {pct}%: {e}")
        return False