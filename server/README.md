# LSL Server

This directory contains the REST API server implementation for the LSL project.

## Components

- `api.py`: FastAPI server implementation with endpoints
- `run.py`: Server startup script

## Usage

Start the server using:

```bash
./server/run.py [options]
```

Options:
- `--host`: Host to listen on (default: from config or 127.0.0.1)
- `--port`: Port to listen on (default: from config or 8000)
- `--main-config`: Path to main config file
- `--users-config`: Path to users config file
- `--containers-config`: Path to containers config file
- `--log-file`: Path to log file
- `--log-level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## API Endpoints

- `GET /get_config`: Get user-specific configuration
- `POST /ping`: Update client's last seen timestamp
- `GET /monitor`: Get system and container monitoring data

Authentication is done via UUID tokens in the Authorization header:

```
Authorization: Bearer <uuid>
```

## Rate Limiting

The API has built-in rate limiting that can be configured in `main.yaml`:

```yaml
server:
  rate_limits:
    get_config: 60  # requests per minute
    ping: 120
    monitor: 30
```

## Configuration Reloading

The server can reload its configuration without restarting by sending a SIGHUP signal:

```bash
kill -HUP <server_pid>
```
