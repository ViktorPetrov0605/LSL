#!/usr/bin/env python3
"""
LSL Demo Client

A simplified client for demonstrating the LSL client-server architecture.
"""
import os
import sys
import argparse
import requests
import time
import json
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_header(message: str) -> None:
    """Print a formatted header message"""
    border = '=' * (len(message) + 4)
    print(f"\n{border}")
    print(f"| {message} |")
    print(f"{border}\n")

class DemoClient:
    """A simplified client for the LSL demo"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.connected = False
        self.client_id = f"demo-client-{int(time.time())}"
    
    def connect(self) -> bool:
        """Connect to the LSL server"""
        try:
            response = requests.get(f"{self.server_url}/ping")
            if response.status_code == 200:
                self.connected = True
                print(f"Successfully connected to LSL server at {self.server_url}")
                return True
            else:
                print(f"Failed to connect to server: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get configuration from the server"""
        if not self.connected:
            print("Not connected to server. Call connect() first.")
            return {}
        
        try:
            response = requests.get(
                f"{self.server_url}/get_config",
                headers={"X-Client-ID": self.client_id}
            )
            if response.status_code == 200:
                data = response.json()
                print("Retrieved configuration from server:")
                return data
            else:
                print(f"Failed to get config: HTTP {response.status_code}")
                return {}
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return {}
    
    def register_container(self, name: str, config: Dict[str, Any]) -> bool:
        """Register a container with the server"""
        if not self.connected:
            print("Not connected to server. Call connect() first.")
            return False
        
        try:
            payload = {
                "name": name,
                "config": config,
                "client_id": self.client_id
            }
            response = requests.post(
                f"{self.server_url}/register_container",
                json=payload,
                headers={"X-Client-ID": self.client_id}
            )
            if response.status_code == 200:
                print(f"Container '{name}' registered with server")
                return True
            else:
                print(f"Failed to register container: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return False
    
    def send_status_update(self) -> None:
        """Send a status update to the server"""
        if not self.connected:
            return
        
        try:
            payload = {
                "client_id": self.client_id,
                "status": "active",
                "timestamp": time.time(),
                "containers": ["demo-container-1", "demo-container-2"],
                "resources": {
                    "cpu_percent": 15.2,
                    "memory_percent": 32.8,
                    "disk_percent": 45.1
                }
            }
            
            response = requests.post(
                f"{self.server_url}/status_update",
                json=payload,
                headers={"X-Client-ID": self.client_id}
            )
            
            if response.status_code != 200:
                print(f"Failed to send status update: HTTP {response.status_code}")
        except requests.RequestException as e:
            print(f"Request error: {e}")

def run_demo_client(server_url: str) -> None:
    """Run the demo client"""
    print_header("LSL DEMO CLIENT")
    
    client = DemoClient(server_url)
    
    # Connect to server
    if not client.connect():
        print("Failed to connect to server. Exiting.")
        return
    
    # Get configuration
    config = client.get_config()
    print(json.dumps(config, indent=2))
    
    # Register demo containers
    demo_containers = {
        "dev_env": {
            "image": "ubuntu:22.04",
            "network": "host",
            "persist": True,
            "volume_path": "/data"
        },
        "web_server": {
            "image": "nginx:alpine",
            "network": "bridge",
            "ports": ["8080:80"],
            "persist": True
        }
    }
    
    for name, container_config in demo_containers.items():
        client.register_container(name, container_config)
    
    # Send regular status updates
    print("Sending status updates every 5 seconds...")
    try:
        while True:
            client.send_status_update()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nClient stopped.")

def main() -> None:
    parser = argparse.ArgumentParser(description="LSL Demo Client")
    parser.add_argument("--server", default="http://localhost:8080",
                        help="URL of the LSL server")
    
    args = parser.parse_args()
    run_demo_client(args.server)

if __name__ == "__main__":
    main()
