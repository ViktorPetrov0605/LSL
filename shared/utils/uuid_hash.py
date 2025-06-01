"""
UUID and password hashing utilities for LSL.

This module provides functions for:
- Generating UUIDs for users, clients, and containers
- Securely hashing passwords using PBKDF2-SHA256
- Verifying passwords against their hashed values
"""
import uuid
import hashlib
import os
import binascii

def generate_uuid():
    """
    Generate a random UUID (version 4) for uniquely identifying users, clients, or containers.
    
    Returns:
        str: A random UUID string in the format 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
    """
    return str(uuid.uuid4())

def hash_password(password, iterations=100000):
    """
    Hash a password using PBKDF2-SHA256 with a random salt.
    
    Args:
        password (str): The password to hash
        iterations (int, optional): Number of PBKDF2 iterations. Defaults to 100000.
        
    Returns:
        str: Hashed password in the format 'algorithm$iterations$salt$hash'
    """
    # Generate a random 16-byte salt (128 bits)
    salt = os.urandom(16)
    
    # Hash the password using PBKDF2-SHA256
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations
    )
    
    # Convert binary salt and hash to hexadecimal strings
    salt_hex = binascii.hexlify(salt).decode('ascii')
    hash_hex = binascii.hexlify(hash_bytes).decode('ascii')
    
    # Return the formatted hash string
    return f'pbkdf2-sha256${iterations}${salt_hex}${hash_hex}'

def verify_password(password, stored_hash):
    """
    Verify a password against its stored hash.
    
    Args:
        password (str): The password to verify
        stored_hash (str): The stored hash in the format 'algorithm$iterations$salt$hash'
        
    Returns:
        bool: True if the password matches the hash, False otherwise
        
    Raises:
        ValueError: If the stored hash is in an invalid format
    """
    # Check stored hash format
    parts = stored_hash.split('$')
    if len(parts) != 4 or parts[0] != 'pbkdf2-sha256':
        raise ValueError("Invalid hash format")
    
    # Extract hash components
    algorithm = parts[0]
    iterations = int(parts[1])
    salt_hex = parts[2]
    hash_hex = parts[3]
    
    # Convert hexadecimal salt back to binary
    salt = binascii.unhexlify(salt_hex)
    
    # Hash the given password with the same salt and iterations
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations
    )
    computed_hash_hex = binascii.hexlify(hash_bytes).decode('ascii')
    
    # Compare the computed hash with the stored hash
    return computed_hash_hex == hash_hex
