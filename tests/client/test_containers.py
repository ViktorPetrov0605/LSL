"""
Tests for client container management module
"""
import pytest
from unittest.mock import patch, MagicMock, call

from client.containers import ContainerManager

class TestContainerManager:
    """Test suite for ContainerManager class"""
    
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    @patch('client.containers.get_client_config')
    def test_initialization_success(self, mock_get_client_config, mock_config_sync, mock_docker):
        """Test successful initialization of ContainerManager"""
        # Setup mocks
        mock_client_config = MagicMock()
        mock_get_client_config.return_value = mock_client_config
        
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Verify docker client initialized
        assert container_manager.docker_client is mock_docker_client
        assert container_manager.client_config is mock_client_config
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    @patch('client.containers.get_client_config')
    def test_initialization_failure(self, mock_get_client_config, mock_config_sync, mock_docker):
        """Test failed initialization of ContainerManager"""
        # Setup mocks
        mock_client_config = MagicMock()
        mock_get_client_config.return_value = mock_client_config
        
        # Docker client raises exception
        mock_docker.from_env.side_effect = Exception("Docker not available")
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Verify docker client is None
        assert container_manager.docker_client is None
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    def test_list_available_containers(self, mock_config_sync, mock_docker):
        """Test listing available containers"""
        # Setup mocks
        mock_config_sync_instance = MagicMock()
        mock_config_sync.return_value = mock_config_sync_instance
        
        # Mock available containers
        mock_config_sync_instance.get_available_containers.return_value = {
            "ubuntu": {
                "image": "ubuntu:latest",
                "description": "Ubuntu container",
                "shared": False,
                "resources": {"memory": "512m"}
            },
            "nginx": {
                "image": "nginx:latest",
                "description": "Nginx web server",
                "shared": True,
                "resources": {"memory": "256m"}
            }
        }
        
        # Create container manager
        container_manager = ContainerManager()
        
        # List available containers
        containers = container_manager.list_available_containers()
        
        # Verify force_sync was called
        mock_config_sync_instance.force_sync.assert_called_once()
        
        # Verify containers list format
        assert len(containers) == 2
        
        # Check ubuntu container info
        ubuntu = next(c for c in containers if c["name"] == "ubuntu")
        assert ubuntu["image"] == "ubuntu:latest"
        assert ubuntu["description"] == "Ubuntu container"
        assert ubuntu["shared"] is False
        
        # Check nginx container info
        nginx = next(c for c in containers if c["name"] == "nginx")
        assert nginx["image"] == "nginx:latest"
        assert nginx["description"] == "Nginx web server"
        assert nginx["shared"] is True
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    def test_list_running_containers(self, mock_config_sync, mock_docker):
        """Test listing running containers"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # Mock running containers
        container1 = MagicMock()
        container1.id = "container1_id_12345678"
        container1.name = "lsl-ubuntu-1234"
        container1.status = "running"
        container1.image.tags = ["ubuntu:latest"]
        container1.attrs = {"Created": "2023-06-01"}
        
        container2 = MagicMock()
        container2.id = "container2_id_87654321"
        container2.name = "other-container"  # Not an LSL container
        container2.status = "running"
        container2.image.tags = ["other:latest"]
        container2.attrs = {"Created": "2023-06-01"}
        
        container3 = MagicMock()
        container3.id = "container3_id_11223344"
        container3.name = "lsl-nginx-5678"
        container3.status = "exited"
        container3.image.tags = ["nginx:latest"]
        container3.attrs = {"Created": "2023-06-01"}
        
        mock_docker_client.containers.list.return_value = [container1, container2, container3]
        
        # Create container manager
        container_manager = ContainerManager()
        
        # List running containers
        containers = container_manager.list_running_containers()
        
        # Verify docker client was called with all=True
        mock_docker_client.containers.list.assert_called_once_with(all=True)
        
        # Verify only LSL containers are returned (excluding non-lsl container)
        assert len(containers) == 2
        
        # Check containers info
        container_names = [c["name"] for c in containers]
        assert "lsl-ubuntu-1234" in container_names
        assert "lsl-nginx-5678" in container_names
        assert "other-container" not in container_names
        
        # Check status is correctly reported
        running_container = next(c for c in containers if c["name"] == "lsl-ubuntu-1234")
        assert running_container["status"] == "running"
        assert running_container["is_running"] is True
        
        stopped_container = next(c for c in containers if c["name"] == "lsl-nginx-5678")
        assert stopped_container["status"] == "exited"
        assert stopped_container["is_running"] is False
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    @patch('client.containers.os')
    def test_start_container_success(self, mock_os, mock_config_sync, mock_docker):
        """Test successfully starting a container"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        mock_container = MagicMock()
        mock_docker_client.containers.run.return_value = mock_container
        
        mock_config_sync_instance = MagicMock()
        mock_config_sync.return_value = mock_config_sync_instance
        
        # Mock process ID
        mock_os.getpid.return_value = 12345
        
        # Mock available containers
        mock_config_sync_instance.get_available_containers.return_value = {
            "ubuntu": {
                "image": "ubuntu:latest",
                "description": "Ubuntu container",
                "shared": False,
                "volumes": [
                    "~/host-dir:/container-dir"
                ],
                "env": {
                    "VAR1": "value1"
                },
                "resources": {
                    "memory": "512m"
                }
            }
        }
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Start container
        success, message = container_manager.start_container(
            "ubuntu", 
            use_host_network=True, 
            persist_data=True
        )
        
        # Verify sync was called
        mock_config_sync_instance.force_sync.assert_called_once()
        
        # Verify success
        assert success is True
        assert "successfully" in message
        
        # Verify Docker client was called with correct parameters
        mock_docker_client.containers.run.assert_called_once()
        call_args = mock_docker_client.containers.run.call_args[1]
        
        assert call_args["image"] == "ubuntu:latest"
        assert call_args["name"] == "lsl-ubuntu-12345"
        assert call_args["detach"] is True
        assert call_args["network_mode"] == "host"
        assert call_args["environment"] == {"VAR1": "value1"}
        assert "memory" in call_args  # Resource limits passed through
        
        # Verify volumes handling
        assert len(call_args["volumes"]) >= 1  # At least one volume (could have persist volume too)
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    def test_start_container_not_in_config(self, mock_config_sync, mock_docker):
        """Test starting a container that doesn't exist in config"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        mock_config_sync_instance = MagicMock()
        mock_config_sync.return_value = mock_config_sync_instance
        
        # Empty container config
        mock_config_sync_instance.get_available_containers.return_value = {}
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Try to start non-existent container
        success, message = container_manager.start_container("nonexistent")
        
        # Verify failure
        assert success is False
        assert "not found" in message
        
        # Verify Docker client was not called
        mock_docker_client.containers.run.assert_not_called()
        
    @patch('client.containers.docker')
    @patch('client.containers.ConfigSyncManager')
    def test_start_container_docker_error(self, mock_config_sync, mock_docker):
        """Test error handling when Docker raises an exception"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # Docker raises an error
        mock_docker_client.containers.run.side_effect = mock_docker.errors.ImageNotFound("Image not found")
        
        mock_config_sync_instance = MagicMock()
        mock_config_sync.return_value = mock_config_sync_instance
        
        # Mock available containers
        mock_config_sync_instance.get_available_containers.return_value = {
            "ubuntu": {
                "image": "ubuntu:latest"
            }
        }
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Start container
        success, message = container_manager.start_container("ubuntu")
        
        # Verify failure
        assert success is False
        assert "Image not found" in message
        
    @patch('client.containers.docker')
    def test_stop_container_success(self, mock_docker):
        """Test successfully stopping containers"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # Mock containers
        container1 = MagicMock()
        container1.name = "lsl-ubuntu-1234"
        container1.status = "running"
        
        container2 = MagicMock()
        container2.name = "lsl-ubuntu-5678"
        container2.status = "running"
        
        mock_docker_client.containers.list.return_value = [container1, container2]
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Stop containers
        success, message = container_manager.stop_container("ubuntu")
        
        # Verify success
        assert success is True
        assert "Stopped 2 container" in message
        
        # Verify Docker client was called to list containers
        mock_docker_client.containers.list.assert_called_once_with(all=True)
        
        # Verify stop was called on each container
        container1.stop.assert_called_once()
        container2.stop.assert_called_once()
        
    @patch('client.containers.docker')
    def test_stop_container_no_match(self, mock_docker):
        """Test stopping containers with no matches"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # No matching containers
        mock_docker_client.containers.list.return_value = []
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Stop containers
        success, message = container_manager.stop_container("nonexistent")
        
        # Verify failure
        assert success is False
        assert "No containers found" in message
        
    @patch('client.containers.docker')
    def test_remove_container_success(self, mock_docker):
        """Test successfully removing containers"""
        # Setup mocks
        mock_docker_client = MagicMock()
        mock_docker.from_env.return_value = mock_docker_client
        
        # Mock containers
        container1 = MagicMock()
        container1.name = "lsl-ubuntu-1234"
        
        container2 = MagicMock()
        container2.name = "lsl-ubuntu-5678"
        
        mock_docker_client.containers.list.return_value = [container1, container2]
        
        # Create container manager
        container_manager = ContainerManager()
        
        # Remove containers
        success, message = container_manager.remove_container(
            "ubuntu", 
            force=True, 
            remove_volumes=True
        )
        
        # Verify success
        assert success is True
        assert "Removed 2 container" in message
        
        # Verify Docker client was called to list containers
        mock_docker_client.containers.list.assert_called_once_with(all=True)
        
        # Verify remove was called on each container with correct params
        container1.remove.assert_called_once_with(force=True, v=True)
        container2.remove.assert_called_once_with(force=True, v=True)
