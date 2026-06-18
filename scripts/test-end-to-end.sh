#!/bin/bash

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# End-to-end test simulating a user downloading and using the package
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  End-to-End User Experience Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Create simulated download directory
echo -e "${YELLOW}[Step 1] Simulating download to ~/Downloads...${NC}"
TEST_HOME=$(mktemp -d)
DOWNLOADS="$TEST_HOME/Downloads"
mkdir -p "$DOWNLOADS"

# Create a tarball of the current project
cd "$(dirname "$0")/.."
tar -czf "$DOWNLOADS/volume-monitor.tar.gz" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    .

echo "  Package created: $DOWNLOADS/volume-monitor.tar.gz"
echo ""

# Step 2: Extract the package (as user would)
echo -e "${YELLOW}[Step 2] Extracting package...${NC}"
cd "$TEST_HOME"
tar -xzf "$DOWNLOADS/volume-monitor.tar.gz"
echo "  Extracted to: $TEST_HOME"
echo ""

# Step 3: Check package contents
echo -e "${YELLOW}[Step 3] Verifying package contents...${NC}"
cd "$TEST_HOME"

REQUIRED_FILES=(
    "pyproject.toml"
    "README.md"
    "install.fish"
    "install.sh"
    "setup.py"
    "src/volume_monitor/__init__.py"
    "src/volume_monitor/cli.py"
    "src/volume_monitor/config.py"
)

ALL_FOUND=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file MISSING"
        ALL_FOUND=false
    fi
done
echo ""

if [ "$ALL_FOUND" = false ]; then
    echo -e "${RED}Required files missing!${NC}"
    exit 1
fi

# Step 4: Test Python package import
echo -e "${YELLOW}[Step 4] Testing Python imports...${NC}"
PYTHONPATH="src" python3 -c "
from volume_monitor.config import MonitorConfig
from volume_monitor.audio.pipewire import clamp_volume_percent
from volume_monitor.utils.normalization import normalize_name
print('  All imports successful')
" && echo -e "  ${GREEN}✓${NC} Imports work" || echo -e "  ${RED}✗${NC} Import failed"
echo ""

# Step 5: Test configuration
echo -e "${YELLOW}[Step 5] Testing configuration...${NC}"
PYTHONPATH="src" python3 -c "
from volume_monitor.config import MonitorConfig
import tempfile, json

config = MonitorConfig()
config_file = tempfile.mktemp(suffix='.json')
config.save(config_file)

with open(config_file) as f:
    data = json.load(f)
    
assert 'companion_ip' in data
assert 'companion_port' in data
print('  Configuration: OK')
" && echo -e "  ${GREEN}✓${NC} Config works" || echo -e "  ${RED}✗${NC} Config failed"
echo ""

# Step 6: Test CLI (dry run)
echo -e "${YELLOW}[Step 6] Testing CLI...${NC}"
PYTHONPATH="src" python3 -m volume_monitor --help >/dev/null 2>&1 && \
    echo -e "  ${GREEN}✓${NC} CLI help works" || \
    echo -e "  ${RED}✗${NC} CLI help failed"
echo ""

# Step 7: Verify no syntax errors in Python files
echo -e "${YELLOW}[Step 7] Checking Python syntax...${NC}"
ERRORS=0
for pyfile in $(find src -name "*.py"); do
    python3 -m py_compile "$pyfile" 2>/dev/null || {
        echo -e "  ${RED}✗${NC} Syntax error in: $pyfile"
        ERRORS=$((ERRORS + 1))
    }
done

if [ $ERRORS -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All Python files have valid syntax"
else
    echo -e "  ${RED}✗${NC} $ERRORS files have syntax errors"
fi
echo ""

# Step 8: Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  End-to-End Test Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "The package structure appears valid."
echo ""
echo "To test actual installation:"
echo "  cd $TEST_HOME"
echo "  pipx install --editable ."
echo "  volume-monitor --help"
echo ""
echo "Clean up test files:"
echo "  rm -rf $TEST_HOME"