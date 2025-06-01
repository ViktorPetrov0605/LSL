#!/usr/bin/env python3
"""
Test script for YAML logger
"""
import os
import sys
import tempfile

# Add the project root to the path
sys.path.append(os.getcwd())

from shared.utils.yaml_logger import setup_logger

# Create a temporary log file
log_file = os.path.join(tempfile.gettempdir(), 'test.log')

# Setup and use the logger
logger = setup_logger('test_logger', log_file)
logger.info('Test info message')
logger.warning('Test warning message with context', extra={'user': 'test', 'request_id': '12345'})

# Print the results
print(f'Log file created at: {log_file}')
print('Log content:')
print('------------')
with open(log_file, 'r') as f:
    print(f.read())
print('------------')
