#!/bin/bash
# Run tests inside the pipx virtual environment
# This ensures the package works correctly when installed via pipx

set -e

echo "========================================"
echo "  Testing inside pipx environment"
echo "========================================"
echo ""

# Find the pipx venv for volume-monitor
PIPX_VENV=""

# Check common locations
for path in \
    "$HOME/.local/pipx/venvs/volume-monitor" \
    "$HOME/.local/share/pipx/venvs/volume-monitor" \
    "$HOME/.pipx/venvs/volume-monitor"; do
    if [ -d "$path" ]; then
        PIPX_VENV="$path"
        break
    fi
done

if [ -z "$PIPX_VENV" ]; then
    echo "Volume Monitor not installed via pipx."
    echo "Install first: pipx install --editable ."
    echo ""
    echo "Or run standalone tests:"
    echo "  bash scripts/test-pipx-install.sh"
    exit 1
fi

echo "Found pipx venv: $PIPX_VENV"
echo ""

# Activate the venv and run tests
echo "Running Python tests inside pipx environment..."
"$PIPX_VENV/bin/python" -c "
import volume_monitor
print(f'Volume Monitor version: {volume_monitor.__version__}')
print(f'Package location: {volume_monitor.__file__}')
print('')

# Test imports
from volume_monitor.config import MonitorConfig
from volume_monitor.audio.pipewire import clamp_volume_percent
from volume_monitor.utils.normalization import normalize_name

# Quick functional tests
config = MonitorConfig()
assert config.companion_port == 16759, 'Default port mismatch'

assert clamp_volume_percent(50) == 50
assert clamp_volume_percent(150) == 100
assert clamp_volume_percent(-10) == 0

assert normalize_name('Firefox') == 'firefox'
assert normalize_name('  Chrome  ') == 'chrome'

print('All checks passed!')
"

echo ""
echo "Testing CLI entry point..."
"$PIPX_VENV/bin/volume-monitor" --help >/dev/null && echo "  CLI: OK" || echo "  CLI: FAILED"

echo ""
echo "Done."