"""
Tests for client configuration module
"""
import os
import yaml
import uuid
import pytest
import tempfile
import time
from unittest.mock import patch, MagicMock

from client.config import ClientConfig, get_client_config

class TestClientConfig:
    """Test suite for the ClientConfig class"""
    
    def test_generate_new_config(self):
        """Test generating a new client configuration"""
        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
            # Create config with temp file path
            client_config = ClientConfig(temp_file.name)
            
            # Check if config has the required sections
            assert "client" in client_config.config
            assert "server" in client_config.config
            assert "settings" in client_config.config
            
            # Check if UUID and token were generated
            assert "uuid" in client_config.config["client"]
            assert "token" in client_config.config["client"]
            
            # Check if config was saved to disk
            with open(temp_file.name, 'r') as f:
                saved_config = yaml.safe_load(f)
                
            assert saved_config["client"]["uuid"] == client_config.config["client"]["uuid"]
            assert saved_config["client"]["token"] == client_config.config["client"]["token"]
            
    def test_load_existing_config(self):
        """Test loading an existing configuration"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
            # Create a config file manually
            test_uuid = "test-uuid-1234"
            test_token = "test-token-5678"
            test_config = {
                "client": {
                    "uuid": test_uuid,
                    "token": test_token,
                    "created_at": time.time()
                },
                "server": {
                    "url": "http://test-server:8000"
                },
                "settings": {
                    "log_level": "DEBUG"
                }
            }
            
            yaml.dump(test_config, temp_file)
            
        try:
            # Load the config we just created
            client_config = ClientConfig(temp_file.name)
            
            # Verify it loaded correctly
            assert client_config.config["client"]["uuid"] == test_uuid
            assert client_config.config["client"]["token"] == test_token
            assert client_config.config["server"]["url"] == "http://test-server:8000"
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    def test_invalid_config_regenerates(self):
        """Test that an invalid config is regenerated"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
            # Create an invalid config file (missing required fields)
            invalid_config = {
                "client": {
                    # Missing uuid and token
                    "created_at": time.time()
                },
                "server": {
                    "url": "http://test-server:8000"
                }
                # Missing settings section
            }
            
            yaml.dump(invalid_config, temp_file)
            
        try:
            # Load the invalid config
            client_config = ClientConfig(temp_file.name)
            
            # It should regenerate a valid config
            assert "uuid" in client_config.config["client"]
            assert "token" in client_config.config["client"]
            assert "settings" in client_config.config
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    def test_reset_config(self):
        """Test resetting the client configuration"""
        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
            # Create initial config
            client_config = ClientConfig(temp_file.name)
            original_uuid = client_config.config["client"]["uuid"]
            original_token = client_config.config["client"]["token"]
            
            # Reset the config
            client_config.reset_config()
            
            # Verify new UUID and token were generated
            assert client_config.config["client"]["uuid"] != original_uuid
            assert client_config.config["client"]["token"] != original_token
            
            # Verify it was saved to disk
            with open(temp_file.name, 'r') as f:
                saved_config = yaml.safe_load(f)
                
            assert saved_config["client"]["uuid"] == client_config.config["client"]["uuid"]
            assert saved_config["client"]["token"] == client_config.config["client"]["token"]
    
    @patch('client.config.requests.get')
    def test_sync_with_server_success(self, mock_get):
        """Test successful sync with server"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "containers": {
                "test-container": {
                    "image": "test-image:latest",
                    "resources": {"memory": "512m"}
                }
            }
        }
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
            client_config = ClientConfig(temp_file.name)
            
            # Sync with server
            result = client_config.sync_with_server()
            
            # Verify sync was successful
            assert result is True
            assert "server_config" in client_config.config
            assert "containers" in client_config.config["server_config"]
            assert "test-container" in client_config.config["server_config"]["containers"]
            
            # Verify server was called with correct headers
            uuid, token = client_config.get_uuid_and_token()
            mock_get.assert_called_once()
            headers = mock_get.call_args[1]['headers']
            assert headers["Authorization"] == f"Bearer {uuid}:{token}"
            
    @patch('client.config.requests.get')
    def test_sync_with_server_failure(self, mock_get):
        """Test failed sync with server"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401  # Unauthorized
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
            client_config = ClientConfig(temp_file.name)
            
            # Sync with server
            result = client_config.sync_with_server()
            
            # Verify sync failed
            assert result is False
            assert "server_config" not in client_config.config
            
    @patch('client.config.requests.get')
    def test_sync_with_server_exception(self, mock_get):
        """Test sync with server raises exception"""
        # Mock exception
        mock_get.side_effect = Exception("Connection error")
        
        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp_file:
            client_config = ClientConfig(temp_file.name)
            
            # Sync with server
            result = client_config.sync_with_server()
            
            # Verify sync failed
            assert result is False
