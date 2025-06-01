"""
Test module for YAML logging utilities in shared/utils/yaml_logger.py
"""
import unittest
import os
import tempfile
import yaml
import logging
import shutil
from unittest.mock import patch, MagicMock

# Import the module to test
from shared.utils.yaml_logger import YAMLLogger, setup_logger, get_logger

class TestYAMLLogger(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for log files."""
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test.log")
        
    def tearDown(self):
        """Clean up temporary files after tests."""
        shutil.rmtree(self.test_dir)
        
    def test_yaml_formatter(self):
        """Test that log entries are properly formatted as YAML."""
        # Setup logger with YAMLLogger
        logger = setup_logger("test_logger", self.log_file)
        
        # Log a test message
        test_message = "Test log message"
        logger.info(test_message)
        
        # Read the log file
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Parse YAML content
        log_entries = list(yaml.safe_load_all(log_content))
        
        # Check if the log entry has the correct format
        self.assertEqual(len(log_entries), 1)
        entry = log_entries[0]
        
        # Check required fields
        self.assertIn('timestamp', entry)
        self.assertIn('level', entry)
        self.assertIn('message', entry)
        
        # Check specific values
        self.assertEqual(entry['level'], 'INFO')
        self.assertEqual(entry['message'], test_message)
        
    def test_multiple_log_entries(self):
        """Test that multiple log entries are properly appended to the log file."""
        logger = setup_logger("test_logger", self.log_file)
        
        # Log multiple messages
        messages = ["Message 1", "Message 2", "Message 3"]
        for msg in messages:
            logger.info(msg)
        
        # Read and parse the log file
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        log_entries = list(yaml.safe_load_all(log_content))
        
        # Check if all messages were logged
        self.assertEqual(len(log_entries), len(messages))
        for i, entry in enumerate(log_entries):
            self.assertEqual(entry['message'], messages[i])
            
    def test_log_levels(self):
        """Test that different log levels are correctly recorded."""
        logger = setup_logger("test_logger", self.log_file)
        
        # Log messages with different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Read and parse the log file
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        log_entries = list(yaml.safe_load_all(log_content))
        
        # Check log levels
        expected_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for i, entry in enumerate(log_entries):
            self.assertEqual(entry['level'], expected_levels[i])
            
    def test_get_logger(self):
        """Test that get_logger returns the same logger for the same name."""
        logger1 = get_logger("test_logger", self.log_file)
        logger2 = get_logger("test_logger")  # Should return the existing logger
        
        self.assertIs(logger1, logger2)
        
    def test_log_rotation(self):
        """Test that log rotation works correctly."""
        # Setup logger with a small max_size for testing rotation
        max_size = 500  # bytes
        max_backups = 2
        logger = setup_logger("test_logger", self.log_file, max_size=max_size, backup_count=max_backups)
        
        # Generate enough logs to trigger rotation
        large_message = "X" * 100  # 100 bytes message
        for _ in range(10):  # Should trigger multiple rotations
            logger.info(large_message)
            
        # Check if log files were rotated
        base_path = os.path.splitext(self.log_file)[0]
        expected_files = [
            self.log_file,  # Current log
            f"{base_path}.1",  # First backup
            f"{base_path}.2",  # Second backup
        ]
        
        for file_path in expected_files:
            self.assertTrue(os.path.exists(file_path), f"Expected log file {file_path} does not exist")
            
        # Ensure we don't have more backups than specified
        unexpected_file = f"{base_path}.3"
        self.assertFalse(os.path.exists(unexpected_file), f"Unexpected backup file {unexpected_file} exists")
        
    def test_extra_fields(self):
        """Test that extra fields are properly included in the YAML output."""
        logger = setup_logger("test_logger", self.log_file)
        
        # Log with extra context
        extra = {'user': 'test_user', 'request_id': '12345', 'client_ip': '192.168.1.1'}
        logger.info("Request processed", extra=extra)
        
        # Read and parse the log file
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        log_entries = list(yaml.safe_load_all(log_content))
        
        # Check extra fields
        entry = log_entries[0]
        for key, value in extra.items():
            self.assertIn(key, entry)
            self.assertEqual(entry[key], value)


if __name__ == '__main__':
    unittest.main()
