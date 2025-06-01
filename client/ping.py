"""
Ping Thread Module

This module implements the background ping thread that keeps the server
informed about the client's online status.
"""
import os
import time
import threading
import logging
import random
from typing import Optional

import requests

# Use absolute imports for better compatibility
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.config import get_client_config, ClientConfig
from shared.utils.yaml_logger import setup_logger

# Initialize logger
logger = setup_logger("ping_thread", "/tmp/lsl_client.log")

class PingManager:
    """
    Client Ping Manager
    
    Handles sending periodic ping signals to the LSL server to update 
    the client's last seen timestamp.
    """
    
    def __init__(self, client_config: Optional[ClientConfig] = None):
        """
        Initialize the ping manager
        
        Args:
            client_config: Optional ClientConfig instance, will create one if not provided
        """
        self.client_config = client_config or get_client_config()
        self.ping_thread = None
        self.stop_event = threading.Event()
        
        # Default ping interval from config (60 seconds)
        self.ping_interval = self.client_config.config["server"].get("ping_interval", 60)
        
        # Retry settings
        self.max_retries = 5
        self.initial_retry_delay = 1.0  # seconds
        self.max_retry_delay = 60.0    # seconds
        
    def start_ping_thread(self) -> None:
        """
        Start the background ping thread
        """
        if self.ping_thread is not None and self.ping_thread.is_alive():
            logger.warning("Ping thread is already running")
            return
            
        self.stop_event.clear()
        self.ping_thread = threading.Thread(
            target=self._ping_loop,
            daemon=True,
            name="PingThread"
        )
        self.ping_thread.start()
        logger.info("Started background ping thread")
        
    def stop_ping_thread(self) -> None:
        """
        Stop the background ping thread
        """
        if self.ping_thread is None or not self.ping_thread.is_alive():
            logger.warning("No ping thread running")
            return
            
        self.stop_event.set()
        self.ping_thread.join(timeout=5.0)
        if self.ping_thread.is_alive():
            logger.warning("Ping thread did not terminate gracefully")
        else:
            logger.info("Stopped background ping thread")
            
    def _ping_loop(self) -> None:
        """
        Background thread loop for periodic pings
        """
        while not self.stop_event.is_set():
            # Send ping to server
            success = self._send_ping_with_retry()
            
            if not success:
                logger.error("Failed to ping server after multiple retries")
                
            # Wait for next ping interval or until stopped
            self.stop_event.wait(self.ping_interval)
    
    def _send_ping_with_retry(self) -> bool:
        """
        Send ping to server with exponential backoff retry
        
        Returns:
            True if ping was successful, False otherwise
        """
        server_url = self.client_config.get_server_url()
        uuid, token = self.client_config.get_uuid_and_token()
        
        # Prepare auth headers
        headers = {
            "Authorization": f"Bearer {uuid}:{token}",
            "Content-Type": "application/json"
        }
        
        retry_delay = self.initial_retry_delay
        
        # Try to ping the server with exponential backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    f"{server_url}/ping",
                    headers=headers,
                    json={"uuid": uuid},
                    timeout=5
                )
                
                if response.status_code == 200:
                    return True
                    
                logger.warning(f"Ping failed with status code: {response.status_code}")
                
            except requests.RequestException as e:
                logger.warning(f"Ping attempt {attempt}/{self.max_retries} failed: {str(e)}")
            
            # Only sleep if we're going to retry
            if attempt < self.max_retries:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.8, 1.2)
                sleep_time = retry_delay * jitter
                
                logger.debug(f"Retrying ping in {sleep_time:.2f} seconds")
                
                # Check if we should stop before sleeping
                if self.stop_event.wait(sleep_time):
                    return False
                    
                # Exponential backoff
                retry_delay = min(retry_delay * 2, self.max_retry_delay)
        
        # All retries failed
        return False
        
    def send_immediate_ping(self) -> bool:
        """
        Send an immediate ping to the server
        
        Returns:
            True if ping was successful, False otherwise
        """
        return self._send_ping_with_retry()
