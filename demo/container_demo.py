#!/usr/bin/env python3
"""
LSL Demo Script - Container Management

This script demonstrates the core container management capabilities of LSL,
including starting containers with different network modes and persistence options.
"""
import os
import sys
import time
from client.containers import ContainerManager
from shared.config import load_yaml_config
from shared.utils.yaml_logger import setup_logger
import subprocess

# Setup logging
logger = setup_logger("demo_containers", "logs/demo.log")

def setup_demo_environment():
    """Set up the demo environment"""
    # Ensure data directories exist
    data_dirs = [
        os.path.expanduser("~/lsl_data/dev_env"),
        os.path.expanduser("~/lsl_data/web_server"),
        os.path.expanduser("~/lsl_data/shared_terminal")
    ]
    for dir_path in data_dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Created data directory: {dir_path}")

def test_container_start(container_manager: ContainerManager, name: str, 
                        use_host_network: bool = False, persist_data: bool = True) -> bool:
    """Test starting a container with specified options"""
    logger.info(f"Starting container '{name}' (host_network={use_host_network}, persist={persist_data})")
    
    success, message = container_manager.start_container(
        name, 
        use_host_network=use_host_network,
        persist_data=persist_data
    )
    
    if success:
        logger.info(f"Successfully started container '{name}': {message}")
    else:
        logger.error(f"Failed to start container '{name}': {message}")
        
    return success

def run_host():
    print("[DEMO] Starting shared session as host...")
    subprocess.run(["python3", "lsl.py", "-n", "dev_env", "--host", "--share", "sharedSession1"])

def run_client(port):
    print(f"[DEMO] Joining shared session as client on port {port}...")
    subprocess.run(["python3", "lsl.py", "--share", f"127.0.0.1:{port}"])

def main():
    """Main demo function"""
    try:
        # Set up demo environment
        setup_demo_environment()
        logger.info("Set up demo environment")
        
        try:
            # Load and validate demo configuration
            load_yaml_config("config/demo-containers.yaml", "containers")
            logger.info("Loaded and validated demo configuration")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
        # Initialize container manager
        container_manager = ContainerManager()
        
        # Demo 1: Start development environment (host network)
        if not test_container_start(container_manager, "dev_env", use_host_network=True):
            sys.exit(1)
            
        time.sleep(2)  # Wait a bit between container operations
        
        # Demo 2: Start web server (bridge network)
        if not test_container_start(container_manager, "web_server", use_host_network=False):
            sys.exit(1)
        
        logger.info("Demo containers started successfully")
        print("\nDemo containers are now running!")
        print("1. dev_env: Development environment with host networking")
        print("2. web_server: Nginx server with bridge networking")
        print("\nTest the containers using the commands in demo/README.md")
        
        print("[DEMO] To run shared terminal session as host: python3 lsl.py -n dev_env --host --share sharedSession1")
        print("[DEMO] To join shared terminal session as client: python3 lsl.py --share 127.0.0.1:<PORT>")
        print("[DEMO] See README.md for more info.")
        
    except Exception as e:
        import traceback
        logger.error(f"Demo failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
