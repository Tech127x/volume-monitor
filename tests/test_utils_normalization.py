"""Tests for name normalization utilities."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

from volume_monitor.utils.normalization import (
    disambiguate_label,
    is_excluded_app,
    norm_device_name,
    normalize_name,
    prettify_game_name,
)


class TestNormalization:
    """Tests for normalization functions."""

    def test_normalize_name(self):
        """Test name normalization."""
        assert normalize_name("Firefox") == "firefox"
        assert normalize_name("  Firefox  ") == "firefox"
        assert normalize_name("FireFox BROWSER") == "firefox browser"

    def test_norm_device_name(self):
        """Test device name normalization."""
        assert norm_device_name("Sound Blaster G8") == "Sound Blaster G8"
        assert norm_device_name("Built-in Audio (HDMI)") == "Built-in Audio"
        assert norm_device_name(None) == "Unknown"

    def test_prettify_game_name(self):
        """Test game name prettification."""
        assert prettify_game_name("hl2.exe") == "Hl2"
        assert prettify_game_name("witcher3.exe") == "Witcher3"
        assert prettify_game_name("my_game-x64") == "My Game X64"

    def test_disambiguate_label(self):
        """Test label disambiguation."""
        used = {"Firefox", "Chrome"}

        # Unique label
        assert disambiguate_label("Spotify", {}, used) == "Spotify"

        # Duplicate label
        assert disambiguate_label("Firefox", {"media.name": "YouTube"}, used) == "Firefox — YouTube"

        # Duplicate with no media name
        assert disambiguate_label("Chrome", {}, used) == "Chrome (2)"

    def test_is_excluded_app(self):
        """Test app exclusion matching."""
        exclude = ["plasmashell", "wireplumber", "pipewire", "chromium input"]

        assert is_excluded_app("plasmashell", exclude) is True
        assert is_excluded_app("PlasmaShell", exclude) is True
        assert is_excluded_app("Firefox", exclude) is False
        assert is_excluded_app("wireplumber helper", exclude) is True
        # "chromium" playback should NOT be excluded by "chromium input" pattern
        assert is_excluded_app("Chromium", exclude) is False
        assert is_excluded_app("Chromium: Playback", exclude) is False
