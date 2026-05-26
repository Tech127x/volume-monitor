"""End-to-end tests that simulate real usage scenarios."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from volume_monitor.config import MonitorConfig
from volume_monitor.monitors.volume import VolumeMonitor
from volume_monitor.monitors.app_knobs import AppKnobMonitor
from volume_monitor.companion.client import CompanionTCPClient


class TestEndToEnd:
    """End-to-end workflow tests."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Companion client."""
        client = MagicMock(spec=CompanionTCPClient)
        client.send_command.return_value = True
        client.update_variable.return_value = True
        return client
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return MonitorConfig(
            companion_ip="127.0.0.1",
            companion_port=16759,
            poll_interval=0.1,
        )
    
    def test_full_config_workflow(self, tmp_path):
        """Test the full configuration workflow."""
        # Create config
        config = MonitorConfig(companion_ip="10.0.0.1")
        
        # Save config
        config_file = tmp_path / "test_config.json"
        config.save(config_file)
        assert config_file.exists()
        
        # Load config
        loaded = MonitorConfig.load(config_file)
        assert loaded.companion_ip == "10.0.0.1"
        
        # Verify JSON structure
        data = json.loads(config_file.read_text())
        assert "companion_ip" in data
        assert "companion_port" in data
        assert "poll_interval" in data
    
    def test_monitor_start_stop(self, mock_client):
        """Test monitor lifecycle."""
        monitor = VolumeMonitor(
            mock_client,
            "volume_var",
            "mute_var",
            "device_var",
        )
        
        # Start should work
        monitor.start()
        assert monitor._running.is_set()
        
        # Stop should work
        monitor.stop()
        assert not monitor._running.is_set()
    
    @patch('volume_monitor.monitors.app_knobs.get_wpctl_audio_streams')
    @patch('volume_monitor.monitors.app_knobs.get_default_sink_state')
    def test_app_knob_monitor_init(self, mock_sink, mock_streams, mock_client):
        """Test app knob monitor initialization."""
        mock_sink.return_value = ("Test Device", False, 75)
        mock_streams.return_value = []
        
        monitor = AppKnobMonitor(mock_client)
        result = monitor.push_initial_state()
        
        # Should return True even with no streams
        assert result is True
    
    def test_variable_naming_consistency(self):
        """Test Companion variable naming is consistent."""
        from volume_monitor.constants import KNOB_MASTER, KNOB_APP_FIRST, KNOB_APP_LAST
        
        # Master knob variables
        assert KNOB_MASTER == 1
        assert KNOB_APP_FIRST == 2
        assert KNOB_APP_LAST == 4
        
        # Variable naming pattern
        monitor = AppKnobMonitor(MagicMock())
        
        for knob in [KNOB_MASTER] + list(range(KNOB_APP_FIRST, KNOB_APP_LAST + 1)):
            vars_map = monitor._knob_vars(knob)
            assert f"knob{knob}_label" in vars_map.values()
            assert f"knob{knob}_volume" in vars_map.values()
            assert f"knob{knob}_muted" in vars_map.values()