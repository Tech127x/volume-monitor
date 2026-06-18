"""Shared test fixtures."""
import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from volume_monitor.config import MonitorConfig


@pytest.fixture
def temp_config_file() -> Generator[Path, None, None]:
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def default_config() -> MonitorConfig:
    """Return a default configuration."""
    return MonitorConfig()


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for testing."""
    return mocker.patch('subprocess.run')


@pytest.fixture
def sample_stream():
    """Create a sample stream entry."""
    return {
        "id": "123",
        "app_name": "Firefox",
        "display_name": "Firefox",
        "volume": 75,
        "muted": False,
        "props": {"application.name": "Firefox", "media.name": "YouTube"},
        "dedupe_key": "stream:123",
    }