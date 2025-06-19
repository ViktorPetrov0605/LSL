import argparse                                                                                                      
import subprocess                                                                                                    
import os                                                                                                            
import sys
import random
import re
import socket
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv
                                                                                          
#Start config loader                                                                                                               
def load_config() -> Dict[str, str]:                                                                                                   
    config: Dict[str, str] = {}                                                                                                      
    try:                                                                                                             
        with open('containers.txt', 'r') as f:                                                                       
            for line in f:                                                                                           
                line = line.strip()                                                                                  
                if not line or line.startswith('#'):                                                                 
                    continue                                                                                         
                name, repo = line.split('=', 1)                                                                      
                config[name.strip()] = repo.strip()                                                                  
    except FileNotFoundError:                                                                                        
        pass  # Config file not found; proceed without it                                                            
    return config

def check_if_screen_exists(session_name: str) -> bool:
    """Check if a screen session with the given name exists"""
    try:
        result = subprocess.run(['screen', '-ls', session_name], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return session_name in result.stdout
    except Exception:
        return False

def setup_screen_session(session_name: str, is_host: bool = True) -> None:
    """Set up a screen session that can be shared between containers"""
    if is_host:
        # Create a new shared screen session
        print(f"Creating shared screen session: {session_name}")
        cmd = ['screen', '-dmS', session_name]
        subprocess.run(cmd, check=True)
        print(f"Screen session '{session_name}' created. Others can connect using: screen -x {session_name}")
    else:
        # Try to connect to an existing shared screen session
        if check_if_screen_exists(session_name):
            print(f"Connecting to shared screen session: {session_name}")
            # We need to exec this directly as it replaces the current process
            os.execvp('screen', ['screen', '-x', session_name])
        else:
            print(f"Error: Shared screen session '{session_name}' does not exist.")
            print("Make sure the host has created the session first.")
            sys.exit(1)                                                                                                    
                                                                                                                     
def get_connection_key() -> str:
    # Use CONNECTION_KEY from .env or default to 'LSL'
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv('CONNECTION_KEY', 'LSL')

def find_free_port(start: int = 10000, end: int = 20000) -> int:
    import random, socket
    while True:
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port

def setup_host_shared_container(image: str, session_name: str, options: list):
    port = find_free_port()
    key = get_connection_key()
    # Prepare Docker run command with SSH port mapping
    docker_cmd = [
        'docker', 'run', '-d', '--rm', '-p', f'{port}:22', '--name', f'lsl_{session_name}'
    ] + options + [image, '/usr/sbin/sshd', '-D']
    # Start container detached with SSHD as entrypoint
    container_id = subprocess.check_output(docker_cmd).decode().strip()
    # Set root password to CONNECTION_KEY
    subprocess.run(['docker', 'exec', container_id, 'bash', '-c', f'echo root:{key} | chpasswd'], check=True)
    # Allow password auth
    subprocess.run(['docker', 'exec', container_id, 'bash', '-c', "sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config"], check=True)
    subprocess.run(['docker', 'exec', container_id, 'bash', '-c', "sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config"], check=True)
    subprocess.run(['docker', 'exec', container_id, 'service', 'ssh', 'restart'], check=True)
    # Install screen and start session
    subprocess.run(['docker', 'exec', container_id, 'apt-get', 'update'], check=True)
    subprocess.run(['docker', 'exec', container_id, 'apt-get', 'install', '-y', 'screen'], check=True)
    subprocess.run(['docker', 'exec', '-u', 'root', container_id, 'screen', '-dmS', session_name], check=True)
    print(f"[LSL] Shared container started. SSH on port {port} (password: {key})")
    print(f"[LSL] To join: python3 lsl.py --share 127.0.0.1:{port}")
    print(f"[LSL] Inside, run: screen -x {session_name}")
    return port, container_id

def join_shared_session_ssh(hostport: str, session_name: str):
    import re
    key = get_connection_key()
    m = re.match(r'([^:]+):(\d+)', hostport)
    if not m:
        print("Invalid --share argument. Use host:port")
        sys.exit(1)
    host, port = m.groups()
    ssh_cmd = [
        'ssh', f'-p{port}', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
        f'root@{host}', f'screen -x {session_name}'
    ]
    print(f"[LSL] Connecting to {host}:{port} as root (password: {key})...")
    # Use sshpass for password automation if available
    try:
        subprocess.run(['sshpass', '-V'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ssh_cmd = ['sshpass', '-p', key] + ssh_cmd
    except Exception:
        print("[LSL] Tip: Install sshpass for passwordless automation, or enter password manually.")
    subprocess.run(ssh_cmd)

def main():                                                                                                          
    parser = argparse.ArgumentParser(description='Manage throwaway Docker containers')                               
    parser.add_argument('-n', '--name', help='Name of the container to start')                                       
    parser.add_argument('-l', '--list', action='store_true', help='List available containers')                       
    parser.add_argument('--net', action='store_true', help='Use host network')                                       
    parser.add_argument('-p', '--persist', action='store_true', help='Persist data in a volume')
    parser.add_argument('--share', help='Create or join a shared terminal session (host:port or session name)')
    parser.add_argument('--host', action='store_true', help='Act as the host for a shared terminal session')                     
    args = parser.parse_args()                                                                                       
                                                                                                                     
    if args.list:                                                                                                    
        config = load_config()                                                                                       
        if not config:                                                                                               
            print("No containers configured.")                                                                       
        else:                                                                                                        
            for name, repo in config.items():                                                                        
                print(f"{name}: {repo}")                                                                             
        sys.exit(0)                                                                                                  
                                                                                                                     
    if args.share and not args.host:
        # Client: join shared session
        join_shared_session_ssh(args.share, 'sharedSession1')
        sys.exit(0)
    if not args.name:                                                                                                
        parser.print_help()                                                                                          
        sys.exit(1)                                                                                                  
                                                                                                                     
    config = load_config()                                                                                           
    image = config.get(args.name, args.name)  # Use config or name as the image                                      
                                                                                                                     
    volume_dir = f".lsl_persist_{args.name}"                                                                         
    options = ['-it']                                                                                                
                                                                                                                     
    if args.persist:                                                                                                 
        os.makedirs(volume_dir, exist_ok=True)                                                                       
        volume_path = os.path.abspath(volume_dir)                                                                    
        options.append(f'-v {volume_path}:/data')                                                                    
                                                                                                                     
    if args.net:                                                                                                     
        options.extend(['--network', 'host'])                                                                        
                                                                                                                     
    # Always use --rm unless we want to keep the container (not required here)                                       
    options.append('--rm')
    
    # Prepare command
    if args.share:
        # Install screen in the container first if needed
        cmd_prefix = ['docker', 'run'] + options
        
        # For a shared terminal session, we need to set up screen
        # Make sure screen package is installed
        install_screen_cmd = cmd_prefix + [image, 'bash', '-c', 
                                          'apt-get update && apt-get install -y screen || apk add screen']
        try:
            print("Setting up shared terminal environment...")
            subprocess.run(install_screen_cmd, check=True)
            
            # Now start the actual container with screen
            shared_session_name = args.share
            
            # Check if we're the host or a client
            if args.host:
                # Host creates the screen session
                cmd = cmd_prefix + [image, 'bash', '-c', 
                                     f'screen -dmS {shared_session_name} && screen -r {shared_session_name}']
                print(f"Starting shared terminal as host: {shared_session_name}")
            else:
                # Client joins the screen session
                cmd = cmd_prefix + [image, 'bash', '-c', 
                                    f'screen -x {shared_session_name} || echo "Session {shared_session_name} not found"']
                print(f"Joining shared terminal session: {shared_session_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error setting up shared terminal: {e}")
            sys.exit(1)
    else:
        # Regular non-shared container
        cmd = ['docker', 'run'] + options + [image, '/bin/bash']                                                         
                                                                                                                     
    try:                                                                                                             
        subprocess.run(cmd, check=True)                                                                              
    except subprocess.CalledProcessError as e:                                                                       
        print(f"Error running container: {e}")                                                                       
        sys.exit(1)                                                                                                  
                                                                                                                     
if __name__ == "__main__":                                                                                           
    main()


