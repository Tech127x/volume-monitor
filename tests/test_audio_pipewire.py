"""Tests for PipeWire interaction functions."""
from volume_monitor.audio.pipewire import (
    clamp_volume_percent,
    volume_percent_from_wpctl_value,
    parse_wpctl_volume_output,
)


class TestVolumeCalculations:
    """Tests for volume calculation functions."""
    
    def test_clamp_volume_percent(self):
        """Test volume percentage clamping."""
        assert clamp_volume_percent(50) == 50
        assert clamp_volume_percent(0) == 0
        assert clamp_volume_percent(100) == 100
        assert clamp_volume_percent(-10) == 0
        assert clamp_volume_percent(150) == 100
        assert clamp_volume_percent(None) is None
        assert clamp_volume_percent(75.6) == 76
    
    def test_volume_percent_from_wpctl(self):
        """Test wpctl value to percentage conversion."""
        assert volume_percent_from_wpctl_value(0.0) == 0
        assert volume_percent_from_wpctl_value(0.5) == 50
        assert volume_percent_from_wpctl_value(0.75) == 75
        assert volume_percent_from_wpctl_value(1.0) == 100
        assert volume_percent_from_wpctl_value(1.05) == 100  # Capped
        assert volume_percent_from_wpctl_value(1.5) == 100
    
    def test_parse_wpctl_volume_output(self):
        """Test parsing wpctl volume output."""
        # Normal volume
        vol, muted = parse_wpctl_volume_output("Volume: 0.75")
        assert vol == 75
        assert muted is False
        
        # Muted
        vol, muted = parse_wpctl_volume_output("Volume: 0.50 [MUTED]")
        assert vol == 50
        assert muted is True
        
        # Invalid output
        vol, muted = parse_wpctl_volume_output("")
        assert vol is None
        assert muted is False


class TestPipeWireIntegration:
    """Integration-style tests (mocked subprocess)."""
    
    def test_get_default_sink_state(self, mock_subprocess_run):
        """Test getting default sink state."""
        from volume_monitor.audio.pipewire import get_default_sink_state
        
        # Mock inspect output
        mock_subprocess_run.side_effect = [
            type('Result', (), {
                'stdout': 'node.description = "Test Speakers"\n',
                'returncode': 0,
            }),
            type('Result', (), {
                'stdout': 'Volume: 0.80\n',
                'returncode': 0,
            }),
        ]
        
        device, muted, vol = get_default_sink_state()
        assert device == "Test Speakers"
        assert muted is False
        assert vol == 80