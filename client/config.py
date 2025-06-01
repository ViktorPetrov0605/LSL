"""
Client Configuration Module

This module handles client configuration including:
- UUID/token generation and persistence
- Fetching and syncing configuration from the LSL server
- Local config file management
"""
import os
import yaml
import uuid
import logging
import time
import requests
import json
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from shared.utils.uuid_hash import generate_uuid
from shared.utils.yaml_logger import setup_logger

# Initialize logger
logger = setup_logger("client_config", "/tmp/lsl_client.log")

# Default paths
DEFAULT_CONFIG_LOCATIONS = [
    os.path.expanduser("~/.config/lsl/config.yaml"),  # XDG config dir
    os.path.expanduser("~/lsl_config.yaml"),          # User home
    "config.yaml"                                     # Current directory
]

class ClientConfig:
    """Client configuration management class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize client configuration
        
        Args:
            config_path: Optional path to config file. If not provided,
                        will search in default locations
        """
        self.config_path = self._find_config_path(config_path)
        self.config = self._load_or_create_config()
        
    def _find_config_path(self, config_path: Optional[str] = None) -> str:
        """
        Find the configuration file path
        
        Args:
            config_path: Optional explicit path to config file
            
        Returns:
            Path to the config file (existing or to be created)
        """
        # If path is explicitly provided, use it
        if config_path:
            return config_path
            
        # Check default locations for existing config
        for path in DEFAULT_CONFIG_LOCATIONS:
            if os.path.exists(path):
                logger.info(f"Found existing config at: {path}")
                return path
                
        # No existing config found, create in XDG config dir
        xdg_config_path = DEFAULT_CONFIG_LOCATIONS[0]
        os.makedirs(os.path.dirname(xdg_config_path), exist_ok=True)
        logger.info(f"Creating new config at: {xdg_config_path}")
        return xdg_config_path
        
    def _load_or_create_config(self) -> Dict[str, Any]:
        """
        Load existing config or create a new one
        
        Returns:
            The configuration dictionary
        """
        try:
            # Try to load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Validate loaded config
                if not self._validate_config(config):
                    logger.warning("Config validation failed, creating new config")
                    config = self._generate_new_config()
                
                return config
            else:
                # No config found, generate new one
                return self._generate_new_config()
                
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Error loading config: {str(e)}, creating new config")
            return self._generate_new_config()

    def _generate_new_config(self) -> Dict[str, Any]:
        """
        Generate a new client configuration with UUID and token
        
        Returns:
            New configuration dictionary
        """
        # Generate new UUID and token
        client_uuid = generate_uuid()
        client_token = uuid.uuid4().hex
        
        config = {
            "client": {
                "uuid": client_uuid,
                "token": client_token,
                "created_at": time.time(),
                "last_server_sync": None
            },
            "server": {
                "url": "http://localhost:8000",  # Default server URL
                "ping_interval": 60,             # Default ping interval in seconds
            },
            "settings": {
                "container_cache_dir": os.path.expanduser("~/.cache/lsl/containers"),
                "log_level": "INFO"
            }
        }
        
        # Save the new configuration
        self._save_config(config)
        logger.info(f"Generated new client UUID: {client_uuid}")
        
        return config
        
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary to save
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Create temporary file path
        temp_path = f"{self.config_path}.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            # Atomic replace
            if os.path.exists(temp_path):
                os.replace(temp_path, self.config_path)
                logger.info(f"Configuration saved to {self.config_path}")
            else:
                logger.error("Failed to write temporary config file")
                
        except IOError as e:
            logger.error(f"Error saving config: {str(e)}")
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ["client", "server", "settings"]
        required_client_fields = ["uuid", "token"]
        
        # Check required sections
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required section: {section}")
                return False
                
        # Check required client fields
        for field in required_client_fields:
            if field not in config["client"]:
                logger.error(f"Missing required client field: {field}")
                return False
                
        return True
        
    def get_uuid_and_token(self) -> Tuple[str, str]:
        """
        Get client UUID and token
        
        Returns:
            Tuple of (UUID, token)
        """
        return self.config["client"]["uuid"], self.config["client"]["token"]
        
    def get_server_url(self) -> str:
        """
        Get server URL
        
        Returns:
            Server URL string
        """
        return self.config["server"].get("url", "http://localhost:8000")
        
    def update_server_url(self, url: str) -> None:
        """
        Update server URL
        
        Args:
            url: New server URL
        """
        self.config["server"]["url"] = url
        self._save_config(self.config)
        
    def sync_with_server(self) -> bool:
        """
        Sync configuration with server
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            uuid, token = self.get_uuid_and_token()
            server_url = self.get_server_url()
            
            # Prepare request headers
            headers = {
                "Authorization": f"Bearer {uuid}:{token}",
                "Content-Type": "application/json"
            }
            
            # Request config from server
            response = requests.get(
                f"{server_url}/get_config",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                # Update last sync timestamp
                self.config["client"]["last_server_sync"] = time.time()
                
                # Save server config
                server_config = response.json()
                
                # Update local cache
                if "server_config" not in self.config:
                    self.config["server_config"] = {}
                    
                self.config["server_config"] = server_config
                self._save_config(self.config)
                
                logger.info("Successfully synced configuration with server")
                return True
            else:
                logger.error(f"Failed to sync config: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error communicating with server: {str(e)}")
            return False
            
    def reset_config(self) -> None:
        """Reset client configuration by generating a new UUID and token"""
        self.config = self._generate_new_config()
        logger.warning("Client configuration has been reset")
        

# Convenience function to get a client config instance
def get_client_config(config_path: Optional[str] = None) -> ClientConfig:
    """
    Get client configuration instance
    
    Args:
        config_path: Optional explicit path to config file
        
    Returns:
        ClientConfig instance
    """
    return ClientConfig(config_path)
