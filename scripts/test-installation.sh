#!/bin/bash

# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor
# Comprehensive installation test script for Volume Monitor
# Simulates a user downloading and installing from scratch

set -e

# Colors
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Volume Monitor Installation Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create a temporary test directory
TEST_DIR=$(mktemp -d)
echo -e "${YELLOW}Test directory: $TEST_DIR${NC}"

# Simulate downloaded package
echo ""
echo -e "${YELLOW}[Test 1] Simulating package download...${NC}"
cp -r . "$TEST_DIR/volume-monitor"
cd "$TEST_DIR/volume-monitor"

# Check package structure
echo ""
echo -e "${YELLOW}[Test 2] Checking package structure...${NC}"

# Check required files
for file in pyproject.toml README.md install.fish setup.py; do
    if [ -f "$file" ]; then
        pass "Found $file"
    else
        fail "Missing $file"
    fi
done

# Check required directories
for dir in src tests scripts docs; do
    if [ -d "$dir" ]; then
        pass "Found $dir/ directory"
    else
        fail "Missing $dir/ directory"
    fi
done

# Check Python package structure
echo ""
echo -e "${YELLOW}[Test 3] Checking Python package...${NC}"

PYTHON_FILES=(
    "src/volume_monitor/__init__.py"
    "src/volume_monitor/config.py"
    "src/volume_monitor/cli.py"
    "src/volume_monitor/audio/pipewire.py"
    "src/volume_monitor/audio/streams.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "Found $file"
    else
        fail "Missing $file"
    fi
done

# Check __init__.py files exist for all subpackages
echo ""
echo -e "${YELLOW}[Test 4] Checking package __init__.py files...${NC}"

for init_file in \
    src/volume_monitor/audio/__init__.py \
    src/volume_monitor/companion/__init__.py \
    src/volume_monitor/monitors/__init__.py \
    src/volume_monitor/utils/__init__.py \
    tests/__init__.py; do
    if [ -f "$init_file" ]; then
        pass "Found $init_file"
    else
        fail "Missing $init_file"
    fi
done

# Test Python imports
echo ""
echo -e "${YELLOW}[Test 5] Testing Python imports...${NC}"

python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    import volume_monitor
    print('  Main package: OK')
except Exception as e:
    print(f'  Main package: FAILED - {e}')
    sys.exit(1)

try:
    from volume_monitor.config import MonitorConfig
    config = MonitorConfig()
    print('  Config module: OK')
except Exception as e:
    print(f'  Config module: FAILED - {e}')
    sys.exit(1)

try:
    from volume_monitor.audio import pipewire
    print('  Audio module: OK')
except Exception as e:
    print(f'  Audio module: FAILED - {e}')
    sys.exit(1)

try:
    from volume_monitor.monitors import VolumeMonitor, AppKnobMonitor
    print('  Monitors module: OK')
except Exception as e:
    print(f'  Monitors module: FAILED - {e}')
    sys.exit(1)

try:
    from volume_monitor.companion import CompanionTCPClient
    print('  Companion module: OK')
except Exception as e:
    print(f'  Companion module: FAILED - {e}')
    sys.exit(1)

print('All imports successful!')
" && pass "All Python imports work" || fail "Python imports failed"

# Test with pytest if available
echo ""
echo -e "${YELLOW}[Test 6] Running unit tests...${NC}"

if python3 -m pytest --version >/dev/null 2>&1; then
    if python3 -m pytest tests/ -v --tb=short 2>&1; then
        pass "Unit tests passed"
    else
        fail "Unit tests failed"
    fi
else
    echo -e "  ${YELLOW}!${NC} pytest not installed, skipping unit tests"
    echo "  Install with: pip install pytest"
fi

# Test pipx installation (dry run)
echo ""
echo -e "${YELLOW}[Test 7] Testing pipx compatibility...${NC}"

if command -v pipx >/dev/null 2>&1; then
    # Check pyproject.toml is valid
    if python3 -c "
import tomllib
try:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
    assert 'project' in data
    assert 'scripts' in data['project']
    print('pyproject.toml: Valid')
except Exception as e:
    print(f'pyproject.toml: INVALID - {e}')
    exit(1)
" 2>/dev/null; then
        pass "pyproject.toml is valid"
    else
        # Try with tomli for older Python
        if python3 -c "import tomli" 2>/dev/null; then
            python3 -c "
import tomli
with open('pyproject.toml', 'rb') as f:
    data = tomli.load(f)
assert 'project' in data
print('pyproject.toml: Valid')
" && pass "pyproject.toml is valid" || fail "pyproject.toml is invalid"
        else
            echo -e "  ${YELLOW}!${NC} Cannot validate pyproject.toml (install tomli)"
        fi
    fi
else
    echo -e "  ${YELLOW}!${NC} pipx not installed, skipping"
fi

# Test Fish shell integration
echo ""
echo -e "${YELLOW}[Test 8] Testing Fish shell files...${NC}"

if [ -f "install.fish" ]; then
    # Check fish syntax
    if command -v fish >/dev/null 2>&1; then
        if fish -n install.fish 2>/dev/null; then
            pass "install.fish has valid syntax"
        else
            fail "install.fish has syntax errors"
        fi
    else
        pass "install.fish exists (fish not available for syntax check)"
    fi
else
    fail "install.fish missing"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  ${GREEN}Passed: $PASS${NC}"
echo -e "  ${RED}Failed: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed! Package is ready for release.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed. Please fix before releasing.${NC}"
    exit 1
fi