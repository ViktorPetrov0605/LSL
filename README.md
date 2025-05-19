# Lightweight Subsystem for Linux (LSL)

## Project Overview

Hey! I'm Viktor Petrov, a student at Fontys University, currently working on this personal project as part of my Open Learning coursework in the second semester. LSL aims to streamline the management of virtualized Linux-based development environments, making it easier and faster for software engineers, system administrators, and DevOps teams to create, manage, and share their development setups.

LSL is designed to provide a quick and efficient way to create temporary containers using Docker's engine. It offers host networking access and file system access, making it ideal for developers who need to compile code across different Linux distributions.

## Project Goals

**What I want to achieve:**

- Develop an efficient Docker-based solution for managing development environments.
- Provide near-instant initialization of environments.
- Reduce resource usage compared to traditional virtual machines (VMs).
- Simplify environment sharing and synchronization across teams.
- Streamline workflows for developers and system administrators.

**Why this project:**

Current solutions often involve heavy VMs or complex container setups that are time-consuming and resource-intensive. LSL aims to address these pain points by offering a developer-friendly platform.

## Technology Comparison

### LSL
- **Overview**: LSL provides a quick and efficient way to create temporary containers using Docker's engine with host networking access and file system access.
- **Speed**: Leveraging Docker's efficient engine ensures rapid container creation and teardown, crucial for development workflows.
- **Practicality**: Direct access to the host's network and file system simplifies many development tasks.

### systemd-nspawn
- **Overview**: A tool that allows users to run commands or entire operating systems in lightweight namespace containers.
- **Speed**: Not as fast as Docker-based solutions, but provides a robust environment with minimal overhead.
- **Practicality**: Simpler to configure than LXC/LXD but lacks some advanced features.

### LXC/LXD Containers and Virtual Machines
- **Overview**: LXC provides OS-level virtualization for multiple isolated Linux systems on a single host. LXD extends this with REST API support and better management tools.
- **Speed**: LXC containers are lightweight and fast, but LXD's VM support adds overhead.
- **Practicality**: Extensive features make it suitable for complex deployment scenarios but can be overkill for simple development tasks.

## Implementation Plan

Given the feedback received, I've broken down the project into smaller, manageable steps:

1. **Core Functionality (CLI):**
   - [x] Environment initialization (`lsl init`).
   - [x] Container creation, listing, start/stop (`lsl create`, `lsl list`, `lsl start/stop`).
2. **Terminal User Interface (TUI):**
   - [ ] Design and implement an intuitive TUI for enhanced user experience.
3. **Collaboration Features:**
   - [ ] Environment sharing and file synchronization.
   - [ ] Access control mechanisms.
4. **Additional Enhanecements:**
   - [ ] Container orchestration using Docker.
   - [ ] Secure authentication and efficient resource management.

## Realistic End Goal:

The primary objective is to create a functional and user-friendly container management system that significantly improves the development workflow, especially in collaborative environments. By focusing on efficiency, speed, and ease of use, LSL will be a valuable tool for developers working on various projects.

## Feedback and Contribution

As this project evolves, I welcome feedback and suggestions! If you have ideas or spot areas for improvement, feel free to open an issue or submit a pull request. Your input is greatly appreciated!

## Documentation

Comprehensive documentation for LSL is available in the `docs/` directory:

* `docs/usage.md`: Detailed instructions on how to use the LSL command-line interface, including examples for common tasks.
* `docs/configuration.md`: Information on configuring available containers and customizing LSL's behavior.

## Getting Started

To begin using LSL, ensure you have Docker installed. Then, clone this repository and explore the documentation. You can list available containers using:
```bash
lsl -l
```
You can also start up this project's website with a lot more nicely-formatted information. You can run 
```bash
docker-compose build
```
then 
```bash
docker-compose up -d
```
In case of issues, assure that both ```docker-compose``` and ```build``` are installed. 
