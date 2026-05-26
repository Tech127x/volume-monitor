"""Integration tests for the complete Volume Monitor package."""
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from volume_monitor import __version__
from volume_monitor.config import MonitorConfig
from volume_monitor.companion.client import CompanionTCPClient
from volume_monitor.monitors.volume import VolumeMonitor
from volume_monitor.monitors.app_knobs import AppKnobMonitor
from volume_monitor.audio.pipewire import (
    clamp_volume_percent,
    parse_wpctl_volume_output,
    volume_percent_from_wpctl_value,
)
from volume_monitor.audio.streams import assign_knob_slots, stream_dedupe_key
from volume_monitor.audio.devices import filter_devices
from volume_monitor.utils.normalization import normalize_name, norm_device_name


class TestPackageIntegrity:
    """Test that the package is properly structured."""
    
    def test_version_string(self):
        """Test version is properly formatted."""
        assert isinstance(__version__, str)
        assert "." in __version__
    
    def test_imports_work(self):
        """Test all major imports work without errors."""
        # Test core imports
        from volume_monitor import VolumeMonitor, AppKnobMonitor, CompanionTCPClient
        from volume_monitor.audio import pipewire, streams, devices, pactl, volume_cache
        from volume_monitor.monitors import volume, app_knobs, base
        from volume_monitor.utils import normalization, notifications, process
        
        assert True
    
    def test_config_defaults(self):
        """Test default configuration is valid."""
        config = MonitorConfig()
        assert config.companion_port == 16759
        assert 0 < config.poll_interval <= 1.0
        assert isinstance(config.exclude_apps, list)
    
    def test_config_serialization(self, tmp_path):
        """Test config can be saved and loaded."""
        config = MonitorConfig(companion_ip="192.168.1.1")
        config_file = tmp_path / "test_config.json"
        config.save(config_file)
        
        loaded = MonitorConfig.load(config_file)
        assert loaded.companion_ip == "192.168.1.1"


class TestVolumeCalculations:
    """Test volume math functions."""
    
    @pytest.mark.parametrize("input_val,expected", [
        (50, 50),
        (0, 0),
        (100, 100),
        (-10, 0),
        (150, 100),
        (None, None),
        (75.6, 76),
        (25.3, 25),
    ])
    def test_clamp_volume(self, input_val, expected):
        assert clamp_volume_percent(input_val) == expected
    
    @pytest.mark.parametrize("output_str,expected_vol,expected_muted", [
        ("Volume: 0.75", 75, False),
        ("Volume: 0.50 [MUTED]", 50, True),
        ("Volume: 1.00", 100, False),
        ("", None, False),
        ("Volume: invalid", None, False),
    ])
    def test_parse_volume_output(self, output_str, expected_vol, expected_muted):
        vol, muted = parse_wpctl_volume_output(output_str)
        assert vol == expected_vol
        assert muted == expected_muted


class TestDeviceFiltering:
    """Test device filter logic thoroughly."""
    
    @pytest.fixture
    def sample_devices(self):
        return [
            {"id": "1", "name": "Sound Blaster G8"},
            {"id": "2", "name": "Built-in Audio"},
            {"id": "3", "name": "USB Headset"},
            {"id": "4", "name": "HDMI Output"},
        ]
    
    def test_no_filters(self, sample_devices):
        result = filter_devices(sample_devices)
        assert len(result) == 4
    
    def test_include_filter(self, sample_devices):
        result = filter_devices(sample_devices, include_patterns=["*Blaster*"])
        assert len(result) == 1
        assert result[0]["name"] == "Sound Blaster G8"
    
    def test_exclude_filter(self, sample_devices):
        result = filter_devices(sample_devices, exclude_patterns=["*HDMI*"])
        assert len(result) == 3
        names = [d["name"] for d in result]
        assert "HDMI Output" not in names
    
    def test_combined_filters(self, sample_devices):
        result = filter_devices(
            sample_devices,
            include_patterns=["Sound*", "Built-in*", "USB*"],
            exclude_patterns=["*USB*"],
        )
        assert len(result) == 2
    
    def test_no_matches_include(self, sample_devices):
        result = filter_devices(sample_devices, include_patterns=["*Nonexistent*"])
        assert len(result) == 0


class TestStreamAssignment:
    """Test stream-to-knob assignment logic."""
    
    def test_empty_streams(self):
        slots = assign_knob_slots([], {})
        assert all(slots[i] is None for i in range(2, 5))
    
    def test_single_stream(self):
        stream = {
            "id": "123",
            "display_name": "Firefox",
            "dedupe_key": "stream:123",
        }
        slots = assign_knob_slots([stream], {})
        assert slots[2] == stream
        assert slots[3] is None
        assert slots[4] is None
    
    def test_stable_assignment(self):
        stream1 = {"id": "1", "display_name": "App1", "dedupe_key": "stream:1"}
        stream2 = {"id": "2", "display_name": "App2", "dedupe_key": "stream:2"}
        
        # First assignment
        slot_by_key = {}
        slots1 = assign_knob_slots([stream1, stream2], slot_by_key)
        knob_for_1 = [k for k, v in slots1.items() if v == stream1][0]
        knob_for_2 = [k for k, v in slots1.items() if v == stream2][0]
        
        # Second assignment should keep same slots
        slots2 = assign_knob_slots([stream2, stream1], slot_by_key)
        assert slots2[knob_for_1] == stream1
        assert slots2[knob_for_2] == stream2


class TestCompanionClient:
    """Test Companion TCP client behavior."""
    
    def test_client_init(self):
        client = CompanionTCPClient("127.0.0.1", 16759, "test")
        assert client.host == "127.0.0.1"
        assert client.port == 16759
        assert not client.connected.is_set()
    
    @patch('socket.socket')
    def test_connect_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = CompanionTCPClient("127.0.0.1", 16759, "test")
        result = client.connect(max_wait=0.1)
        
        assert result is True
        assert client.connected.is_set()
    
    @patch('socket.socket')
    def test_variable_update_format(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.object(CompanionTCPClient, 'connect', return_value=True):
            client = CompanionTCPClient("127.0.0.1", 16759, "test")
            client.connected.set()
            
            with patch.object(client, '_send') as mock_send:
                client.update_variable("test_var", "42")
                mock_send.assert_called_once_with(
                    "CUSTOM-VARIABLE test_var SET-VALUE 42\n"
                )


class TestCLI:
    """Test CLI argument parsing."""
    
    def test_parser_creation(self):
        from volume_monitor.cli import create_parser
        parser = create_parser()
        assert parser is not None
    
    def test_parser_start_args(self):
        from volume_monitor.cli import create_parser
        parser = create_parser()
        
        # Test mutually exclusive group
        args = parser.parse_args(["--start"])
        assert args.start is True
        assert args.stop is False
        
        args = parser.parse_args(["--stop"])
        assert args.stop is True
        assert args.start is False
    
    def test_parser_device_args(self):
        from volume_monitor.cli import create_parser
        parser = create_parser()
        
        args = parser.parse_args(["--list-devices"])
        assert args.list_devices is True
        
        args = parser.parse_args(["--include", "Test Device"])
        assert args.include == "Test Device"