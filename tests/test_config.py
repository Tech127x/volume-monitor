"""Tests for configuration management."""
import json
from pathlib import Path

from volume_monitor.config import MonitorConfig


class TestMonitorConfig:
    """Tests for MonitorConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MonitorConfig()
        assert config.companion_ip == "127.0.0.1"
        assert config.companion_port == 16759
        assert config.poll_interval == 0.03
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = MonitorConfig(companion_ip="192.168.1.1", companion_port=8000)
        assert config.companion_ip == "192.168.1.1"
        assert config.companion_port == 8000
        
        # Invalid port
        try:
            MonitorConfig(companion_port=70000)
            assert False, "Should have raised ValidationError"
        except Exception:
            pass
    
    def test_save_and_load(self, temp_config_file):
        """Test saving and loading configuration."""
        config = MonitorConfig(companion_ip="10.0.0.1")
        config.save(temp_config_file)
        
        loaded = MonitorConfig.load(temp_config_file)
        assert loaded.companion_ip == "10.0.0.1"
    
    def test_load_nonexistent(self):
        """Test loading when config file doesn't exist."""
        config = MonitorConfig.load(Path("/nonexistent/config.json"))
        assert config.companion_ip == "127.0.0.1"