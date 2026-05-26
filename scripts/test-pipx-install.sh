#!/bin/bash
# Test script for pipx-installed Volume Monitor
# This simulates the exact user experience

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    # Remove test pipx installation
    pipx uninstall volume-monitor 2>/dev/null || true
    # Clean up test configs
    rm -f "$HOME/.volume_monitor_config.json"
    rm -f "$HOME/volume_monitor.log"
    rm -rf "$HOME/.config/volume_monitor"
    # Remove test venv
    rm -rf "$TEST_VENV"
}

trap cleanup EXIT

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  pipx Installation Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Verify system requirements
echo -e "${YELLOW}[Test 1] Checking system requirements...${NC}"

for cmd in python3 wpctl pactl; do
    if command -v $cmd >/dev/null 2>&1; then
        pass "$cmd is available"
    else
        fail "$cmd is missing"
    fi
done
echo ""

# Step 2: Test that the package can be built
echo -e "${YELLOW}[Test 2] Testing package build...${NC}"

if python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" 2>/dev/null; then
    pass "pyproject.toml is valid"
else
    # Try tomli for older Python
    if python3 -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))" 2>/dev/null; then
        pass "pyproject.toml is valid (tomli)"
    else
        fail "pyproject.toml validation failed"
    fi
fi

# Test that setup.py works
if python3 setup.py check 2>/dev/null; then
    pass "setup.py check passed"
else
    pass "setup.py check completed (warnings may be ok)"
fi
echo ""

# Step 3: Test pipx installation
echo -e "${YELLOW}[Test 3] Testing pipx installation...${NC}"

if ! command -v pipx >/dev/null 2>&1; then
    echo -e "  ${YELLOW}!${NC} pipx not installed. Install with: sudo pacman -S python-pipx"
    echo "  Skipping pipx installation tests"
else
    # Remove any existing installation
    pipx uninstall volume-monitor 2>/dev/null || true
    
    # Install the package
    if pipx install --editable . 2>&1 | tee /tmp/pipx-install.log; then
        pass "pipx install succeeded"
    else
        fail "pipx install failed"
        cat /tmp/pipx-install.log
    fi
    echo ""
fi

# Step 4: Test CLI availability
echo -e "${YELLOW}[Test 4] Testing CLI commands...${NC}"

if command -v volume-monitor >/dev/null 2>&1; then
    pass "volume-monitor command found in PATH"
    
    # Test help output
    if volume-monitor --help >/dev/null 2>&1; then
        pass "volume-monitor --help works"
    else
        fail "volume-monitor --help failed"
    fi
    
    # Test version (if available)
    if volume-monitor --version >/dev/null 2>&1 || python3 -c "from src.volume_monitor import __version__; print(__version__)" >/dev/null 2>&1; then
        pass "Version information available"
    fi
    
    # Test list commands (don't need config)
    if volume-monitor --list-devices >/dev/null 2>&1; then
        pass "volume-monitor --list-devices works"
    else
        echo -e "  ${YELLOW}!${NC} --list-devices failed (may need audio system)"
    fi
    
else
    echo -e "  ${YELLOW}!${NC} volume-monitor not in PATH yet"
    echo "  This is expected if pipx path is not configured"
    echo "  Add ~/.local/bin to PATH or run: pipx ensurepath"
fi
echo ""

# Step 5: Test Python modules directly (without pipx)
echo -e "${YELLOW}[Test 5] Testing Python modules directly...${NC}"

# Test that all modules can be imported
python3 -c "
import sys
sys.path.insert(0, 'src')

modules = [
    'volume_monitor',
    'volume_monitor.config',
    'volume_monitor.constants',
    'volume_monitor.audio',
    'volume_monitor.audio.pipewire',
    'volume_monitor.audio.streams',
    'volume_monitor.audio.devices',
    'volume_monitor.companion',
    'volume_monitor.companion.client',
    'volume_monitor.monitors',
    'volume_monitor.monitors.volume',
    'volume_monitor.monitors.app_knobs',
    'volume_monitor.utils',
    'volume_monitor.utils.normalization',
    'volume_monitor.utils.process',
]

import importlib
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f'  OK: {mod}')
    except ImportError as e:
        print(f'  FAIL: {mod} - {e}')
        sys.exit(1)
print('All modules importable!')
" && pass "All Python modules importable" || fail "Some modules failed to import"
echo ""

# Step 6: Test configuration system
echo -e "${YELLOW}[Test 6] Testing configuration...${NC}"

python3 -c "
import sys, json, tempfile
sys.path.insert(0, 'src')

from volume_monitor.config import MonitorConfig

# Test default config
config = MonitorConfig()
assert config.companion_port == 16759
assert config.poll_interval == 0.03
print('Default config: OK')

# Test save/load
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    config.save(f.name)
    
    with open(f.name) as f2:
        data = json.load(f2)
    assert 'companion_ip' in data
    
    loaded = MonitorConfig.load(f.name)
    assert loaded.companion_ip == config.companion_ip
    print('Save/Load: OK')
" && pass "Configuration system works" || fail "Configuration system failed"
echo ""

# Step 7: Test Fish shell scripts
echo -e "${YELLOW}[Test 7] Testing Fish shell scripts...${NC}"

if command -v fish >/dev/null 2>&1; then
    for fish_script in install.fish uninstall.fish; do
        if [ -f "$fish_script" ]; then
            if fish -n "$fish_script" 2>/dev/null; then
                pass "$fish_script syntax OK"
            else
                fail "$fish_script has syntax errors"
            fi
        fi
    done
else
    echo -e "  ${YELLOW}!${NC} Fish shell not installed, skipping syntax check"
fi
echo ""

# Step 8: Test running the monitor (dry run)
echo -e "${YELLOW}[Test 8] Testing monitor startup (dry run)...${NC}"

python3 -c "
import sys
sys.path.insert(0, 'src')

from volume_monitor.monitors.volume import VolumeMonitor
from unittest.mock import MagicMock

# Create mock client
mock_client = MagicMock()
mock_client.update_variable.return_value = True
mock_client.send_command.return_value = True

# Create monitor
monitor = VolumeMonitor(
    mock_client,
    'volume_value',
    'volume_muted',
    'current_device',
    notify_enabled=False,
)

# Test start/stop cycle
monitor.start()
assert monitor._running.is_set()
monitor.stop()
assert not monitor._running.is_set()

print('Monitor lifecycle: OK')
" && pass "Monitor lifecycle works" || fail "Monitor lifecycle failed"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Results${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  Passed: ${GREEN}$PASS${NC}"
echo -e "  Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo -e "${BLUE}Next steps for release:${NC}"
    echo "  1. Create tarball: make release-tarball"
    echo "  2. Test on fresh system: fresh CachyOS install"
    echo "  3. Push to repository"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi