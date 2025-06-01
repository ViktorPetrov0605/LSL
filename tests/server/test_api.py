"""
Test module for REST API in server/api.py
"""
import unittest
import os
import tempfile
import yaml
import json
import pytest
import signal
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the module to test
from server.api import app, reload_config, setup_app, get_running_containers

class TestRESTAPI(unittest.TestCase):
    def setUp(self):
        """Set up temporary config files and client for testing."""
        # Create a temporary directory for config files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test config files
        self.users_path = os.path.join(self.test_dir, 'users.yaml')
        self.containers_path = os.path.join(self.test_dir, 'containers.yaml')
        self.main_path = os.path.join(self.test_dir, 'main.yaml')
        
        # Create basic test users config
        self.test_users = {
            "users": {
                "testuser1": {
                    "uuid": "11111111-1111-4111-a111-111111111111",
                    "password_hash": "pbkdf2-sha256$100000$aabbccddeeff$1234567890abcdef",
                    "allowed_containers": ["alpine", "ubuntu"],
                    "metadata": {"email": "user1@example.com"}
                },
                "testuser2": {
                    "uuid": "22222222-2222-4222-a222-222222222222",
                    "password_hash": "pbkdf2-sha256$100000$bbccddeeffaa$234567890abcdef1",
                    "allowed_containers": ["ubuntu"],
                    "metadata": {"email": "user2@example.com"}
                }
            }
        }
        
        # Create basic test containers config
        self.test_containers = {
            "containers": {
                "alpine": {
                    "image": "alpine:latest",
                    "shared": False,
                    "resources": {
                        "cpu": "0.5",
                        "memory": "512Mi"
                    }
                },
                "ubuntu": {
                    "image": "ubuntu:20.04",
                    "shared": True,
                    "resources": {
                        "cpu": "1.0",
                        "memory": "1Gi"
                    }
                }
            }
        }
        
        # Create basic test main config with rate limits
        self.test_main = {
            "admin": {
                "username": "admin",
                "password_hash": "pbkdf2-sha256$100000$ccddeeffe$3456789012abcdef"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "rate_limits": {
                    "get_config": 60,
                    "ping": 120,
                    "monitor": 30
                }
            },
            "logging": {
                "level": "info",
                "file": "/tmp/lsl-server.log"
            }
        }
        
        # Write the test configs to files
        with open(self.users_path, 'w') as f:
            yaml.dump(self.test_users, f)
        with open(self.containers_path, 'w') as f:
            yaml.dump(self.test_containers, f)
        with open(self.main_path, 'w') as f:
            yaml.dump(self.test_main, f)
        
        # Setup test client with our app
        with patch('server.api.CONFIG_PATHS', {
            'main': self.main_path,
            'users': self.users_path,
            'containers': self.containers_path
        }):
            # Reset current state
            app.state.main_config = None
            app.state.users_config = None
            app.state.containers_config = None
            app.state.last_seen = {}
            
            # Initialize with our test configs
            setup_app()
            
            # Create a test client
            self.client = TestClient(app)
    
    def tearDown(self):
        """Clean up temporary files after tests."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_ping_endpoint_valid_uuid(self):
        """Test that ping endpoint works with a valid UUID."""
        valid_uuid = "11111111-1111-4111-a111-111111111111"  # testuser1's UUID
        response = self.client.post(
            "/ping",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        
        # Check response
        assert response.status_code == 200
        assert "success" in response.json()
        assert response.json()["success"] is True
        
        # Check that last_seen was updated
        assert valid_uuid in app.state.last_seen
        assert (datetime.now() - app.state.last_seen[valid_uuid]).total_seconds() < 5
    
    def test_ping_endpoint_invalid_uuid(self):
        """Test that ping endpoint rejects invalid UUIDs."""
        invalid_uuid = "not-a-valid-uuid"
        response = self.client.post(
            "/ping",
            headers={"Authorization": f"Bearer {invalid_uuid}"}
        )
        
        # Check response
        assert response.status_code == 401
        assert "error" in response.json()
        assert "detail" in response.json()
        
        # Check that last_seen was not updated
        assert invalid_uuid not in app.state.last_seen
    
    def test_get_config_endpoint_valid_uuid(self):
        """Test that get_config endpoint returns merged config for a valid UUID."""
        valid_uuid = "11111111-1111-4111-a111-111111111111"  # testuser1's UUID
        response = self.client.get(
            "/get_config",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check that user gets only allowed containers
        assert "containers" in data
        assert len(data["containers"]) == 2
        assert "alpine" in data["containers"]
        assert "ubuntu" in data["containers"]
        
        # Check container details
        assert data["containers"]["alpine"]["image"] == "alpine:latest"
        assert data["containers"]["ubuntu"]["shared"] is True
    
    def test_get_config_endpoint_restricted_containers(self):
        """Test that users can only access their allowed containers."""
        valid_uuid = "22222222-2222-4222-a222-222222222222"  # testuser2's UUID (only ubuntu)
        response = self.client.get(
            "/get_config",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check that user gets only allowed containers
        assert "containers" in data
        assert len(data["containers"]) == 1
        assert "alpine" not in data["containers"]
        assert "ubuntu" in data["containers"]
    
    @patch('server.api.get_system_stats')
    @patch('server.api.get_running_containers')
    def test_monitor_endpoint(self, mock_containers, mock_stats):
        """Test that monitor endpoint returns system and container stats."""
        # Mock system stats
        mock_stats.return_value = {
            "cpu": 15.2,
            "memory": {"total": 16384, "used": 8192, "percent": 50.0},
            "disk": {"total": 100, "used": 25, "percent": 25.0}
        }
        
        # Mock container info
        mock_containers.return_value = [
            {
                "name": "lsl_alpine_testuser1",
                "image": "alpine:latest",
                "status": "running",
                "owner": "testuser1"
            },
            {
                "name": "lsl_ubuntu_shared",
                "image": "ubuntu:20.04",
                "status": "running",
                "owner": "testuser2"
            }
        ]
        
        # Add some last seen data
        app.state.last_seen = {
            "11111111-1111-4111-a111-111111111111": datetime.now() - timedelta(minutes=5),
            "22222222-2222-4222-a222-222222222222": datetime.now() - timedelta(seconds=30)
        }
        
        response = self.client.get(
            "/monitor",
            headers={"Authorization": f"Bearer admin-token"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check that we get system stats
        assert "system" in data
        assert "cpu" in data["system"]
        assert "memory" in data["system"]
        assert "disk" in data["system"]
        
        # Check that we get container info
        assert "containers" in data
        assert len(data["containers"]) == 2
        
        # Check that we get client last seen info
        assert "clients" in data
        assert len(data["clients"]) == 2
        # Users should be resolved to usernames
        assert any(client["username"] == "testuser1" for client in data["clients"])
        assert any(client["username"] == "testuser2" for client in data["clients"])
    
    def test_rate_limiting(self):
        """Test that rate limiting works as expected."""
        valid_uuid = "11111111-1111-4111-a111-111111111111"
        
        # Set a very low rate limit for testing
        app.state.main_config["server"]["rate_limits"]["ping"] = 2  # 2 requests per minute
        
        # First request should succeed
        response1 = self.client.post(
            "/ping",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        assert response1.status_code == 200
        
        # Second request should succeed
        response2 = self.client.post(
            "/ping",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        assert response2.status_code == 200
        
        # Third request should be rate limited
        response3 = self.client.post(
            "/ping",
            headers={"Authorization": f"Bearer {valid_uuid}"}
        )
        assert response3.status_code == 429  # Too Many Requests
        assert "error" in response3.json()
    
    def test_reload_config_signal_handler(self):
        """Test that SIGHUP reloads configurations."""
        # Mock the signal handler
        with patch('server.api.load_yaml_config') as mock_load:
            # Setup mock to return different values on each call
            mock_load.side_effect = [
                {"server": {"host": "127.0.0.2"}},  # New main config
                {"users": {"newuser": {"uuid": "new-uuid"}}},  # New users config
                {"containers": {"newcontainer": {"image": "new:image"}}}  # New containers config
            ]
            
            # Call the reload function directly (simulating signal handler)
            reload_config(None, None)
            
            # Check that configs were reloaded
            assert mock_load.call_count == 3
            assert app.state.main_config["server"]["host"] == "127.0.0.2"
            assert "newuser" in app.state.users_config["users"]
            assert "newcontainer" in app.state.containers_config["containers"]

if __name__ == "__main__":
    unittest.main()
