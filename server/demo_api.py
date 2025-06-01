#!/usr/bin/env python3
"""
Demo script for LSL REST API
"""
import sys
import json
import requests
import argparse
import uuid
from datetime import datetime, timedelta

def format_json(data):
    """Format JSON data with indentation."""
    return json.dumps(data, indent=2)

def ping_server(base_url, uuid_token):
    """Send a ping to the server."""
    url = f"{base_url}/ping"
    headers = {"Authorization": f"Bearer {uuid_token}"}
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        print(f"Ping successful: {format_json(response.json())}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending ping: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {format_json(e.response.json())}")
        sys.exit(1)

def get_config(base_url, uuid_token):
    """Get user configuration from the server."""
    url = f"{base_url}/get_config"
    headers = {"Authorization": f"Bearer {uuid_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Configuration:")
        print(format_json(response.json()))
    except requests.exceptions.RequestException as e:
        print(f"Error getting config: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {format_json(e.response.json())}")
        sys.exit(1)

def get_monitor_data(base_url):
    """Get monitoring data from the server."""
    url = f"{base_url}/monitor"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print(f"System Stats:")
        print(f"  CPU: {data['system']['cpu']}%")
        print(f"  Memory: {data['system']['memory']['used']} MB / {data['system']['memory']['total']} MB ({data['system']['memory']['percent']}%)")
        print(f"  Disk: {data['system']['disk']['used']} GB / {data['system']['disk']['total']} GB ({data['system']['disk']['percent']}%)")
        
        print(f"\nRunning Containers:")
        for container in data['containers']:
            print(f"  - {container['name']} ({container['image']}) - {container['status']}")
            if container['owner']:
                print(f"    Owner: {container['owner']}")
        
        print(f"\nClients:")
        for client in data['clients']:
            print(f"  - {client['username']} ({client['uuid']})")
            print(f"    Last seen: {client['last_seen']} ({client['seconds_ago']} seconds ago)")
    except requests.exceptions.RequestException as e:
        print(f"Error getting monitoring data: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {format_json(e.response.json())}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='LSL REST API Demo')
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base URL of the LSL server')
    parser.add_argument('--uuid', default='11111111-1111-4111-a111-111111111111', help='UUID token for authentication')
    parser.add_argument('--action', choices=['ping', 'config', 'monitor', 'all'], default='all', help='Action to perform')
    
    args = parser.parse_args()
    
    # Validate UUID
    try:
        uuid_obj = uuid.UUID(args.uuid)
    except ValueError:
        print(f"Error: Invalid UUID format - {args.uuid}")
        sys.exit(1)
    
    print(f"=== LSL REST API Demo ===")
    print(f"Server: {args.url}")
    print(f"UUID: {args.uuid}")
    print()
    
    if args.action in ['ping', 'all']:
        print("=== PING ENDPOINT ===")
        ping_server(args.url, args.uuid)
        print()
    
    if args.action in ['config', 'all']:
        print("=== GET_CONFIG ENDPOINT ===")
        get_config(args.url, args.uuid)
        print()
    
    if args.action in ['monitor', 'all']:
        print("=== MONITOR ENDPOINT ===")
        get_monitor_data(args.url)

if __name__ == "__main__":
    main()
