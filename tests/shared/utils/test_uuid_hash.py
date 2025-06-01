"""
Test module for UUID and hashing utilities in shared/utils/uuid_hash.py
"""
import unittest
import uuid
import re
import hashlib
import os
from unittest.mock import patch, mock_open, MagicMock

# Import the module to test
from shared.utils.uuid_hash import generate_uuid, hash_password, verify_password

class TestUUIDGeneration(unittest.TestCase):
    def test_generate_uuid_format(self):
        """Test that generated UUID is in the correct format."""
        result = generate_uuid()
        # Check if result is a string
        self.assertIsInstance(result, str)
        # Check if result matches UUID format
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        )
        self.assertTrue(bool(uuid_pattern.match(result)))
        
    def test_generate_uuid_uniqueness(self):
        """Test that generated UUIDs are unique."""
        uuids = [generate_uuid() for _ in range(100)]
        # Check that all UUIDs are unique
        self.assertEqual(len(uuids), len(set(uuids)))
        
    def test_generate_uuid_validates(self):
        """Test that generated UUIDs are valid according to the uuid module."""
        result = generate_uuid()
        # This should not raise an exception if the UUID is valid
        uuid_obj = uuid.UUID(result)
        self.assertEqual(str(uuid_obj), result)


class TestPasswordHashing(unittest.TestCase):
    def test_hash_password(self):
        """Test that hashing a password returns a string in the expected format."""
        password = "testPassword123"
        result = hash_password(password)
        
        # Check if result is a string
        self.assertIsInstance(result, str)
        
        # Check if hash contains algorithm, salt, and hash parts
        parts = result.split('$')
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], 'pbkdf2-sha256')
        
        # Check if iterations count is a number
        self.assertTrue(parts[1].isdigit())
        
        # Check if salt and hash are hexadecimal
        self.assertTrue(all(c in '0123456789abcdef' for c in parts[2]))
        self.assertTrue(all(c in '0123456789abcdef' for c in parts[3]))
        
    def test_verify_password_correct(self):
        """Test that a correctly hashed password verifies."""
        password = "correctPassword123"
        hashed = hash_password(password)
        
        # Verify with correct password
        self.assertTrue(verify_password(password, hashed))
        
    def test_verify_password_incorrect(self):
        """Test that an incorrectly hashed password fails verification."""
        password = "correctPassword123"
        wrong_password = "wrongPassword456"
        hashed = hash_password(password)
        
        # Verify with incorrect password
        self.assertFalse(verify_password(wrong_password, hashed))
        
    def test_verify_password_invalid_hash(self):
        """Test that verification fails with an invalid hash format."""
        password = "testPassword123"
        invalid_hash = "invalid-hash-format"
        
        with self.assertRaises(ValueError):
            verify_password(password, invalid_hash)
            
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        self.assertNotEqual(hash1, hash2)
        
    def test_same_password_different_salts(self):
        """Test that the same password hashed twice produces different hashes due to salting."""
        password = "samePassword"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        self.assertNotEqual(hash1, hash2)


if __name__ == '__main__':
    unittest.main()
