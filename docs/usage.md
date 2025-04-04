# Lightweight Subsystem for Linux (LSL) - Usage Guide

## Overview

LSL provides a command-line interface (CLI) for managing lightweight Docker containers. This guide details how to use the CLI to list available containers, start new containers, and customize your environment.

## Basic Usage

The primary command is `lsl`. Here's a breakdown of the available options:

*   `lsl --list` or `lsl -l`: Lists the available containers configured in `containers.txt`. If the `containers.txt` file is not found or is empty, a message indicating no containers are configured will be displayed.
*   `lsl -n <container_name>`: Starts a container with the specified name. LSL first attempts to find the container name within the `containers.txt` configuration file. If the name is found, the corresponding Docker image specified in the configuration file is used. If the name is *not* found in `containers.txt`, LSL will attempt to use the provided `<container_name>` directly as the Docker image name.
*   `lsl --persist -n <container_name>`: Starts a container with data persistence enabled. This option creates a dedicated volume for storing data generated within the container. The volume is created in a directory named `.lsl_persist_<container_name>` within the current working directory. Any data written to `/data` within the container will be stored in this volume, ensuring that data is preserved even when the container is stopped or removed.
*   `lsl --net -n <container_name>`: Starts a container using the host network. This option allows the container to access the host machine's network interfaces directly, providing increased network performance and access to host services. However, it also means that the container's ports are directly exposed on the host machine.

## Examples

**Listing available containers:**

```bash
lsl -l
```

This command will display a list of the containers configured in `containers.txt`, showing the container name and its corresponding Docker image.

**Starting a container named `dev_env`:**

```bash
lsl -n dev_env
```

This command will start a container using the `ubuntu:latest` image, as defined in the `containers.txt` file.

**Starting a container with data persistence:**

```bash
lsl --persist -n web_app
```

This command will start a container using the `nginx:alpine` image (from `containers.txt`) and enable data persistence. Data written to `/data` within the container will be stored in the `.lsl_persist_web_app` directory.

**Starting a container with host network mode:**

```bash
lsl --net -n db_server
```

This command will start a container using the `postgres:14` image (from `containers.txt`) and use the host network.

**Starting a container using a direct image name (not found in `containers.txt`):**

```bash
lsl -n my_custom_image:latest
```

This command will attempt to start a container using the `my_custom_image:latest` image directly, without looking for it in `containers.txt`.
