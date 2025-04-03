import argparse
import subprocess
import os
import sys

def load_config():
    config = {}
    try:
        with open('containers.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                name, repo = line.split('=', 1)
                config[name.strip()] = repo.strip()
    except FileNotFoundError:
        pass
    return config

def main():
    parser = argparse.ArgumentParser(description='Manage throwaway Docker containers')
    parser.add_argument('-n', '--name', help='Name of the container to start')
    parser.add_argument('-l', '--list', action='store_true', help='List available containers')
    parser.add_argument('--net', action='store_true', help='Use host network')
    parser.add_argument('-p', '--persist', action='store_true', help='Persist data in a volume')
    args = parser.parse_args()

    if args.list:
        config = load_config()
        if not config:
            print("No containers configured.")
        else:
            for name, repo in config.items():
                print(f"{name}: {repo}")
        sys.exit(0)

    if not args.name:
        parser.print_help()
        sys.exit(1)

    config = load_config()
    image = config.get(args.name, args.name)

    volume_dir = f".lsl_persist_{args.name}"
    options = ['-it']

    if args.persist:
        os.makedirs(volume_dir, exist_ok=True)
        volume_path = os.path.abspath(volume_dir)
        options.append(f'-v {volume_path}:/data')

    if args.net:
        options.extend(['--network', 'host'])

    options.append('--rm')

    cmd = ['docker', 'run'] + options + [image, '/bin/bash']

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running container: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
