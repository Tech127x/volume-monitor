"""Verify package structure is correct for distribution."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

import importlib
import os
import pkgutil
from pathlib import Path

import pytest


def test_package_can_be_imported():
    """Test that the main package imports cleanly."""
    import volume_monitor

    assert hasattr(volume_monitor, "__version__")


def test_all_modules_importable():
    """Test that all submodules can be imported."""
    import volume_monitor

    modules_to_test = [
        "volume_monitor.config",
        "volume_monitor.constants",
        "volume_monitor.logging_setup",
        "volume_monitor.fish_support",
        "volume_monitor.cli_utils",
        "volume_monitor.audio",
        "volume_monitor.audio.pipewire",
        "volume_monitor.audio.streams",
        "volume_monitor.audio.devices",
        "volume_monitor.audio.pactl",
        "volume_monitor.audio.volume_cache",
        "volume_monitor.companion",
        "volume_monitor.companion.client",
        "volume_monitor.monitors",
        "volume_monitor.monitors.base",
        "volume_monitor.monitors.volume",
        "volume_monitor.monitors.app_knobs",
        "volume_monitor.utils",
        "volume_monitor.utils.normalization",
        "volume_monitor.utils.notifications",
        "volume_monitor.utils.process",
        "volume_monitor.utils.threading_utils",
    ]

    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_package_files_exist():
    """Verify all expected files exist in the package."""
    src_dir = Path(__file__).parent.parent / "src" / "volume_monitor"

    expected_files = [
        "__init__.py",
        "__main__.py",
        "cli.py",
        "cli_utils.py",
        "config.py",
        "constants.py",
        "logging_setup.py",
        "fish_support.py",
        "config.fish",
        "audio/__init__.py",
        "audio/devices.py",
        "audio/pactl.py",
        "audio/pipewire.py",
        "audio/streams.py",
        "audio/volume_cache.py",
        "companion/__init__.py",
        "companion/client.py",
        "monitors/__init__.py",
        "monitors/app_knobs.py",
        "monitors/base.py",
        "monitors/volume.py",
        "utils/__init__.py",
        "utils/normalization.py",
        "utils/notifications.py",
        "utils/process.py",
        "utils/threading_utils.py",
    ]

    missing_files = []
    for file_path in expected_files:
        full_path = src_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        pytest.fail(f"Missing files: {missing_files}")


def test_package_metadata():
    """Test package metadata is correct."""
    import volume_monitor

    assert hasattr(volume_monitor, "__version__")
    assert hasattr(volume_monitor, "__author__")
    assert hasattr(volume_monitor, "__license__")
    assert isinstance(volume_monitor.__version__, str)
    assert volume_monitor.__license__ == "MIT"
