"""
Test module for YAML configuration operations in shared/config.py
"""
import unittest
import os
import tempfile
import yaml
import json
import shutil
import fcntl
import time
import threading
from unittest.mock import patch, MagicMock

# Import the module to test
from shared.config import (
    load_yaml_config, 
    save_yaml_config, 
    add_user,
    update_user,
    remove_user,
    add_container,
    update_container,
    remove_container,
    update_admin_credentials
)

class TestConfigOperations(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and config files for testing."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create paths for our test config files
        self.main_config_path = os.path.join(self.test_dir, 'main.yaml')
        self.users_config_path = os.path.join(self.test_dir, 'users.yaml')
        self.containers_config_path = os.path.join(self.test_dir, 'containers.yaml')
        
        # Set up test schema directory
        self.schema_dir = os.path.join(self.test_dir, 'schemas', 'definitions')
        os.makedirs(self.schema_dir, exist_ok=True)
        
        # Create test schemas
        self.create_test_schemas()
        
        # Set environment variable for test schemas
        os.environ['LSL_TEST_SCHEMA_DIR'] = self.schema_dir
        
        # Create test config files
        self.create_test_configs()
        
    def tearDown(self):
        """Clean up temporary files and directories after tests."""
        shutil.rmtree(self.test_dir)
        
    def create_test_schemas(self):
        """Create simplified test schemas."""
        # Main schema
        main_schema = {
            "type": "object",
            "required": ["server", "admin"],
            "properties": {
                "server": {
                    "type": "object",
                    "required": ["host", "port"],
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"}
                    }
                },
                "admin": {
                    "type": "object",
                    "required": ["username", "password_hash"],
                    "properties": {
                        "username": {"type": "string"},
                        "password_hash": {"type": "string"}
                    }
                }
            }
        }
        
        # Users schema
        users_schema = {
            "type": "object",
            "required": ["users"],
            "properties": {
                "users": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_-]+$": {
                            "type": "object",
                            "required": ["uuid", "password_hash"],
                            "properties": {
                                "uuid": {"type": "string"},
                                "password_hash": {"type": "string"},
                                "allowed_containers": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Containers schema
        containers_schema = {
            "type": "object",
            "required": ["containers"],
            "properties": {
                "containers": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_-]+$": {
                            "type": "object",
                            "required": ["image"],
                            "properties": {
                                "image": {"type": "string"},
                                "shared": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
        
        # Write schemas to files
        with open(os.path.join(self.schema_dir, 'main.json'), 'w') as f:
            json.dump(main_schema, f)
            
        with open(os.path.join(self.schema_dir, 'users.json'), 'w') as f:
            json.dump(users_schema, f)
            
        with open(os.path.join(self.schema_dir, 'containers.json'), 'w') as f:
            json.dump(containers_schema, f)
    
    def create_test_configs(self):
        """Create test config files with valid data."""
        # Main config
        main_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080
            },
            "admin": {
                "username": "admin",
                "password_hash": "pbkdf2-sha256$100000$abcdef1234567890$1234567890abcdef"
            }
        }
        
        # Users config
        users_config = {
            "users": {
                "testuser": {
                    "uuid": "12345678-1234-1234-1234-123456789012",
                    "password_hash": "pbkdf2-sha256$100000$abcdef1234567890$1234567890abcdef",
                    "allowed_containers": ["alpine", "ubuntu"]
                }
            }
        }
        
        # Containers config
        containers_config = {
            "containers": {
                "alpine": {
                    "image": "alpine:latest",
                    "shared": False
                },
                "ubuntu": {
                    "image": "ubuntu:22.04",
                    "shared": True
                }
            }
        }
        
        # Write configs to files
        with open(self.main_config_path, 'w') as f:
            yaml.dump(main_config, f)
            
        with open(self.users_config_path, 'w') as f:
            yaml.dump(users_config, f)
            
        with open(self.containers_config_path, 'w') as f:
            yaml.dump(containers_config, f)
    
    def test_load_yaml_config(self):
        """Test loading YAML config files."""
        # Test loading a valid config file
        config = load_yaml_config(self.main_config_path, 'main')
        self.assertIsInstance(config, dict)
        self.assertIn('server', config)
        self.assertIn('admin', config)
        self.assertEqual(config['server']['port'], 8080)
        
        # Test loading a non-existent file
        with self.assertRaises(ValueError):
            load_yaml_config(os.path.join(self.test_dir, 'nonexistent.yaml'), 'main')
            
        # Test loading an invalid format file
        invalid_path = os.path.join(self.test_dir, 'invalid.yaml')
        with open(invalid_path, 'w') as f:
            f.write("This is not valid YAML")
        with self.assertRaises(ValueError):
            load_yaml_config(invalid_path, 'main')
            
        # Test loading a valid file with invalid schema
        invalid_schema_path = os.path.join(self.test_dir, 'invalid_schema.yaml')
        with open(invalid_schema_path, 'w') as f:
            yaml.dump({"wrong_key": "value"}, f)
        with self.assertRaises(ValueError):
            load_yaml_config(invalid_schema_path, 'main')
    
    def test_save_yaml_config(self):
        """Test saving YAML config files."""
        # Modify the config and save it
        config = load_yaml_config(self.main_config_path, 'main')
        config['server']['port'] = 9090
        
        # Save the modified config
        save_yaml_config(self.main_config_path, config, 'main')
        
        # Load the config again and check if changes were saved
        reloaded_config = load_yaml_config(self.main_config_path, 'main')
        self.assertEqual(reloaded_config['server']['port'], 9090)
        
        # Test saving with validation error
        invalid_config = {
            "server": {
                "host": "0.0.0.0",
                # Missing required port
            },
            "admin": {
                "username": "admin",
                "password_hash": "pbkdf2-sha256$100000$abcdef1234567890$1234567890abcdef"
            }
        }
        with self.assertRaises(ValueError):
            save_yaml_config(self.main_config_path, invalid_config, 'main')
    
    def test_atomic_save(self):
        """Test that saving is atomic and doesn't corrupt files on error."""
        # Get initial content to compare against later
        with open(self.main_config_path, 'r') as f:
            initial_content = f.read()
        
        # Try to save invalid config (should fail)
        invalid_config = {"invalid": "config"}
        try:
            save_yaml_config(self.main_config_path, invalid_config, 'main')
        except ValueError:
            pass  # Expected error
            
        # Check that the file wasn't corrupted
        with open(self.main_config_path, 'r') as f:
            current_content = f.read()
        self.assertEqual(initial_content, current_content)
    
    def test_file_locking(self):
        """Test file locking during save operations."""
        # This test simulates concurrent access
        
        # Function to simulate another process trying to access the file
        def try_lock_file():
            try:
                with open(self.main_config_path, 'r+') as f:
                    # Try to acquire an exclusive lock, should fail if file is locked
                    fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
            except IOError:
                # Expected if file is locked
                return False
        
        # Start a save operation that takes some time
        config = load_yaml_config(self.main_config_path, 'main')
        
        # Mock the save operation to take some time and check locking
        original_open = open
        
        file_was_locked = [False]  # Using list to allow modification from nested function
        
        def mock_save(file_path, config, schema_name):
            with original_open(file_path, 'r+') as f:
                fcntl.lockf(f, fcntl.LOCK_EX)
                # Check if file is really locked
                file_was_locked[0] = not try_lock_file()
                time.sleep(0.1)  # Simulate work
                # Write the file
                f.seek(0)
                yaml.dump(config, f)
                f.truncate()
        
        with patch('shared.config.save_yaml_config', side_effect=mock_save):
            config['server']['port'] = 9999
            save_yaml_config(self.main_config_path, config, 'main')
            
        self.assertTrue(file_was_locked[0], "File should have been locked during save")
    
    def test_add_user(self):
        """Test adding a user to the users config."""
        # Add a new user
        new_user = {
            "uuid": "98765432-9876-9876-9876-987654321098",
            "password_hash": "pbkdf2-sha256$100000$0987654321$fedcba0987654321",
            "allowed_containers": ["alpine"]
        }
        add_user(self.users_config_path, "newuser", new_user)
        
        # Check if user was added
        users_config = load_yaml_config(self.users_config_path, 'users')
        self.assertIn("newuser", users_config["users"])
        self.assertEqual(users_config["users"]["newuser"]["uuid"], new_user["uuid"])
        
        # Test adding a user that already exists
        with self.assertRaises(ValueError):
            add_user(self.users_config_path, "newuser", new_user)
    
    def test_update_user(self):
        """Test updating a user in the users config."""
        # Update an existing user
        updated_data = {
            "allowed_containers": ["ubuntu"]
        }
        update_user(self.users_config_path, "testuser", updated_data)
        
        # Check if user was updated
        users_config = load_yaml_config(self.users_config_path, 'users')
        self.assertEqual(users_config["users"]["testuser"]["allowed_containers"], ["ubuntu"])
        
        # Test updating a non-existent user
        with self.assertRaises(ValueError):
            update_user(self.users_config_path, "nonexistent", updated_data)
    
    def test_remove_user(self):
        """Test removing a user from the users config."""
        # Remove a user
        remove_user(self.users_config_path, "testuser")
        
        # Check if user was removed
        users_config = load_yaml_config(self.users_config_path, 'users')
        self.assertNotIn("testuser", users_config["users"])
        
        # Test removing a non-existent user
        with self.assertRaises(ValueError):
            remove_user(self.users_config_path, "nonexistent")
    
    def test_add_container(self):
        """Test adding a container to the containers config."""
        # Add a new container
        new_container = {
            "image": "nginx:latest",
            "shared": True
        }
        add_container(self.containers_config_path, "nginx", new_container)
        
        # Check if container was added
        containers_config = load_yaml_config(self.containers_config_path, 'containers')
        self.assertIn("nginx", containers_config["containers"])
        self.assertEqual(containers_config["containers"]["nginx"]["image"], "nginx:latest")
        
        # Test adding a container that already exists
        with self.assertRaises(ValueError):
            add_container(self.containers_config_path, "nginx", new_container)
    
    def test_update_container(self):
        """Test updating a container in the containers config."""
        # Update an existing container
        updated_data = {
            "image": "alpine:3.16"
        }
        update_container(self.containers_config_path, "alpine", updated_data)
        
        # Check if container was updated
        containers_config = load_yaml_config(self.containers_config_path, 'containers')
        self.assertEqual(containers_config["containers"]["alpine"]["image"], "alpine:3.16")
        
        # Test updating a non-existent container
        with self.assertRaises(ValueError):
            update_container(self.containers_config_path, "nonexistent", updated_data)
    
    def test_remove_container(self):
        """Test removing a container from the containers config."""
        # Remove a container
        remove_container(self.containers_config_path, "alpine")
        
        # Check if container was removed
        containers_config = load_yaml_config(self.containers_config_path, 'containers')
        self.assertNotIn("alpine", containers_config["containers"])
        
        # Test removing a non-existent container
        with self.assertRaises(ValueError):
            remove_container(self.containers_config_path, "nonexistent")
    
    def test_update_admin_credentials(self):
        """Test updating admin credentials in the main config."""
        # Update admin credentials
        new_credentials = {
            "username": "newadmin",
            "password_hash": "pbkdf2-sha256$100000$adminadminadmin$adminadminadmin"
        }
        update_admin_credentials(self.main_config_path, new_credentials)
        
        # Check if credentials were updated
        main_config = load_yaml_config(self.main_config_path, 'main')
        self.assertEqual(main_config["admin"]["username"], "newadmin")
        self.assertEqual(main_config["admin"]["password_hash"], "pbkdf2-sha256$100000$adminadminadmin$adminadminadmin")
        
        # Test updating with invalid credentials
        invalid_credentials = {
            "username": "newadmin"
            # Missing password_hash
        }
        with self.assertRaises(ValueError):
            update_admin_credentials(self.main_config_path, invalid_credentials)


if __name__ == '__main__':
    unittest.main()
