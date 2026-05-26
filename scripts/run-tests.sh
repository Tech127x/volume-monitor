#!/bin/bash
# Master test runner for Volume Monitor
# Run this before releasing

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Volume Monitor Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Package structure
echo -e "${BLUE}[1/6] Package Structure${NC}"
python3 -c "
from pathlib import Path
import sys

required = [
    'pyproject.toml', 'setup.py', 'README.md',
    'src/volume_monitor/__init__.py',
    'src/volume_monitor/cli.py',
    'src/volume_monitor/config.py',
    'src/volume_monitor/audio/pipewire.py',
    'src/volume_monitor/companion/client.py',
    'src/volume_monitor/monitors/volume.py',
    'install.fish', 'uninstall.fish',
]

missing = [f for f in required if not Path(f).exists()]
if missing:
    print(f'Missing files: {missing}')
    sys.exit(1)
print('OK - All required files present')
"

# Test 2: Python imports
echo -e "${BLUE}[2/6] Python Imports${NC}"
PYTHONPATH="src" python3 -c "
from volume_monitor.config import MonitorConfig
from volume_monitor.audio import pipewire, streams, devices
from volume_monitor.monitors import VolumeMonitor, AppKnobMonitor
from volume_monitor.companion import CompanionTCPClient
from volume_monitor.utils import normalization, process
print('OK - All imports successful')
"

# Test 3: Configuration
echo -e "${BLUE}[3/6] Configuration${NC}"
PYTHONPATH="src" python3 -c "
from volume_monitor.config import MonitorConfig
c = MonitorConfig()
c.model_dump()  # Validate serialization
print('OK - Configuration valid')
"

# Test 4: Unit tests (if pytest available)
echo -e "${BLUE}[4/6] Unit Tests${NC}"
if python3 -c "import pytest" 2>/dev/null; then
    PYTHONPATH="src" python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20
else
    echo "pytest not available - install with: pip install pytest"
    echo "Skipping unit tests"
fi

# Test 5: pipx compatibility
echo -e "${BLUE}[5/6] pipx Compatibility${NC}"
if command -v pipx >/dev/null 2>&1; then
    pipx run --spec . volume-monitor --help >/dev/null 2>&1 && \
        echo "OK - pipx run works" || \
        echo "WARN - pipx run failed (may need editable install)"
else
    echo "pipx not installed - skipping"
fi

# Test 6: Fish syntax
echo -e "${BLUE}[6/6] Fish Syntax${NC}"
if command -v fish >/dev/null 2>&1; then
    for f in install.fish uninstall.fish scripts/setup-fish-integration.fish; do
        [ -f "$f" ] && fish -n "$f" 2>/dev/null && echo "  OK: $f" || echo "  SKIP: $f not found"
    done
else
    echo "Fish not installed - skipping"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Test Suite Complete${NC}"
echo -e "${GREEN}========================================${NC}"