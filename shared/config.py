"""
Configuration management module for LSL.

This module provides functions for:
- Loading and saving YAML configuration files
- Atomic writes with file locking
- CRUD operations for users and containers
- Updating admin credentials
"""
import os
import yaml
import fcntl
import tempfile
import shutil
from typing import Dict, Any, List, Optional

from shared.schemas.validator import validate_yaml, load_and_validate_yaml_file

def load_yaml_config(file_path: str, schema_name: str) -> Dict[str, Any]:
    """
    Load and validate a YAML configuration file.
    
    Args:
        file_path (str): Path to the YAML file
        schema_name (str): Name of the schema to validate against
        
    Returns:
        Dict[str, Any]: Loaded and validated configuration
        
    Raises:
        ValueError: If file doesn't exist, contains invalid YAML, or fails validation
    """
    # Load and validate the file
    data, is_valid, error = load_and_validate_yaml_file(schema_name, file_path)
    
    if not is_valid:
        raise ValueError(f"Configuration file {file_path} failed validation: {error}")
        
    return data

def save_yaml_config(file_path: str, config: Dict[str, Any], schema_name: str) -> None:
    """
    Save configuration to a YAML file with file locking and atomic write.
    
    Args:
        file_path (str): Path to the YAML file
        config (Dict[str, Any]): Configuration data to save
        schema_name (str): Name of the schema to validate against
        
    Raises:
        ValueError: If configuration fails schema validation
    """
    # Validate the config before saving
    is_valid, error = validate_yaml(schema_name, config)
    if not is_valid:
        raise ValueError(f"Invalid configuration: {error}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    # Create a temporary file in the same directory
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(file_path)))
    
    try:
        # Close the file descriptor returned by mkstemp
        os.close(temp_fd)
        
        # Write the config to the temporary file
        with open(temp_path, 'w') as temp_file:
            yaml.dump(config, temp_file, default_flow_style=False)
            
        # Move the temporary file to the target location (atomic)
        shutil.move(temp_path, file_path)
        
        # Set permissions (rw-r--r--)
        os.chmod(file_path, 0o644)
        
    except Exception as e:
        # Clean up the temporary file if anything goes wrong
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise ValueError(f"Error saving configuration: {e}")

def _atomic_yaml_update(file_path: str, schema_name: str, 
                        update_func: callable, lock_mode: int = fcntl.LOCK_EX) -> Dict[str, Any]:
    """
    Helper function for atomic updates to YAML config files with locking.
    
    Args:
        file_path (str): Path to the YAML file
        schema_name (str): Name of the schema to validate against
        update_func (callable): Function that takes the config dict and updates it
        lock_mode (int, optional): File locking mode. Defaults to exclusive lock.
        
    Returns:
        Dict[str, Any]: Updated configuration
        
    Raises:
        ValueError: If file can't be read/written or configuration is invalid
    """
    # Create the file if it doesn't exist
    if not os.path.exists(file_path):
        # Create a minimal valid config based on schema requirements
        if schema_name == 'users':
            initial_config = {"users": {}}
        elif schema_name == 'containers':
            initial_config = {"containers": {}}
        else:
            raise ValueError(f"Cannot create a new config file for schema: {schema_name}")
            
        save_yaml_config(file_path, initial_config, schema_name)
    
    # Open the file for reading and writing
    with open(file_path, 'r+') as f:
        # Acquire lock
        fcntl.lockf(f, lock_mode)
        
        try:
            # Read the current config
            config = yaml.safe_load(f) or {}
            
            # Call the update function
            updated_config = update_func(config)
            
            # Write the updated config back to the file
            f.seek(0)
            yaml.dump(updated_config, f, default_flow_style=False)
            f.truncate()
            
            return updated_config
            
        finally:
            # Release the lock (happens automatically when the file is closed)
            pass

# User operations

def add_user(users_file: str, username: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a user to the users configuration.
    
    Args:
        users_file (str): Path to the users YAML file
        username (str): Username of the user to add
        user_data (Dict[str, Any]): User data
        
    Returns:
        Dict[str, Any]: Updated users configuration
        
    Raises:
        ValueError: If username already exists or data is invalid
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "users" in config:
            config["users"] = {}
        
        if username in config["users"]:
            raise ValueError(f"User '{username}' already exists")
        
        # Add the user
        config["users"][username] = user_data
        return config
    
    return _atomic_yaml_update(users_file, 'users', update_config)

def update_user(users_file: str, username: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a user in the users configuration.
    
    Args:
        users_file (str): Path to the users YAML file
        username (str): Username of the user to update
        user_data (Dict[str, Any]): User data to update
        
    Returns:
        Dict[str, Any]: Updated users configuration
        
    Raises:
        ValueError: If username doesn't exist or data is invalid
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "users" in config or username not in config["users"]:
            raise ValueError(f"User '{username}' does not exist")
        
        # Update the user
        for key, value in user_data.items():
            config["users"][username][key] = value
        
        return config
    
    return _atomic_yaml_update(users_file, 'users', update_config)

def remove_user(users_file: str, username: str) -> Dict[str, Any]:
    """
    Remove a user from the users configuration.
    
    Args:
        users_file (str): Path to the users YAML file
        username (str): Username of the user to remove
        
    Returns:
        Dict[str, Any]: Updated users configuration
        
    Raises:
        ValueError: If username doesn't exist
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "users" in config or username not in config["users"]:
            raise ValueError(f"User '{username}' does not exist")
        
        # Remove the user
        del config["users"][username]
        return config
    
    return _atomic_yaml_update(users_file, 'users', update_config)

# Container operations

def add_container(containers_file: str, container_name: str, container_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a container to the containers configuration.
    
    Args:
        containers_file (str): Path to the containers YAML file
        container_name (str): Name of the container to add
        container_data (Dict[str, Any]): Container data
        
    Returns:
        Dict[str, Any]: Updated containers configuration
        
    Raises:
        ValueError: If container already exists or data is invalid
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "containers" in config:
            config["containers"] = {}
        
        if container_name in config["containers"]:
            raise ValueError(f"Container '{container_name}' already exists")
        
        # Add the container
        config["containers"][container_name] = container_data
        return config
    
    return _atomic_yaml_update(containers_file, 'containers', update_config)

def update_container(containers_file: str, container_name: str, container_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a container in the containers configuration.
    
    Args:
        containers_file (str): Path to the containers YAML file
        container_name (str): Name of the container to update
        container_data (Dict[str, Any]): Container data to update
        
    Returns:
        Dict[str, Any]: Updated containers configuration
        
    Raises:
        ValueError: If container doesn't exist or data is invalid
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "containers" in config or container_name not in config["containers"]:
            raise ValueError(f"Container '{container_name}' does not exist")
        
        # Update the container
        for key, value in container_data.items():
            config["containers"][container_name][key] = value
        
        return config
    
    return _atomic_yaml_update(containers_file, 'containers', update_config)

def remove_container(containers_file: str, container_name: str) -> Dict[str, Any]:
    """
    Remove a container from the containers configuration.
    
    Args:
        containers_file (str): Path to the containers YAML file
        container_name (str): Name of the container to remove
        
    Returns:
        Dict[str, Any]: Updated containers configuration
        
    Raises:
        ValueError: If container doesn't exist
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "containers" in config or container_name not in config["containers"]:
            raise ValueError(f"Container '{container_name}' does not exist")
        
        # Remove the container
        del config["containers"][container_name]
        return config
    
    return _atomic_yaml_update(containers_file, 'containers', update_config)

# Admin credentials operations

def update_admin_credentials(main_file: str, admin_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update admin credentials in the main configuration.
    
    Args:
        main_file (str): Path to the main YAML file
        admin_data (Dict[str, Any]): Admin credentials data
        
    Returns:
        Dict[str, Any]: Updated main configuration
        
    Raises:
        ValueError: If data is invalid
    """
    def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
        if not "admin" in config:
            config["admin"] = {}
        
        # Required fields for admin
        if "username" not in admin_data or "password_hash" not in admin_data:
            raise ValueError("Admin credentials must include 'username' and 'password_hash'")
        
        # Update admin credentials
        config["admin"].update(admin_data)
        return config
    
    return _atomic_yaml_update(main_file, 'main', update_config)
