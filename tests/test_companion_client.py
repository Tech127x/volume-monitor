"""Tests for Companion TCP client."""
# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor

from unittest.mock import Mock, patch, MagicMock

from volume_monitor.companion.client import CompanionTCPClient


class TestCompanionClient:
    """Tests for CompanionTCPClient."""
    
    def test_init(self):
        """Test client initialization."""
        client = CompanionTCPClient("127.0.0.1", 16759, "test_device")
        assert client.host == "127.0.0.1"
        assert client.port == 16759
        assert client.device_id == "test_device"
        assert not client.connected.is_set()
    
    @patch('socket.socket')
    def test_connect_success(self, mock_socket_class):
        """Test successful connection."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = CompanionTCPClient("127.0.0.1", 16759, "test_device")
        result = client.connect(max_wait=0.1)
        
        assert result is True
        assert client.connected.is_set()
    
    @patch('socket.socket')
    def test_send_command_reconnects(self, mock_socket_class):
        """Test that send_command reconnects if needed."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        client = CompanionTCPClient("127.0.0.1", 16759, "test_device")
        result = client.send_command("TEST\n")
        
        assert result is True
    
    def test_update_variable(self):
        """Test variable update command formatting."""
        with patch.object(CompanionTCPClient, 'connect', return_value=True):
            with patch.object(CompanionTCPClient, '_send', return_value=True) as mock_send:
                client = CompanionTCPClient("127.0.0.1", 16759, "test_device")
                client.update_variable("test_var", "42")
                
                mock_send.assert_called_once_with(
                    "CUSTOM-VARIABLE test_var SET-VALUE 42\n"
                )