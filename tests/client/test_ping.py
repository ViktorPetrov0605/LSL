"""
Tests for client ping module
"""
import time
import pytest
import threading
from unittest.mock import patch, MagicMock

from client.ping import PingManager
from client.config import ClientConfig

class TestPingManager:
    """Test suite for PingManager class"""
    
    @patch('client.ping.ClientConfig')
    @patch('client.ping.requests.post')
    def test_send_immediate_ping_success(self, mock_post, mock_config):
        """Test successful immediate ping"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = "http://test-server:8000"
        mock_config_instance.get_uuid_and_token.return_value = ("test-uuid", "test-token")
        mock_config.return_value = mock_config_instance
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create ping manager with the mock config
        ping_manager = PingManager(mock_config_instance)
        
        # Send immediate ping
        result = ping_manager.send_immediate_ping()
        
        # Verify ping was successful
        assert result is True
        mock_post.assert_called_once()
        
        # Verify correct URL and headers used
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test-server:8000/ping"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-uuid:test-token"
        
    @patch('client.ping.ClientConfig')
    @patch('client.ping.requests.post')
    def test_send_immediate_ping_failure(self, mock_post, mock_config):
        """Test failed immediate ping"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = "http://test-server:8000"
        mock_config_instance.get_uuid_and_token.return_value = ("test-uuid", "test-token")
        mock_config.return_value = mock_config_instance
        
        # Setup mock response for failure
        mock_response = MagicMock()
        mock_response.status_code = 401  # Unauthorized
        mock_post.return_value = mock_response
        
        # Create ping manager
        ping_manager = PingManager(mock_config_instance)
        
        # Send immediate ping
        result = ping_manager.send_immediate_ping()
        
        # Verify ping failed
        assert result is False
        
    @patch('client.ping.ClientConfig')
    @patch('client.ping.requests.post')
    def test_ping_with_retry(self, mock_post, mock_config):
        """Test ping with retry logic"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = "http://test-server:8000"
        mock_config_instance.get_uuid_and_token.return_value = ("test-uuid", "test-token")
        mock_config.return_value = mock_config_instance
        
        # First request fails with exception, second succeeds
        mock_post.side_effect = [
            Exception("Connection error"),  # First attempt fails
            MagicMock(status_code=200)      # Second attempt succeeds
        ]
        
        # Create ping manager with a very short retry delay for testing
        ping_manager = PingManager(mock_config_instance)
        ping_manager.initial_retry_delay = 0.1
        
        # Send ping with retry
        result = ping_manager._send_ping_with_retry()
        
        # Verify ping was eventually successful
        assert result is True
        assert mock_post.call_count == 2
        
    @patch('client.ping.ClientConfig')
    @patch('client.ping.requests.post')
    @patch('client.ping.time.sleep')  # Mock sleep to speed up tests
    def test_ping_with_max_retries_failure(self, mock_sleep, mock_post, mock_config):
        """Test ping fails after max retries"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = "http://test-server:8000"
        mock_config_instance.get_uuid_and_token.return_value = ("test-uuid", "test-token")
        mock_config.return_value = mock_config_instance
        
        # All requests fail
        mock_post.side_effect = Exception("Connection error")
        
        # Create ping manager with minimal retries and delay
        ping_manager = PingManager(mock_config_instance)
        ping_manager.max_retries = 3
        ping_manager.initial_retry_delay = 0.1
        
        # Send ping with retry
        result = ping_manager._send_ping_with_retry()
        
        # Verify ping failed after max retries
        assert result is False
        assert mock_post.call_count == 3  # Called exactly max_retries times
        
    @patch('client.ping.ClientConfig')
    @patch('client.ping.PingManager._send_ping_with_retry')
    def test_start_stop_ping_thread(self, mock_send_ping, mock_config):
        """Test starting and stopping the ping thread"""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.config = {
            "server": {"ping_interval": 0.1}  # Short interval for testing
        }
        
        # Create ping manager
        ping_manager = PingManager(mock_config_instance)
        
        # Start ping thread
        ping_manager.start_ping_thread()
        
        # Verify thread is running
        assert ping_manager.ping_thread.is_alive()
        
        # Let it run for a bit
        time.sleep(0.3)  # Should allow for multiple pings
        
        # Stop the thread
        ping_manager.stop_ping_thread()
        
        # Verify thread stopped
        assert not ping_manager.ping_thread.is_alive()
        
        # Verify ping was called at least once
        assert mock_send_ping.call_count >= 1
