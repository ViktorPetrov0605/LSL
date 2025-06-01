"""
YAML schema validation utilities for LSL.

This module provides functions for:
- Loading JSON schemas for various config files
- Validating YAML data against these schemas
- Providing clear error messages for validation failures
"""
import os
import json
import yaml
import jsonschema
from typing import Dict, Any, Tuple, Optional, Union

def get_schema_path(schema_name: str) -> str:
    """
    Get the filesystem path to a schema definition file.
    
    Args:
        schema_name (str): Name of the schema without extension
        
    Returns:
        str: Full path to the schema file
    """
    # First try the test directory, which might be set for tests
    if 'LSL_TEST_SCHEMA_DIR' in os.environ:
        test_path = os.path.join(
            os.environ['LSL_TEST_SCHEMA_DIR'], 
            f"{schema_name}.json"
        )
        if os.path.exists(test_path):
            return test_path
            
    # Schemas are stored in shared/schemas/definitions/*.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'schemas', 'definitions', f"{schema_name}.json")

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from disk.
    
    Args:
        schema_name (str): Name of the schema without extension
        
    Returns:
        Dict[str, Any]: Schema as a Python dictionary
        
    Raises:
        ValueError: If schema file doesn't exist or contains invalid JSON
    """
    schema_path = get_schema_path(schema_name)
    
    try:
        with open(schema_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in schema file {schema_path}: {e}")
    except FileNotFoundError:
        raise ValueError(f"Schema file not found: {schema_path}")

def validate_yaml(schema_name: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate YAML data against a schema.
    
    Args:
        schema_name (str): Name of the schema to validate against
        data (Dict[str, Any]): YAML data as Python dictionary
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
            - is_valid: True if validation passed, False otherwise
            - error_message: None if validation passed, error message string otherwise
    """
    schema = load_schema(schema_name)
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)

def load_and_validate_yaml_file(schema_name: str, file_path: str) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Load YAML from a file and validate it against a schema.
    
    Args:
        schema_name (str): Name of the schema to validate against
        file_path (str): Path to the YAML file
        
    Returns:
        Tuple[Dict[str, Any], bool, Optional[str]]: (data, is_valid, error_message)
            - data: Loaded YAML data as Python dictionary (or empty dict if loading fails)
            - is_valid: True if file exists, contains valid YAML, and passes schema validation
            - error_message: None if validation passed, error message string otherwise
    """
    # Initialize return values
    data = {}
    is_valid = False
    error = None
    
    try:
        # Try to load the YAML file
        with open(file_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data is None:  # Empty file
                    data = {}
                    error = f"File {file_path} is empty"
                    return data, is_valid, error
            except yaml.YAMLError as e:
                error = f"Invalid YAML in file {file_path}: {e}"
                return data, is_valid, error
                
        # Validate loaded data against schema
        is_valid, error = validate_yaml(schema_name, data)
        return data, is_valid, error
        
    except FileNotFoundError:
        error = f"File not found: {file_path}"
        return data, is_valid, error
