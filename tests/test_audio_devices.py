"""Tests for audio device management."""
# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x

from volume_monitor.audio.devices import filter_devices


class TestDeviceFiltering:
    """Tests for device filtering."""
    
    def test_filter_devices_no_patterns(self):
        """Test filtering with no patterns."""
        devices = [
            {"id": "1", "name": "Sound Blaster G8"},
            {"id": "2", "name": "Built-in Audio"},
        ]
        result = filter_devices(devices)
        assert len(result) == 2
    
    def test_filter_devices_include(self):
        """Test include filtering."""
        devices = [
            {"id": "1", "name": "Sound Blaster G8"},
            {"id": "2", "name": "Built-in Audio"},
            {"id": "3", "name": "USB Headset"},
        ]
        result = filter_devices(devices, include_patterns=["*Blaster*", "*USB*"])
        assert len(result) == 2
        assert result[0]["name"] == "Sound Blaster G8"
        assert result[1]["name"] == "USB Headset"
    
    def test_filter_devices_exclude(self):
        """Test exclude filtering."""
        devices = [
            {"id": "1", "name": "Sound Blaster G8"},
            {"id": "2", "name": "Built-in Audio"},
            {"id": "3", "name": "HDMI Output"},
        ]
        result = filter_devices(devices, exclude_patterns=["*HDMI*"])
        assert len(result) == 2
        names = [d["name"] for d in result]
        assert "HDMI Output" not in names
    
    def test_filter_devices_include_and_exclude(self):
        """Test combined include/exclude filtering."""
        devices = [
            {"id": "1", "name": "Sound Blaster G8"},
            {"id": "2", "name": "Built-in Audio"},
            {"id": "3", "name": "USB Headset"},
        ]
        result = filter_devices(
            devices,
            include_patterns=["Sound*", "Built*", "USB*"],
            exclude_patterns=["*USB*"],
        )
        assert len(result) == 2
        names = [d["name"] for d in result]
        assert "USB Headset" not in names