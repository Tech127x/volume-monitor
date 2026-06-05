"""End-to-end tests that simulate real usage scenarios."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from volume_monitor.companion.client import CompanionTCPClient
from volume_monitor.config import MonitorConfig
from volume_monitor.monitors.app_knobs import AppKnobMonitor
from volume_monitor.monitors.volume import VolumeMonitor


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

    @patch("volume_monitor.monitors.app_knobs.get_wpctl_audio_streams")
    @patch("volume_monitor.monitors.app_knobs.get_default_sink_state")
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
        from volume_monitor.constants import KNOB_APP_FIRST, KNOB_APP_LAST, KNOB_MASTER

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

    def test_monitor_inherits_basemonitor(self, mock_client):
        """Test that monitors inherit from BaseMonitor."""
        from volume_monitor.monitors.base import BaseMonitor

        monitor = VolumeMonitor(
            mock_client,
            "volume_var",
            "mute_var",
            "device_var",
        )
        assert isinstance(monitor, BaseMonitor)

        knob_monitor = AppKnobMonitor(mock_client)
        assert isinstance(knob_monitor, BaseMonitor)

    def test_volume_monitor_throttling(self, mock_client):
        """Test volume monitor's update throttling."""
        with patch("volume_monitor.monitors.volume.time.time", return_value=1000.0):
            monitor = VolumeMonitor(
                mock_client,
                "vol_var",
                "mute_var",
                "dev_var",
            )

            # First update should go through (last_t is 0, so window is open)
            monitor.update_companion(50, False, "Test Device")
            initial_calls = mock_client.update_variable.call_count
            assert initial_calls > 0

            # Now last_t is 1000.0, subsequent calls with same time are within 0.02s window
            monitor.update_companion(60, False, "Test Device")
            monitor.update_companion(70, False, "Test Device")
            # No new calls because throttle window is still active
            assert mock_client.update_variable.call_count == initial_calls

    def test_volume_monitor_same_state_skipped(self, mock_client):
        """Test that identical state doesn't trigger updates."""
        from volume_monitor.audio.pipewire import get_default_sink_state

        monitor = VolumeMonitor(
            mock_client,
            "vol_var",
            "mute_var",
            "dev_var",
        )

        monitor._last_vol = 50
        monitor._last_muted = False
        monitor._last_dev = "Test Device"
        monitor._last_t = 0.0

        monitor.update_companion(50, False, "Test Device")
        # No new calls because state is identical
        assert mock_client.update_variable.call_count == 0

    def test_config_load_merge(self, tmp_path):
        """Test that config merges partial files with defaults."""
        import json

        # Save partial config (only IP, missing other fields)
        partial = {"companion_ip": "10.0.0.50"}
        config_file = tmp_path / "partial_config.json"
        config_file.write_text(json.dumps(partial))

        loaded = MonitorConfig.load(config_file)
        # Custom value should be loaded
        assert loaded.companion_ip == "10.0.0.50"
        # Default values should fill in
        assert loaded.companion_port == 16759
        assert loaded.poll_interval == 0.03
        assert loaded.notify_on_switch is True
        assert loaded.exclude_apps is not None

    def test_config_load_corrupted(self, tmp_path):
        """Test that corrupted config falls back to defaults gracefully."""
        config_file = tmp_path / "corrupt_config.json"
        config_file.write_text("{not valid json}")

        loaded = MonitorConfig.load(config_file)
        assert loaded.companion_ip == "127.0.0.1"
        assert loaded.companion_port == 16759

    @patch("volume_monitor.monitors.volume.get_default_sink_state")
    def test_volume_monitor_push_initial_state_failure(self, mock_sink, mock_client):
        """Test monitor handles initial state read failure gracefully."""
        mock_sink.return_value = (None, False, None)

        monitor = VolumeMonitor(
            mock_client,
            "vol_var",
            "mute_var",
            "dev_var",
        )

        result = monitor.push_initial_state()
        assert result is False

    def test_cli_parser_list_devices(self):
        """Test CLI parser with list-devices argument."""
        from volume_monitor.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--list-devices"])
        assert args.list_devices is True

    def test_cli_parser_mutual_exclusion(self):
        """Test CLI parser rejects conflicting arguments."""
        from volume_monitor.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--start", "--stop"])
