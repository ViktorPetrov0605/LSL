#!/usr/bin/env python3
"""
LSL Container Features Tes        try:
            result = subprocess.run(
                ['docker', 'ps', '-q', '-f', 'name=test_env'],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                subprocess.run(
                    ['docker', 'rm', '-f', 'test_env'],
                    capture_output=True,
                    check=True
                )
        except subprocess.CalledProcessError:
            pass  # No containers to clean up script tests key features of LSL containers including:
1. Default hidden persistent volumes
2. Named persistent volumes
3. Network access modes (host vs container network)
"""
import os
import subprocess
import time
import unittest
from pathlib import Path
from typing import Any

class TestContainerFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Ensure we're in the correct directory
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Clean up any existing test directories
        cls.cleanup_test_dirs()
        
    @classmethod
    def tearDownClass(cls) -> None:
        # Clean up test directories
        cls.cleanup_test_dirs()
        
    def setUp(self) -> None:
        """Clean up before each test"""
        self.cleanup_test_dirs()
        
    def tearDown(self) -> None:
        """Clean up after each test"""
        self.cleanup_test_dirs()
        
    @classmethod
    def cleanup_test_dirs(cls) -> None:
        """Clean up test directories between test runs"""
        test_dirs = ['.lsl_persist_test_env', 'testing']
        for dir_name in test_dirs:
            try:
                path = Path(dir_name)
                if path.exists():
                    for file in path.glob('*'):
                        file.unlink()
                    path.rmdir()
            except Exception as e:
                print(f"Warning: Could not clean up {dir_name}: {e}")
                
        # Also clean up any running containers
        try:
            subprocess.run(
                ['docker', 'ps', '-q', '-f', 'name=test_env'],
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(
                ['docker', 'rm', '-f', 'test_env'],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            pass  # No containers to clean up

    def test_default_persistence(self) -> None:
        """Test case 1: Default hidden persistent volume"""
        # Start container with default persistence
        cmd = ['python', 'lsl.py', '-n', 'test_env', '-p']
        container = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Create test file in container
            commands = "ls -la /data && echo 'Test content for default persistence' > /data/test.txt && ls -la /data/test.txt && exit\n"
            stdout, stderr = container.communicate(commands, timeout=10)
            print(f"\nContainer stdout:\n{stdout}\nContainer stderr:\n{stderr}")
            
            # Wait for container to completely exit
            container.wait(timeout=5)
            
            # Give filesystem a moment to sync
            time.sleep(1)
            
            # Verify file exists in hidden directory
        except Exception as e:
            self.fail(f"Container operation failed: {e}")
        
        hidden_dir = Path('.lsl_persist_test_env')
        test_file = hidden_dir / 'test.txt'
        
        self.assertTrue(hidden_dir.exists(), "Hidden persistence directory not created")
        self.assertTrue(test_file.exists(), "Test file not created in persistent volume")
        self.assertEqual(
            test_file.read_text().strip(),
            'Test content for default persistence',
            "File content doesn't match expected"
        )

    def test_named_persistence(self) -> None:
        """Test case 2: Named persistent volume"""
        # Start container with named persistence directory
        cmd = ['python', 'lsl.py', '-n', 'test_env', '-p', 'testing']
        container = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Create test file in container
        commands = "set -e\ntouch /data/test.txt\necho 'Testing case for named folder for persistence' > /data/test.txt\nexit\n"
        container.communicate(commands)
        
        # Wait for container to completely exit
        container.wait()
        
        # Verify file exists in named directory
        test_dir = Path('testing')
        test_file = test_dir / 'test.txt'
        
        self.assertTrue(test_dir.exists(), "Named persistence directory not created")
        self.assertTrue(test_file.exists(), "Test file not created in persistent volume")
        self.assertEqual(
            test_file.read_text().strip(),
            'Testing case for named folder for persistence',
            "File content doesn't match expected"
        )

    def test_network_modes(self) -> None:
        """Test case 3: Network access modes"""
        def test_ping(container: subprocess.Popen[Any], target: str) -> bool:
            try:
                cmd = f"ping -c 1 {target}"
                if container.stdin:
                    container.stdin.write(f"{cmd}\n")
                    container.stdin.flush()
                time.sleep(2)  # Give time for ping to complete
                return True
            except Exception:
                return False

        # Test container network (default)
        cmd = ['python', 'lsl.py', '-n', 'test_env']
        container = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Test pings
        google_reachable = test_ping(container, "google.com")
        internal_unreachable = test_ping(container, "10.241.102.210")
        
        if container.stdin:
            container.stdin.write("exit\n")
        container.wait()
        
        self.assertTrue(google_reachable, "Container should be able to reach google.com")
        self.assertFalse(internal_unreachable, "Container should not reach internal network")

        # Test host network
        cmd = ['python', 'lsl.py', '-n', 'test_env', '--net']
        container = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Test pings with host network
        google_reachable = test_ping(container, "google.com")
        internal_reachable = test_ping(container, "10.241.102.210")
        
        if container.stdin:
            container.stdin.write("exit\n")
        container.wait()
        
        self.assertTrue(google_reachable, "Container should be able to reach google.com")
        self.assertTrue(internal_reachable, "Container should be able to reach internal network")

if __name__ == '__main__':
    unittest.main()
