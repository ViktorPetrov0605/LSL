#!/usr/bin/env python3
"""
Test script for schema validation
"""
import os
import sys
import json
import tempfile

# Add the project root to the path
sys.path.insert(0, os.getcwd())

# Create a temporary directory for the test schema
schema_dir = os.path.join(tempfile.gettempdir(), 'schemas', 'definitions')
os.makedirs(schema_dir, exist_ok=True)

# Create a simple test schema
test_schema = {
    "type": "object",
    "required": ["name", "age"],
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    }
}

# Write the schema to a file
schema_path = os.path.join(schema_dir, 'person.json')
with open(schema_path, 'w') as f:
    json.dump(test_schema, f)
    
# Set environment variable for tests
os.environ['LSL_TEST_SCHEMA_DIR'] = schema_dir
print(f"Using test schema directory: {schema_dir}")

# Path setup for the validator module
from shared.schemas.validator import validate_yaml, load_schema

# Test with valid data
valid_data = {
    "name": "John Doe",
    "age": 30
}

print("Testing schema validation...")
print("\nValid data test:")
print(f"Data: {valid_data}")
valid, errors = validate_yaml('person', valid_data)
print(f"Valid: {valid}")
print(f"Errors: {errors}")

# Test with invalid data
invalid_data = {
    "name": "Jane Doe",
    # Age is missing
}

print("\nInvalid data test (missing age):")
print(f"Data: {invalid_data}")
valid, errors = validate_yaml('person', invalid_data)
print(f"Valid: {valid}")
print(f"Errors: {errors}")

# Test with invalid data type
invalid_type_data = {
    "name": "John Doe",
    "age": "thirty"  # Should be integer
}

print("\nInvalid data type test (age is string):")
print(f"Data: {invalid_type_data}")
valid, errors = validate_yaml('person', invalid_type_data)
print(f"Valid: {valid}")
print(f"Errors: {errors}")

print("\nSchema testing completed.")
