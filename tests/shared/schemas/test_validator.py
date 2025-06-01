"""
Test module for YAML schema validation utilities in shared/schemas/validator.py
"""
import unittest
import os
import tempfile
import yaml
import json
from unittest.mock import patch, mock_open

# Import the module to test
from shared.schemas.validator import validate_yaml, load_schema, get_schema_path

class TestSchemaValidation(unittest.TestCase):
    def setUp(self):
        """Set up test schemas and YAML files."""
        # Example test schema
        self.test_schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"},
                "hobbies": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        # Example valid YAML that matches the schema
        self.valid_yaml = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "hobbies": ["reading", "swimming"]
        }
        
        # Example invalid YAML with missing required field
        self.invalid_yaml_missing_field = {
            "name": "Jane Doe",
            "email": "jane@example.com"
        }
        
        # Example invalid YAML with wrong type
        self.invalid_yaml_wrong_type = {
            "name": "John Doe",
            "age": "thirty",  # Should be an integer
            "email": "john@example.com"
        }
        
    @patch('shared.schemas.validator.load_schema')
    def test_validate_valid_yaml(self, mock_load_schema):
        """Test that valid YAML passes validation."""
        mock_load_schema.return_value = self.test_schema
        
        result, errors = validate_yaml('person', self.valid_yaml)
        self.assertTrue(result)
        self.assertIsNone(errors)
        
    @patch('shared.schemas.validator.load_schema')
    def test_validate_missing_field(self, mock_load_schema):
        """Test that YAML with missing required fields fails validation."""
        mock_load_schema.return_value = self.test_schema
        
        result, errors = validate_yaml('person', self.invalid_yaml_missing_field)
        self.assertFalse(result)
        self.assertIsNotNone(errors)
        self.assertIn("'age' is a required property", str(errors))
        
    @patch('shared.schemas.validator.load_schema')
    def test_validate_wrong_type(self, mock_load_schema):
        """Test that YAML with wrong field type fails validation."""
        mock_load_schema.return_value = self.test_schema
        
        result, errors = validate_yaml('person', self.invalid_yaml_wrong_type)
        self.assertFalse(result)
        self.assertIsNotNone(errors)
        self.assertIn("'thirty' is not of type 'integer'", str(errors))
        
    def test_get_schema_path(self):
        """Test that get_schema_path returns the correct path."""
        schema_name = 'test_schema'
        expected_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'schemas',
            'definitions',
            f"{schema_name}.json"
        )
        
        actual_path = get_schema_path(schema_name)
        self.assertEqual(actual_path, expected_path)
        
    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "object"}')
    def test_load_schema(self, mock_file):
        """Test that load_schema correctly loads and parses a schema file."""
        schema = load_schema('test_schema')
        
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema, {"type": "object"})
        mock_file.assert_called_once()
        
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_schema_file_not_found(self, mock_file):
        """Test that load_schema raises exception when schema file is not found."""
        with self.assertRaises(ValueError):
            load_schema('nonexistent_schema')
            
    @patch("builtins.open", new_callable=mock_open, read_data='{invalid json')
    def test_load_schema_invalid_json(self, mock_file):
        """Test that load_schema raises exception when schema file contains invalid JSON."""
        with self.assertRaises(ValueError):
            load_schema('invalid_schema')


if __name__ == '__main__':
    unittest.main()
