#!/usr/bin/env python3
"""
LSL Demo Server

This is a simplified version of the LSL server for demonstration purposes,
serving a web dashboard and providing basic API endpoints for client interaction.
"""
import os
import sys
import argparse
import json
from typing import Dict, Any, List
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import mimetypes

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Global state for the demo server
server_state = {
    "clients": {},
    "containers": {},
    "start_time": time.time(),
    "requests_handled": 0
}

class DemoRequestHandler(SimpleHTTPRequestHandler):
    """Handler for demo server requests"""
    
    def __init__(self, *args, **kwargs):
        self.directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        server_state["requests_handled"] += 1
        
        if self.path == '/':
            self.path = '/demo_dashboard.html'
            return self.send_file_response()
        
        elif self.path == '/ping':
            self.send_json_response({"status": "ok", "server_time": time.time()})
        
        elif self.path == '/get_config':
            config = {
                "server_version": "1.0.0-demo",
                "containers": {
                    "dev_env": {
                        "image": "ubuntu:22.04",
                        "network": "host",
                        "persist": True
                    },
                    "web_server": {
                        "image": "nginx:alpine",
                        "network": "bridge",
                        "ports": ["8080:80"],
                        "persist": True
                    }
                },
                "settings": {
                    "auto_updates": True,
                    "sync_interval": 60,
                    "logging_level": "info"
                }
            }
            self.send_json_response(config)
        
        elif self.path == '/api/status':
            uptime = int(time.time() - server_state["start_time"])
            status = {
                "status": "active",
                "uptime_seconds": uptime,
                "client_count": len(server_state["clients"]),
                "container_count": len(server_state["containers"]),
                "requests_handled": server_state["requests_handled"]
            }
            self.send_json_response(status)
        
        elif self.path == '/swagger.json':
            # Serve OpenAPI spec
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "LSL Demo Server API",
                    "version": "1.0.0-demo",
                    "description": "API documentation for the LSL Demo Server."
                },
                "paths": {
                    "/ping": {
                        "get": {
                            "summary": "Ping the server",
                            "responses": {
                                "200": {
                                    "description": "Server is alive",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/get_config": {
                        "get": {
                            "summary": "Get server config",
                            "responses": {
                                "200": {
                                    "description": "Config object",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/api/status": {
                        "get": {
                            "summary": "Get server status",
                            "responses": {
                                "200": {
                                    "description": "Status object",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/register_container": {
                        "post": {
                            "summary": "Register a container",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Container registered",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/status_update": {
                        "post": {
                            "summary": "Update client status",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Status updated",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            self.send_json_response(openapi_spec)
        
        elif self.path == '/docs':
            # Serve Swagger UI HTML
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(self.swagger_ui_html().encode('utf-8'))
        
        else:
            # Try to serve static files from the demo directory
            return self.send_file_response()
    
    def do_POST(self):
        """Handle POST requests"""
        server_state["requests_handled"] += 1
        
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_json_response({"error": "No data provided"}, status_code=400)
            return
            
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON data"}, status_code=400)
            return
            
        if self.path == '/register_container':
            client_id = data.get("client_id", "unknown")
            container_name = data.get("name")
            container_config = data.get("config")
            
            if not container_name or not container_config:
                self.send_json_response({"error": "Missing container details"}, status_code=400)
                return
                
            # Update server state
            server_state["containers"][container_name] = {
                "config": container_config,
                "client_id": client_id,
                "registered_at": datetime.now().isoformat()
            }
            
            # Make sure client is registered
            if client_id not in server_state["clients"]:
                server_state["clients"][client_id] = {
                    "first_seen": datetime.now().isoformat(),
                    "containers": []
                }
                
            server_state["clients"][client_id]["containers"].append(container_name)
            server_state["clients"][client_id]["last_seen"] = datetime.now().isoformat()
                
            self.send_json_response({
                "status": "ok",
                "message": f"Container {container_name} registered"
            })
            
        elif self.path == '/status_update':
            client_id = data.get("client_id")
            status = data.get("status")
            
            if not client_id:
                self.send_json_response({"error": "Missing client_id"}, status_code=400)
                return
                
            # Update client status
            if client_id not in server_state["clients"]:
                server_state["clients"][client_id] = {
                    "first_seen": datetime.now().isoformat(),
                    "containers": []
                }
                
            server_state["clients"][client_id].update({
                "status": status,
                "last_seen": datetime.now().isoformat(),
                "resources": data.get("resources", {}),
                "containers": data.get("containers", [])
            })
                
            self.send_json_response({"status": "ok"})
            
        else:
            self.send_json_response({"error": "Endpoint not found"}, status_code=404)
    
    def send_json_response(self, data: Dict, status_code: int = 200):
        """Send a JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_file_response(self):
        """Attempt to serve a file"""
        try:
            return super().do_GET()
        except Exception as e:
            self.send_json_response(
                {"error": f"File not found: {self.path}"}, 
                status_code=404
            )
    
    def swagger_ui_html(self):
        """Return a minimal Swagger UI HTML page"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>LSL Demo Server API Docs</title>
            <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
        </head>
        <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            });
        };
        </script>
        </body>
        </html>
        '''

def run_server(port: int):
    """Run the demo server on the specified port"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DemoRequestHandler)
    print(f"LSL Demo Server running on port {port}")
    print(f"Dashboard available at http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")

def main():
    """Main entry point for the demo server script"""
    parser = argparse.ArgumentParser(description="LSL Demo Server")
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to run the server on')
    parser.add_argument('--demo', action='store_true',
                        help='Run in demo mode with simulated data')
    
    args = parser.parse_args()
    
    # Print server info
    print("=" * 50)
    print("LSL DEMO SERVER")
    print("=" * 50)
    print("This is a simplified version of the LSL server for demonstration purposes.")
    
    if args.demo:
        print("Running in DEMO mode with simulated data")
        
        # Add some fake data to the server state
        server_state["clients"]["demo-client-1"] = {
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "status": "active",
            "containers": ["dev_env", "web_server"],
            "resources": {
                "cpu_percent": 15.2,
                "memory_percent": 32.8,
                "disk_percent": 45.1
            }
        }
        
        server_state["containers"]["dev_env"] = {
            "config": {
                "image": "ubuntu:22.04",
                "network": "host",
                "persist": True
            },
            "client_id": "demo-client-1",
            "registered_at": datetime.now().isoformat()
        }
        
        server_state["containers"]["web_server"] = {
            "config": {
                "image": "nginx:alpine",
                "network": "bridge",
                "ports": ["8080:80"],
                "persist": True
            },
            "client_id": "demo-client-1",
            "registered_at": datetime.now().isoformat()
        }
    
    # Run the server
    run_server(args.port)

if __name__ == '__main__':
    main()
