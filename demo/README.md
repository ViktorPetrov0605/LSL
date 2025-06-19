# LSL Demo Guide

This demo showcases the key features of LSL (Lightweight Subsystem for Linux) focusing on container management, network configuration, and multi-user interaction.

## Demo Components

1. **Custom Container Configurations**
   - Located in `config/demo-containers.yaml`
   - Three pre-configured containers demonstrating different use cases:
     - `dev_env`: Development environment with host networking
     - `web_server`: Nginx server with bridge networking
     - `shared_terminal`: Shared terminal environment for multi-user interaction

2. **Networking Options**
   - Host Network Mode: Direct access to host's network interfaces (dev_env)
   - Bridge Network Mode: Isolated container networking (web_server, shared_terminal)

3. **Data Persistence**
   - All containers have persistent storage configured
   - Data locations:
     - Dev Environment: `~/lsl_data/dev_env`
     - Web Server: `~/lsl_data/web_server`
     - Shared Terminal: `~/lsl_data/shared_terminal`

## How to Test

### 1. Development Environment (Host Network)
```bash
# Start the development environment
lsl -n dev_env --net --persist

# Test network access (should use host's network)
ping google.com
ip addr show

# Test persistence (data in /data will persist)
echo "test data" > /data/test.txt
exit
```

### 2. Web Server (Bridge Network)
```bash
# Start the web server
lsl -n web_server --persist

# Test persistence
echo "Hello from LSL" > /usr/share/nginx/html/index.html

# Access the web server
curl http://localhost:8080
```

### 3. Shared Terminal (Multi-User)
```bash
# First user starts the shared terminal
lsl -n shared_terminal --persist

# Second user connects to the same container
# Instructions for connecting will be displayed when the container starts
```

## Testing Persistence

After starting and stopping containers, verify that:
1. Data written to mounted volumes persists between sessions
2. Container configurations are preserved
3. User settings and access permissions are maintained

## Network Configuration

- Host networking (`--net`): Container uses host's network stack
- Bridge networking (default): Container uses Docker's bridge network
