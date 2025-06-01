#!/usr/bin/env python3
"""
LSL Server startup script

This script starts the LSL server, including both the REST API for client 
communication and the Web Admin UI for administrative tasks.
"""
import os
import sys
import uvicorn
import argparse
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .api import app, setup_app, logger
from .web_admin import WebAdmin

def main():
    """Start the LSL server."""
    parser = argparse.ArgumentParser(description='LSL Server')
    parser.add_argument('--host', default=None, help='Host to listen on')
    parser.add_argument('--port', type=int, default=None, help='Port to listen on')
    parser.add_argument('--main-config', default=None, help='Path to main config file')
    parser.add_argument('--users-config', default=None, help='Path to users config file')
    parser.add_argument('--containers-config', default=None, help='Path to containers config file')
    parser.add_argument('--log-file', default=None, help='Path to log file')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Log level')
    parser.add_argument('--disable-web-admin', action='store_true', help='Disable Web Admin UI')
    args = parser.parse_args()
    
    # Set environment variables for config paths if provided
    if args.main_config:
        os.environ['LSL_MAIN_CONFIG'] = args.main_config
    if args.users_config:
        os.environ['LSL_USERS_CONFIG'] = args.users_config
    if args.containers_config:
        os.environ['LSL_CONTAINERS_CONFIG'] = args.containers_config
    if args.log_file:
        os.environ['LSL_SERVER_LOG'] = args.log_file
    
    try:
        # Initialize the API app
        setup_app()
        
        # Initialize the Web Admin UI if not disabled
        if not args.disable_web_admin:
            web_admin = WebAdmin(app)
            logger.info("Web Admin UI initialized")
        
        # Get the host and port from arguments or config
        host = args.host
        port = args.port
        
        # If not provided in args, try to get from config
        if not host or not port:
            try:
                if not host:
                    host = app.state.main_config.get('server', {}).get('host', '127.0.0.1')
                if not port:
                    port = app.state.main_config.get('server', {}).get('port', 8000)
            except (AttributeError, KeyError):
                # Fallback to defaults if config access fails
                if not host:
                    host = '127.0.0.1'
                if not port:
                    port = 8000
        
        # Set log level
        try:
            log_level = getattr(logging, args.log_level)
            logger.setLevel(log_level)
        except AttributeError:
            logger.warning(f"Invalid log level: {args.log_level}, using INFO")
        
        # Log startup info
        admin_status = "enabled" if not args.disable_web_admin else "disabled"
        logger.info(f"Starting LSL server on {host}:{port} (Web Admin UI: {admin_status})")
        
        # Start the server
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
