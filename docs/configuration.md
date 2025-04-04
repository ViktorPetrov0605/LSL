# Lightweight Subsystem for Linux (LSL) - Configuration Guide

## Overview

This document details the configuration options for LSL, focusing on the `containers.txt` file. Proper configuration is crucial for LSL to function correctly.

## The `containers.txt` File

LSL relies on a configuration file named `containers.txt` to define available containers and their corresponding Docker images. This file should be placed in the same directory from which you are running the `lsl` command.

### File Format

The `containers.txt` file should contain lines in the following format:

```
<container_name>=<docker_image>
```

*  `<container_name>`: A unique name for the container. This name is used to identify the container when starting it using the `lsl` command. It should be descriptive and easy to remember.
*  `<docker_image>`: The name of the Docker image to use for the container. This can be a publicly available image from Docker Hub (e.g., `ubuntu:latest`, `postgres:14`) or a locally built image.

### Example `containers.txt` File

```
dev_env=ubuntu:latest
db_server=postgres:14
web_app=nginx:alpine
```

### Comments and Blank Lines

*  **Comments:** Lines starting with `#` are treated as comments and are ignored. Use comments to explain the purpose of each container or to provide additional information.
*  **Blank Lines:** Blank lines are also ignored. Use blank lines to improve readability.

### Best Practices

*  **Use Descriptive Names:** Choose container names that clearly indicate the purpose of the container (e.g., `dev_env`, `db_server`, `web_app`).
*  **Specify Image Tags:** Always include a specific image tag (e.g., `ubuntu:latest`, `postgres:14`) to ensure consistent behavior. Using `latest` can lead to unexpected changes when the image is updated.
*  **Keep the File Organized:** Use comments and blank lines to organize the `containers.txt` file and make it easier to maintain.

## Advanced Configuration (Future Enhanecments)

In future versions of LSL, we plan to add support for more advanced configuration options, such as:

*  **Environment Variables:** The ability to define environment variables for each container.
*  **Port Mappings:** The ability to map ports between the container and the host machine.
*  **Volume Mounts:** The ability to mount volumes between the container and the host machine.
