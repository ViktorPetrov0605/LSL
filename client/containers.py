"""
Container Management Module

This module handles container operations including:
- Starting containers
- Stopping containers
- Removing containers
- Error handling for Docker operations
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple

import docker
from docker.errors import APIError, ImageNotFound, NotFound

# Use absolute imports for better compatibility
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.config import get_client_config, ClientConfig
from client.sync import ConfigSyncManager
from shared.utils.yaml_logger import setup_logger

# Initialize logger
logger = setup_logger("container_manager", "/tmp/lsl_client.log")

class ContainerManager:
    """Container management class for LSL client"""
    
    def __init__(self, client_config: Optional[ClientConfig] = None):
        """
        Initialize container manager
        
        Args:
            client_config: Optional ClientConfig instance, will create one if not provided
        """
        self.client_config = client_config or get_client_config()
        self.config_sync = ConfigSyncManager(self.client_config)
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self.docker_client = None
            
    def _check_docker_availability(self) -> bool:
        """
        Check if Docker is available
        
        Returns:
            True if Docker is available, False otherwise
        """
        if self.docker_client is None:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Docker is not available: {str(e)}")
                return False
                
        try:
            # Check Docker connection
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker connection error: {str(e)}")
            return False
            
    def _format_error_message(self, error: Exception) -> str:
        """
        Format a user-friendly error message from Docker exception
        
        Args:
            error: Docker exception
            
        Returns:
            User-friendly error message
        """
        if isinstance(error, ImageNotFound):
            return f"Docker image not found. Please check the image name or pull it first."
        elif isinstance(error, NotFound):
            return f"Container or resource not found."
        elif isinstance(error, APIError):
            # Extract the most relevant part of the API error
            msg = str(error)
            if "permission denied" in msg.lower():
                return "Permission denied. You may need to run with sudo or add your user to the docker group."
            elif "conflict" in msg.lower():
                return "Name conflict. A container with this name may already exist."
            else:
                return f"Docker API error: {msg}"
        else:
            return f"Docker error: {str(error)}"
    
    def list_available_containers(self) -> List[Dict[str, Any]]:
        """
        List containers available to the user
        
        Returns:
            List of available container configurations
        """
        # Force sync to ensure we have latest container list
        self.config_sync.force_sync()
        
        # Get container configurations from server config
        containers_dict = self.config_sync.get_available_containers()
        
        # Convert to list format for easier display
        containers_list = []
        for name, config in containers_dict.items():
            container_info = {
                "name": name,
                "image": config.get("image", "unknown"),
                "description": config.get("description", ""),
                "shared": config.get("shared", False),
                "resources": config.get("resources", {})
            }
            containers_list.append(container_info)
            
        return containers_list
        
    def list_running_containers(self) -> List[Dict[str, Any]]:
        """
        List running LSL containers
        
        Returns:
            List of running container information
        """
        if not self._check_docker_availability():
            logger.error("Docker is not available")
            return []
            
        try:
            # Get LSL-managed containers
            all_containers = self.docker_client.containers.list(all=True)
            lsl_containers = [c for c in all_containers if c.name.startswith("lsl-")]
            
            result = []
            for container in lsl_containers:
                # Extract basic info
                info = {
                    "id": container.id[:12],  # Short ID
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "status": container.status,
                    "created": container.attrs.get("Created", ""),
                    "is_running": container.status == "running"
                }
                result.append(info)
                
            return result
            
        except Exception as e:
            error_msg = self._format_error_message(e)
            logger.error(f"Error listing containers: {error_msg}")
            return []
            
    def start_container(self, container_name: str, use_host_network: bool = False, 
                       persist_data: bool = False) -> Tuple[bool, str]:
        """
        Start a container by name
        
        Args:
            container_name: Name of the container to start (as defined in server config)
            use_host_network: Whether to use host networking
            persist_data: Whether to persist container data in volumes
            
        Returns:
            Tuple of (success, message)
        """
        if not self._check_docker_availability():
            return False, "Docker is not available"
            
        # Get container config
        self.config_sync.force_sync()
        containers_dict = self.config_sync.get_available_containers()
        
        # Check if container exists in config
        if container_name not in containers_dict:
            return False, f"Container '{container_name}' not found in available containers"
            
        container_config = containers_dict[container_name]
        
        try:
            # Prepare container parameters
            image = container_config.get("image")
            if not image:
                return False, f"No image specified for container '{container_name}'"
                
            # Create unique container name
            unique_name = f"lsl-{container_name}-{os.getpid()}"
            
            # Prepare volumes
            volumes = {}
            if container_config.get("volumes"):
                for vol in container_config["volumes"]:
                    # Parse volume string (host:container:mode)
                    parts = vol.split(":")
                    if len(parts) >= 2:
                        host_path, container_path = parts[0], parts[1]
                        # Expand user home directory if needed
                        if host_path.startswith("~"):
                            host_path = os.path.expanduser(host_path)
                        # Create host directory if it doesn't exist
                        if not os.path.exists(host_path):
                            os.makedirs(host_path, exist_ok=True)
                        volumes[host_path] = {'bind': container_path, 'mode': 'rw'}
            
            # Add persistent volume if requested
            if persist_data:
                persist_path = os.path.expanduser(f"~/.lsl/data/{container_name}")
                os.makedirs(persist_path, exist_ok=True)
                volumes[persist_path] = {'bind': '/data', 'mode': 'rw'}
                
            # Network config
            network_mode = "host" if use_host_network else None
            
            # Environment variables
            environment = container_config.get("env", {})
            
            # Resource limits
            resource_limits = container_config.get("resources", {})
            
            # Start container
            container = self.docker_client.containers.run(
                image=image,
                name=unique_name,
                detach=True,
                volumes=volumes,
                network_mode=network_mode,
                environment=environment,
                **resource_limits  # memory, cpu_shares, etc.
            )
            
            # Handle tmux/screen setup for shared containers
            is_shared = container_config.get("shared", False)
            if is_shared:
                # Here you would set up tmux/screen inside the container
                # This would require executing commands in the container
                pass
                
            logger.info(f"Started container {unique_name} from image {image}")
            return True, f"Container '{unique_name}' started successfully"
            
        except Exception as e:
            error_msg = self._format_error_message(e)
            logger.error(f"Error starting container: {error_msg}")
            return False, f"Failed to start container: {error_msg}"
            
    def stop_container(self, container_name: str) -> Tuple[bool, str]:
        """
        Stop a running container
        
        Args:
            container_name: Name of the container to stop
            
        Returns:
            Tuple of (success, message)
        """
        if not self._check_docker_availability():
            return False, "Docker is not available"
            
        # Check if container name is a prefix or exact match
        try:
            all_containers = self.docker_client.containers.list(all=True)
            matching_containers = [c for c in all_containers 
                                 if c.name == container_name or 
                                    c.name.startswith(f"lsl-{container_name}-")]
            
            if not matching_containers:
                return False, f"No containers found matching '{container_name}'"
                
            # Stop all matching containers
            for container in matching_containers:
                if container.status == "running":
                    logger.info(f"Stopping container {container.name}")
                    container.stop(timeout=10)
                else:
                    logger.info(f"Container {container.name} is already stopped")
                    
            return True, f"Stopped {len(matching_containers)} container(s)"
            
        except Exception as e:
            error_msg = self._format_error_message(e)
            logger.error(f"Error stopping container: {error_msg}")
            return False, f"Failed to stop container: {error_msg}"
            
    def remove_container(self, container_name: str, force: bool = False, 
                        remove_volumes: bool = False) -> Tuple[bool, str]:
        """
        Remove a container
        
        Args:
            container_name: Name of the container to remove
            force: Force removal even if running
            remove_volumes: Whether to remove associated volumes
            
        Returns:
            Tuple of (success, message)
        """
        if not self._check_docker_availability():
            return False, "Docker is not available"
            
        try:
            all_containers = self.docker_client.containers.list(all=True)
            matching_containers = [c for c in all_containers 
                                 if c.name == container_name or 
                                    c.name.startswith(f"lsl-{container_name}-")]
            
            if not matching_containers:
                return False, f"No containers found matching '{container_name}'"
                
            # Remove all matching containers
            for container in matching_containers:
                logger.info(f"Removing container {container.name}")
                container.remove(force=force, v=remove_volumes)
                
            return True, f"Removed {len(matching_containers)} container(s)"
            
        except Exception as e:
            error_msg = self._format_error_message(e)
            logger.error(f"Error removing container: {error_msg}")
            return False, f"Failed to remove container: {error_msg}"
