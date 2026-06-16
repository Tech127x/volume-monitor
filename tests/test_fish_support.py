"""Test Fish shell support functionality."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

import os
from pathlib import Path
from unittest.mock import Mock, patch

from volume_monitor.fish_support import (
    detect_shell,
    ensure_path_in_shell_config,
    get_shell_config_file,
    is_fish_shell,
)


class TestShellDetection:
    """Test shell detection functions."""

    def test_detect_shell_from_env(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            assert detect_shell() == "fish"

    def test_detect_shell_bash(self):
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert detect_shell() == "bash"

    def test_is_fish_shell_true(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            assert is_fish_shell() is True

    def test_is_fish_shell_false(self):
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert is_fish_shell() is False

    def test_get_shell_config_fish(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            config = get_shell_config_file()
            assert config is not None
            assert config.name == "config.fish"
            assert ".config/fish" in str(config)

    def test_get_shell_config_bash(self):
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            config = get_shell_config_file()
            assert config is not None
            assert config.name == ".bashrc"


class TestFishConfig:
    """Test Fish configuration functions."""

    def test_ensure_path_in_config(self, tmp_path):
        with patch("volume_monitor.fish_support.get_shell_config_file") as mock_config:
            config_file = tmp_path / "config.fish"
            mock_config.return_value = config_file

            with patch("volume_monitor.fish_support.detect_shell", return_value="fish"):
                result = ensure_path_in_shell_config("~/.local/bin")
                assert result is True
                assert config_file.exists()

                content = config_file.read_text()
                assert "fish_add_path" in content
                assert ".local/bin" in content
