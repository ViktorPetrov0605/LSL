# Lightweight Subsystem for Linux (LSL) - Usage Guide

## Overview

LSL provides a command-line interface (CLI) for managing lightweight Docker containers. This guide details how to use the CLI to list available containers, start new containers, and customize your environment.

## Basic Usage

The primary command is `lsl`. Here's a breakdown of the available options:

* `lsl --list` or `lsl -l`: Lists the available containers configured in `containers.txt`.
* `lsl -n <container_name>`: Starts a container with the specified name. If the name is not found in `containers.txt`, it will attempt to use the name as a Docker image name directly.
* `lsl --persist -n <container_name>`: Starts a container with data persistence enabled, storing data in a volume.
* `lsl --net -n <container_name>`: Starts a container using the host network.

## Examples

**Listing available containers:**

