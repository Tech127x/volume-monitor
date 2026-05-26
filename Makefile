.PHONY: install test test-quick test-pipx test-all lint format clean build release dev-refresh dev-restart dev-stop dev-start update help

# Default target
help:
	@echo "Volume Monitor Makefile"
	@echo ""
	@echo "Development:"
	@echo "  make dev-stop       - Stop the monitor"
	@echo "  make dev-start      - Start the monitor"
	@echo "  make dev-refresh    - Reinstall and restart (after code changes)"
	@echo "  make dev-restart    - Restart only (no reinstall)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-quick     - Quick structural tests"
	@echo ""
	@echo "Release:"
	@echo "  make release        - Create release tarball"
	@echo "  make clean          - Clean build artifacts"

# Stop the monitor
dev-stop:
	@echo "Stopping volume-monitor..."
	@-pkill -f "volume-monitor" 2>/dev/null || true
	@sleep 0.5
	@echo "✓ Stopped"

# Start the monitor
dev-start:
	@echo "Starting volume-monitor..."
	@volume-monitor --start 2>/dev/null || \
		(echo "Installing first..." && pipx install --force --editable . && volume-monitor --start)
	@echo "✓ Started"

# Reinstall only (no restart)
dev-reinstall:
	@echo "Reinstalling..."
	@pipx install --force --editable .
	@echo "✓ Reinstalled"

# Full refresh: stop, reinstall, start
dev-refresh: dev-stop dev-reinstall
	@echo "Starting volume-monitor..."
	@volume-monitor --start
	@echo "✓ Refreshed and restarted"
	@echo ""
	@echo "Check status: volume-monitor --status"

# Restart only (no reinstall) 
dev-restart: dev-stop dev-start
	@echo "✓ Restarted"

# Update from current directory (for users)
update:
	@echo "Stopping volume-monitor..."
	@-pkill -f "volume-monitor" 2>/dev/null || true
	@sleep 1
	@echo "Updating..."
	@pipx install --force --editable .
	@echo "Starting..."
	@volume-monitor --start
	@echo "✓ Updated and restarted"

# Quick test - no dependencies needed
test-quick:
	@echo "Running quick tests..."
	@bash scripts/run-tests.sh

# Test pipx installation
test-pipx:
	@echo "Testing pipx installation..."
	@bash scripts/test-pipx-install.sh

# Run pytest if available
test-pytest:
	@if python3 -c "import pytest" 2>/dev/null; then \
		PYTHONPATH="src" python3 -m pytest tests/ -v; \
	else \
		echo "Install pytest: pip install pytest"; \
	fi

# All tests
test: test-quick test-pytest

# Code quality
lint:
	@python3 -c "import ruff" 2>/dev/null && ruff check src/ || echo "ruff not installed"
	@python3 -c "import mypy" 2>/dev/null && mypy src/ --ignore-missing-imports || echo "mypy not installed"

# Format code
format:
	@python3 -c "import black" 2>/dev/null && black src/ tests/ || echo "black not installed"

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Build tarball for distribution
build:
	tar -czf volume-monitor.tar.gz \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache' \
		--exclude='*.egg-info' \
		--exclude='dist' \
		--exclude='build' \
		.
	@echo "Created: volume-monitor.tar.gz"
	@ls -lh volume-monitor.tar.gz

# Create versioned release tarball
release:
	@python3 -c "from src.volume_monitor import __version__; print(f'Version: {__version__}')"
	tar -czf volume-monitor-$$(python3 -c "from src.volume_monitor import __version__; print(__version__)").tar.gz \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache' \
		--exclude='*.egg-info' \
		--exclude='dist' \
		--exclude='build' \
		.
	@ls -lh volume-monitor-*.tar.gz