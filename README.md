# Lightweight Subsystem for Linux (LSL)

## Project Overview

Hey! I'm Viktor Petrov, a student at Fontys University, currently working on this personal project as part of my Open Learning coursework in the second semester. LSL aims to streamline the management of virtualized Linux-based development environments, making it easier and faster for software engineers, system administrators, and DevOps teams to create, manage, and share their development setups.

## Project Goals

**What I want to achieve:**
- Develop an efficient Docker-based solution for managing development environments.
- Provide near-instant initialization of environments.
- Reduce resource usage compared to traditional virtual machines (VMs).
- Simplify environment sharing and synchronization across teams.
- Streamline workflows for developers and system administrators.

**Why this project:**
Current solutions often involve heavy VMs or complex container setups that are time-consuming and resource-intensive. LSL aims to address these pain points by offering a developer-friendly platform.

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

4. **Additional Enhancements:**
  - [ ] Container orchestration using Docker.
  - [ ] Secure authentication and efficient resource management.

## Realistic End Goal:
The primary objective is to create a functional and user-friendly container management system that significantly improves the development workflow, especially in collaborative environments. By focusing on efficiency, speed, and ease of use, LSL will be a valuable tool for developers working on various projects.

## Feedback and Contribution

As this project evolves, I welcome feedback and suggestions! If you have ideas or spot areas for improvement, feel free to open an issue or submit a pull request. Your input is greatly appreciated!
