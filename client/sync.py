"""
Config Sync Module

This module handles the synchronization of client configuration with the LSL server,
including fetching container configurations and keeping them updated.
"""
import os
import time
import threading
import logging
from typing import Optional, Dict, Any

import requests

from client.config import get_client_config, ClientConfig
from shared.utils.yaml_logger import setup_logger

# Initialize logger
logger = setup_logger("config_sync", "/tmp/lsl_client.log")

class ConfigSyncManager:
    """
    Configuration Synchronization Manager
    
    Handles periodic syncing of client configuration with the server
    """
    
    def __init__(self, client_config: Optional[ClientConfig] = None):
        """
        Initialize the config sync manager
        
        Args:
            client_config: Optional ClientConfig instance, will create one if not provided
        """
        self.client_config = client_config or get_client_config()
        self.sync_thread = None
        self.stop_event = threading.Event()
        self.sync_interval = self.client_config.config["server"].get("ping_interval", 60)
        
    def start_sync_thread(self) -> None:
        """
        Start the configuration sync thread
        """
        if self.sync_thread is not None and self.sync_thread.is_alive():
            logger.warning("Sync thread is already running")
            return
            
        self.stop_event.clear()
        self.sync_thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="ConfigSyncThread"
        )
        self.sync_thread.start()
        logger.info("Started configuration sync thread")
        
    def stop_sync_thread(self) -> None:
        """
        Stop the configuration sync thread
        """
        if self.sync_thread is None or not self.sync_thread.is_alive():
            logger.warning("No sync thread running")
            return
            
        self.stop_event.set()
        self.sync_thread.join(timeout=5.0)
        if self.sync_thread.is_alive():
            logger.warning("Sync thread did not terminate gracefully")
        else:
            logger.info("Stopped configuration sync thread")
            
    def _sync_loop(self) -> None:
        """
        Background thread loop for periodic configuration syncing
        """
        while not self.stop_event.is_set():
            # Sync configuration with server
            try:
                self._sync_and_ping()
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                
            # Wait for the next sync interval or until stopped
            self.stop_event.wait(self.sync_interval)
            
    def _sync_and_ping(self) -> None:
        """
        Perform configuration sync and server ping
        """
        server_url = self.client_config.get_server_url()
        uuid, token = self.client_config.get_uuid_and_token()
        
        # Prepare auth headers
        headers = {
            "Authorization": f"Bearer {uuid}:{token}",
            "Content-Type": "application/json"
        }
        
        try:
            # 1. Sync full config
            self.client_config.sync_with_server()
            
            # 2. Send ping to update last-seen timestamp
            ping_response = requests.post(
                f"{server_url}/ping",
                headers=headers,
                json={"uuid": uuid},
                timeout=5
            )
            
            if ping_response.status_code == 200:
                logger.debug("Successfully pinged server")
            else:
                logger.error(f"Ping failed with status code: {ping_response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Error communicating with server: {str(e)}")
            
    def force_sync(self) -> bool:
        """
        Force an immediate configuration sync with the server
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            success = self.client_config.sync_with_server()
            if success:
                logger.info("Forced config sync successful")
            else:
                logger.warning("Forced config sync failed")
            return success
        except Exception as e:
            logger.error(f"Error during forced sync: {str(e)}")
            return False
            
    def get_available_containers(self) -> Dict[str, Any]:
        """
        Get list of containers available to this user
        
        Returns:
            Dictionary of container configurations
        """
        if "server_config" not in self.client_config.config:
            logger.warning("No server configuration available, forcing sync")
            self.force_sync()
            
        server_config = self.client_config.config.get("server_config", {})
        return server_config.get("containers", {})
