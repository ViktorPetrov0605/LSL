"""
Tests for client sync module
"""
import pytest
from unittest.mock import patch, MagicMock

from client.sync import ConfigSyncManager

class TestConfigSyncManager:
    """Test suite for ConfigSyncManager class"""
    
    @patch('client.sync.get_client_config')
    def test_force_sync_success(self, mock_get_client_config):
        """Test successful forced sync"""
        # Setup mock client config
        mock_client_config = MagicMock()
        mock_client_config.sync_with_server.return_value = True
        mock_get_client_config.return_value = mock_client_config
        
        # Create sync manager
        sync_manager = ConfigSyncManager()
        
        # Force sync
        result = sync_manager.force_sync()
        
        # Verify sync was successful
        assert result is True
        mock_client_config.sync_with_server.assert_called_once()
        
    @patch('client.sync.get_client_config')
    def test_force_sync_failure(self, mock_get_client_config):
        """Test failed forced sync"""
        # Setup mock client config
        mock_client_config = MagicMock()
        mock_client_config.sync_with_server.return_value = False
        mock_get_client_config.return_value = mock_client_config
        
        # Create sync manager
        sync_manager = ConfigSyncManager()
        
        # Force sync
        result = sync_manager.force_sync()
        
        # Verify sync failed
        assert result is False
        
    @patch('client.sync.get_client_config')
    def test_force_sync_exception(self, mock_get_client_config):
        """Test exception during forced sync"""
        # Setup mock client config
        mock_client_config = MagicMock()
        mock_client_config.sync_with_server.side_effect = Exception("Sync error")
        mock_get_client_config.return_value = mock_client_config
        
        # Create sync manager
        sync_manager = ConfigSyncManager()
        
        # Force sync
        result = sync_manager.force_sync()
        
        # Verify sync failed
        assert result is False
        
    @patch('client.sync.get_client_config')
    @patch('client.sync.ConfigSyncManager._sync_and_ping')
    def test_start_stop_sync_thread(self, mock_sync_and_ping, mock_get_client_config):
        """Test starting and stopping sync thread"""
        # Setup mock client config
        mock_client_config = MagicMock()
        mock_client_config.config = {
            "server": {"ping_interval": 0.1}  # Short interval for testing
        }
        mock_get_client_config.return_value = mock_client_config
        
        # Create sync manager
        sync_manager = ConfigSyncManager(mock_client_config)
        
        # Start sync thread
        sync_manager.start_sync_thread()
        
        # Verify thread is running
        assert sync_manager.sync_thread.is_alive()
        
        # Let it run for a bit
        import time
        time.sleep(0.3)  # Should allow for multiple syncs
        
        # Stop the thread
        sync_manager.stop_sync_thread()
        
        # Verify thread stopped
        assert not sync_manager.sync_thread.is_alive()
        
        # Verify sync was called at least once
        assert mock_sync_and_ping.call_count >= 1
        
    @patch('client.sync.get_client_config')
    def test_get_available_containers(self, mock_get_client_config):
        """Test getting available containers"""
        # Setup mock client config
        mock_client_config = MagicMock()
        mock_client_config.config = {
            "server_config": {
                "containers": {
                    "test-container": {
                        "image": "test-image:latest",
                        "resources": {"memory": "512m"}
                    }
                }
            }
        }
        mock_get_client_config.return_value = mock_client_config
        
        # Create sync manager
        sync_manager = ConfigSyncManager(mock_client_config)
        
        # Get available containers
        containers = sync_manager.get_available_containers()
        
        # Verify containers returned correctly
        assert "test-container" in containers
        assert containers["test-container"]["image"] == "test-image:latest"
        
    @patch('client.sync.get_client_config')
    @patch('client.sync.ConfigSyncManager.force_sync')
    def test_get_available_containers_no_server_config(self, mock_force_sync, mock_get_client_config):
        """Test getting available containers when no server config exists"""
        # Setup mock client config with no server_config
        mock_client_config = MagicMock()
        mock_client_config.config = {}  # No server_config
        mock_get_client_config.return_value = mock_client_config
        
        # Setup mock force_sync to update config with containers
        def mock_force_sync_impl():
            mock_client_config.config["server_config"] = {
                "containers": {"added-container": {"image": "added-image"}}
            }
            return True
            
        mock_force_sync.side_effect = mock_force_sync_impl
        
        # Create sync manager
        sync_manager = ConfigSyncManager(mock_client_config)
        
        # Get available containers
        containers = sync_manager.get_available_containers()
        
        # Verify force_sync was called and containers returned
        mock_force_sync.assert_called_once()
        assert "added-container" in containers
