#!/usr/bin/env python3
"""
LSL Demo Tests

Test cases for the LSL demo features including shared terminals and web interface.
"""
import os
import sys
import subprocess
import unittest
import time
import requests
from urllib.parse import urljoin

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class LSLDemoTests(unittest.TestCase):
    """Test cases for the LSL Demo features"""
    
    @classmethod
    def setUpClass(cls):
        """Start the demo server for testing"""
        print("Starting demo server for tests...")
        cls.server_port = 8090
        cls.server_url = f"http://localhost:{cls.server_port}"
        
        # Start server in a separate process
        cls.server_process = subprocess.Popen(
            [sys.executable, 'demo_server.py', '--port', str(cls.server_port), '--demo'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Wait for server to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Stop the demo server after tests"""
        print("Stopping demo server...")
        if cls.server_process:
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()
    
    def test_01_server_running(self):
        """Test if the demo server is running"""
        try:
            response = requests.get(urljoin(self.server_url, '/ping'))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'ok')
        except (requests.RequestException, AssertionError) as e:
            self.fail(f"Server not running or not responding correctly: {e}")
    
    def test_02_get_config(self):
        """Test retrieving config from the server"""
        response = requests.get(urljoin(self.server_url, '/get_config'))
        self.assertEqual(response.status_code, 200)
        
        config = response.json()
        self.assertIn('containers', config)
        self.assertIn('dev_env', config['containers'])
        self.assertIn('web_server', config['containers'])
    
    def test_03_register_container(self):
        """Test registering a container with the server"""
        container_data = {
            "name": "test_container",
            "client_id": "test-client",
            "config": {
                "image": "alpine:latest",
                "network": "bridge",
                "persist": True
            }
        }
        
        response = requests.post(
            urljoin(self.server_url, '/register_container'),
            json=container_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_04_status_update(self):
        """Test sending a status update to the server"""
        status_data = {
            "client_id": "test-client",
            "status": "active",
            "timestamp": time.time(),
            "containers": ["test_container"],
            "resources": {
                "cpu_percent": 25.5,
                "memory_percent": 40.2,
                "disk_percent": 33.7
            }
        }
        
        response = requests.post(
            urljoin(self.server_url, '/status_update'),
            json=status_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_05_api_status(self):
        """Test getting API status"""
        response = requests.get(urljoin(self.server_url, '/api/status'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'active')
        self.assertIn('uptime_seconds', data)
        self.assertIn('client_count', data)
        self.assertGreaterEqual(data['client_count'], 1)  # At least our test client

class LSLSharedTerminalTests(unittest.TestCase):
    """Tests for the LSL Shared Terminal feature"""
    
    def test_check_screen_exists(self):
        """Test the screen session detection function"""
        # Import the function from lsl.py
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from lsl import check_if_screen_exists
        
        # Create a test screen session
        test_session = "lsl_test_session"
        subprocess.run(['screen', '-dmS', test_session], check=False)
        
        # Check that the function can detect it
        self.assertTrue(check_if_screen_exists(test_session))
        
        # Check that it correctly reports non-existent sessions
        self.assertFalse(check_if_screen_exists("nonexistent_session"))
        
        # Clean up
        subprocess.run(['screen', '-X', '-S', test_session, 'quit'], check=False)

def run_tests():
    """Run the test suite"""
    # Check for screen command
    try:
        subprocess.run(['which', 'screen'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("WARNING: 'screen' command not found. Shared terminal tests may fail.")
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'])

if __name__ == "__main__":
    run_tests()
