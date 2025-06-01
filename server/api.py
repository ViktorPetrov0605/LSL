"""
REST API implementation for LSL server.

This module provides:
- FastAPI server setup
- Endpoints for client interaction (/get_config, /ping, /monitor)
- Rate limiting
- Error handling
- Config reloading via SIGHUP
"""
import os
import signal
import time
import psutil
import docker
import yaml
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import uuid

# Import shared modules
from shared.config import load_yaml_config
from shared.utils.yaml_logger import setup_logger

# Path configuration
CONFIG_PATHS = {
    'main': os.environ.get('LSL_MAIN_CONFIG', 'config/main.yaml'),
    'users': os.environ.get('LSL_USERS_CONFIG', 'config/users.yaml'),
    'containers': os.environ.get('LSL_CONTAINERS_CONFIG', 'config/containers.yaml')
}

# Setup logging
log_file = os.environ.get('LSL_SERVER_LOG', 'logs/server.log')
logger = setup_logger('lsl_server', log_file, level=logging.INFO)

# Create FastAPI application
app = FastAPI(title="LSL Server API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme for token authentication
token_auth_scheme = HTTPBearer(auto_error=True)

# Rate limiting configuration
class RateLimiter:
    def __init__(self, limit_per_minute: int = 60):
        self.limit_per_minute = limit_per_minute
        self.requests = {}  # {client_id: [timestamp1, timestamp2, ...]}
    
    def is_rate_limited(self, client_id: str) -> bool:
        """Check if a client is rate-limited."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize client if not seen before
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove requests older than 1 minute
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > minute_ago
        ]
        
        # Check if too many requests
        if len(self.requests[client_id]) >= self.limit_per_minute:
            return True
        
        # Add this request
        self.requests[client_id].append(now)
        return False

# Initialize rate limiters
rate_limiters = {
    'get_config': RateLimiter(),
    'ping': RateLimiter(),
    'monitor': RateLimiter()
}

def setup_app():
    """Initialize application state with configuration."""
    logger.info("Initializing LSL server")
    
    try:
        # Load configurations
        app.state.main_config = load_yaml_config(CONFIG_PATHS['main'], 'main')
        app.state.users_config = load_yaml_config(CONFIG_PATHS['users'], 'users')
        app.state.containers_config = load_yaml_config(CONFIG_PATHS['containers'], 'containers')
        
        # Initialize last seen timestamps
        app.state.last_seen = {}  # {uuid: last_seen_timestamp}
        
        # Configure rate limiters from main config
        if 'server' in app.state.main_config and 'rate_limits' in app.state.main_config['server']:
            rate_limits = app.state.main_config['server']['rate_limits']
            for endpoint, limit in rate_limits.items():
                if endpoint in rate_limiters:
                    rate_limiters[endpoint].limit_per_minute = limit
                
        logger.info("Server configuration loaded successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize server: {e}")
        raise

def get_system_stats() -> Dict[str, Any]:
    """Get system statistics using psutil."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": cpu_percent,
            "memory": {
                "total": memory.total // (1024 * 1024),  # MB
                "used": memory.used // (1024 * 1024),  # MB
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total // (1024 * 1024 * 1024),  # GB
                "used": disk.used // (1024 * 1024 * 1024),  # GB
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {"error": "Failed to retrieve system statistics"}

def get_running_containers() -> List[Dict[str, Any]]:
    """Get information about running Docker containers."""
    try:
        client = docker.from_env()
        containers = client.containers.list()
        
        result = []
        for container in containers:
            # Try to extract owner from container name
            owner = None
            name = container.name
            
            # LSL containers are named with pattern: lsl_{container_type}_{owner}
            if name.startswith('lsl_'):
                parts = name.split('_')
                if len(parts) >= 3:
                    owner = parts[2]
            
            result.append({
                "name": name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "owner": owner
            })
            
        return result
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return []

def get_user_for_uuid(user_uuid: str) -> Optional[str]:
    """Get username for a given UUID."""
    users = app.state.users_config.get('users', {})
    for username, user_data in users.items():
        if user_data.get('uuid') == user_uuid:
            return username
    return None

def validate_uuid(credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """Validate UUID from Authorization header."""
    token = credentials.credentials
    
    # Check if token is a valid UUID
    try:
        uuid_obj = uuid.UUID(token)
        token = str(uuid_obj)
    except ValueError:
        logger.warning(f"Invalid UUID format in token: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UUID format",
        )
    
    # Check if UUID belongs to a valid user
    username = get_user_for_uuid(token)
    if not username:
        logger.warning(f"Unknown UUID in request: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown UUID",
        )
    
    return token

def apply_rate_limit(endpoint: str, uuid_token: str):
    """Apply rate limiting for a specific endpoint and token."""
    if endpoint not in rate_limiters:
        return
        
    if rate_limiters[endpoint].is_rate_limited(uuid_token):
        logger.warning(f"Rate limit exceeded for {endpoint} by {uuid_token}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {endpoint}. Please try again later."
        )

async def error_handler(request: Request, exc: HTTPException):
    """Custom error handler for HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

def reload_config(signum, frame):
    """Signal handler to reload configuration on SIGHUP."""
    logger.info("Received SIGHUP, reloading configuration")
    
    try:
        # Reload configurations
        app.state.main_config = load_yaml_config(CONFIG_PATHS['main'], 'main')
        app.state.users_config = load_yaml_config(CONFIG_PATHS['users'], 'users')
        app.state.containers_config = load_yaml_config(CONFIG_PATHS['containers'], 'containers')
        
        # Update rate limiters
        if 'server' in app.state.main_config and 'rate_limits' in app.state.main_config['server']:
            rate_limits = app.state.main_config['server']['rate_limits']
            for endpoint, limit in rate_limits.items():
                if endpoint in rate_limiters:
                    rate_limiters[endpoint].limit_per_minute = limit
        
        logger.info("Configuration reloaded successfully")
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    setup_app()
    
    # Register SIGHUP handler for config reload
    signal.signal(signal.SIGHUP, reload_config)
    
    logger.info("LSL server started")

@app.get("/get_config")
async def get_config(uuid_token: str = Depends(validate_uuid)):
    """
    Get the merged configuration for a user identified by UUID.
    
    Returns only the containers the user is allowed to access.
    """
    # Apply rate limiting
    apply_rate_limit('get_config', uuid_token)
    
    # Get username for this UUID
    username = get_user_for_uuid(uuid_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Get user data
    users = app.state.users_config.get('users', {})
    user_data = users.get(username, {})
    
    # Get allowed containers for this user
    allowed_containers = user_data.get('allowed_containers', [])
    
    # Build user-specific configuration
    all_containers = app.state.containers_config.get('containers', {})
    user_containers = {}
    
    for container_name in allowed_containers:
        if container_name in all_containers:
            user_containers[container_name] = all_containers[container_name]
    
    # Build the response
    config = {
        "username": username,
        "uuid": uuid_token,
        "containers": user_containers
    }
    
    # Add user metadata if available
    if 'metadata' in user_data:
        config['metadata'] = user_data['metadata']
    
    logger.info(f"Config requested by {username} ({uuid_token})")
    return config

@app.post("/ping")
async def ping(uuid_token: str = Depends(validate_uuid)):
    """
    Update last seen timestamp for a user identified by UUID.
    """
    # Apply rate limiting
    apply_rate_limit('ping', uuid_token)
    
    # Update last seen timestamp
    app.state.last_seen[uuid_token] = datetime.now()
    
    # Get username for logging
    username = get_user_for_uuid(uuid_token)
    
    logger.debug(f"Ping from {username} ({uuid_token})")
    return {"success": True}

@app.get("/monitor")
async def monitor():
    """
    Get monitoring information: system stats, running containers, and client status.
    """
    # For now, no authentication required (could add admin auth)
    
    # Apply rate limiting using request IP as identifier
    apply_rate_limit('monitor', "admin")  # TODO: Use actual admin token
    
    # Gather monitoring data
    system_stats = get_system_stats()
    containers = get_running_containers()
    
    # Format client data
    clients = []
    for client_uuid, last_seen_time in app.state.last_seen.items():
        username = get_user_for_uuid(client_uuid)
        last_seen_seconds = (datetime.now() - last_seen_time).total_seconds()
        
        clients.append({
            "username": username or "unknown",
            "uuid": client_uuid,
            "last_seen": last_seen_time.isoformat(),
            "seconds_ago": int(last_seen_seconds)
        })
    
    # Sort clients by last seen time (most recent first)
    clients.sort(key=lambda x: x["seconds_ago"])
    
    logger.debug("Monitor data requested")
    return {
        "system": system_stats,
        "containers": containers,
        "clients": clients
    }

# Exception handler
app.add_exception_handler(HTTPException, error_handler)

if __name__ == "__main__":
    import uvicorn
    
    # Get server configuration from main config or use defaults
    try:
        setup_app()
        host = app.state.main_config.get('server', {}).get('host', '127.0.0.1')
        port = app.state.main_config.get('server', {}).get('port', 8000)
    except Exception:
        logger.warning("Using default server configuration")
        host = '127.0.0.1'
        port = 8000
    
    # Start server
    uvicorn.run(app, host=host, port=port)
