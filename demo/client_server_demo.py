#!/usr/bin/env python3
"""
LSL Client-Server Demo

This script demonstrates the client-server architecture of LSL,
showing how to set up and connect both components to display a simple web interface.
"""
import os
import sys
import subprocess
import time
import webbrowser
from typing import List, Dict, Any, Optional
import threading

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_header(message: str) -> None:
    """Print a formatted header message"""
    border = '=' * (len(message) + 4)
    print(f"\n{border}")
    print(f"| {message} |")
    print(f"{border}\n")

def start_server(port: int = 8080) -> subprocess.Popen:
    """Start the LSL server in a subprocess"""
    print_header("STARTING LSL SERVER")
    print(f"Starting server on port {port}...")
    
    # Create command to run the server
    cmd = [sys.executable, os.path.join('..', 'server', 'run.py'), '--port', str(port), '--demo']
    
    # Start the server as a subprocess
    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(2)
    print("LSL Server started!")
    return process

def start_client(server_url: str) -> subprocess.Popen:
    """Start the LSL client in a subprocess"""
    print_header("STARTING LSL CLIENT")
    print(f"Connecting to server at {server_url}...")
    
    # Create command to run the client demo
    cmd = [sys.executable, os.path.join('..', 'demo', 'demo_client.py'), 
           '--server', server_url]
    
    # Start the client as a subprocess
    process = subprocess.Popen(
        cmd, 
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)
    print("LSL Client started and connected to server!")
    return process

def open_demo_page(url: str) -> None:
    """Open the demo page in a web browser"""
    print_header("OPENING DEMO WEBPAGE")
    print(f"Opening demo webpage at: {url}")
    
    # Wait a moment to ensure the server is ready
    time.sleep(3)
    
    # Open the web browser
    try:
        webbrowser.open(url)
        print("Demo webpage opened in your browser!")
    except Exception as e:
        print(f"Failed to open browser automatically: {e}")
        print(f"Please manually open: {url}")

def stream_output(process: subprocess.Popen, prefix: str) -> None:
    """Stream the output of a subprocess with a prefix"""
    while process.poll() is None:
        if process.stdout:
            line = process.stdout.readline()
            if line:
                print(f"{prefix}: {line.strip()}")
        time.sleep(0.1)

def run_demo() -> None:
    """Run the client-server demo"""
    print_header("LSL CLIENT-SERVER DEMO")
    print("This demo shows how LSL's client and server components work together.")
    print("We will:")
    print(" 1. Start the LSL server")
    print(" 2. Start the LSL client and connect to the server")
    print(" 3. Open a web browser to view the LSL dashboard")
    print()
    
    port = 8080
    server_url = f"http://localhost:{port}"
    dashboard_url = f"{server_url}/dashboard"
    
    try:
        # Start the server
        server_process = start_server(port)
        
        # Start a thread to stream server output
        server_thread = threading.Thread(
            target=stream_output,
            args=(server_process, "SERVER"),
            daemon=True
        )
        server_thread.start()
        
        # Start the client
        client_process = start_client(server_url)
        
        # Start a thread to stream client output
        client_thread = threading.Thread(
            target=stream_output,
            args=(client_process, "CLIENT"),
            daemon=True
        )
        client_thread.start()
        
        # Open the demo page
        open_demo_page(dashboard_url)
        
        print_header("DEMO RUNNING")
        print("The demo is now running! You should see the dashboard in your web browser.")
        print("Press Ctrl+C to stop the demo when finished.")
        
        # Keep the main thread running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping demo...")
    finally:
        # Clean up processes
        for process in [server_process, client_process]:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print("Demo stopped.")

if __name__ == "__main__":
    run_demo()
