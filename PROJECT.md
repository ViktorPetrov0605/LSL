# Project code design & architectural document
# 1. Server Implementation

## 1.1 YAML Configuration Management

### 1.1.1 Schema Definition & Validation
- Define strict schemas (using PyYAML/JSONSchema) for:
    - `main.yaml`: global server settings (admin credentials, network, logging config)
    - `users.yaml`: user entries (UUID, username, password hash, allowed containers, metadata)
    - `containers.yaml`: container templates (image, resources, shared flag, env, volumes, net)
    - Per-user config: user-specific overrides (e.g., allowed containers, resource limits)
- Implement schema validation in `shared/schemas.py`:
    - Validate on load and before save
    - Raise clear, user-facing errors for violations

#### Tests
- Pytest: Load with valid/invalid data, test all required/optional fields
- Pytest: Missing, extra, wrong-typed fields
- Pytest: Attempt to save invalid config, assert error

---

### 1.1.2 Atomic Load/Save with Locking
- Use OS-level file locks (fcntl or portalocker)
- Write to temp file, atomic move to replace
- Handle concurrent admin/web edits to avoid race conditions
- Detect and recover from partial/corrupted writes

#### Tests
- Pytest: Simulate concurrent writes, verify no corruption
- Pytest: Force crash mid-write, verify config is recoverable

---

### 1.1.3 CRUD Operations
- Utility functions in `shared/config.py`:
    - Add/remove/update user (all attributes, including allowed containers)
    - Add/remove/update container (all fields)
    - Update admin credentials (secure password hash)
    - Admin can always edit per-user container access unless config file disables this for a user

#### Tests
- Pytest: Add, remove, update entries; verify persistence in YAML
- Pytest: Admin can edit per-user container list

---

## 1.2 REST API for Client Interaction

### 1.2.1 API Server Setup
- Use FastAPI for async endpoints and auto-docs
- Load configs at startup, reload on SIGHUP (signal handler)
- Serve on configurable host/port, support HTTPS

#### Tests
- Pytest: Start/stop, SIGHUP triggers reload, `/ping` returns 200

---

### 1.2.2 /get_config Endpoint
- Auth via UUID/token in header
- Returns merged user/container config as JSON
- Includes only containers user is allowed to access
- Returns HTTP 401 on invalid UUID, 400 on malformed req

#### Tests
- Pytest: Valid/invalid UUID, malformed request

---

### 1.2.3 /ping Endpoint
- Accepts UUID, updates last seen timestamp (in-memory, flush to disk on interval)
- Used for monitoring client liveness

#### Tests
- Pytest: Successful ping updates timestamp, invalid UUID returns error

---

### 1.2.4 /monitor Endpoint
- Returns:
    - Server CPU, RAM, disk (psutil)
    - Running containers (Docker SDK): name, image, owner, status
    - Last ping for each user

#### Tests
- Pytest: Mock psutil/Docker, edge cases (no clients/containers)

---

### 1.2.5 Error Handling & Rate Limiting
- Return structured JSON errors (code, message, details)
- Rate limit endpoints (e.g. 60/min per client)
- Log all errors (YAML logger)

#### Tests
- Pytest: Trigger rate limit, malformed JSON, verify errors/logs

---

## 1.3 Web Admin UI

### 1.3.1 Authentication
- Login page (admin credentials from `main.yaml`)
- Secure session cookie (HTTPOnly, Secure)
- Logout endpoint

#### Tests
- Pytest: Login/logout, session expiry

---

### 1.3.2 User Management
- List, add, edit, delete users
- Admin can set username, password, allowed containers, and metadata
- Can generate/reset user tokens

#### Tests
- Pytest: CRUD operations, verify YAML, token reset

---

### 1.3.3 Container Management
- List, add, edit, delete container templates
- Set all container fields (image, resources, shared, env, volumes, network)
- Assign containers to users

#### Tests
- Pytest: CRUD operations, verify YAML, assign containers

---

### 1.3.4 Web Error Handling & Permissions
- All actions require authentication
- CSRF protection for all forms
- Unauthorized/forbidden access returns errors

#### Tests
- Pytest: Unauthenticated/unauthorized, CSRF token required

---

## 1.4 Monitoring Dashboard

### 1.4.1 Client Status Table
- Table: username, UUID, last ping (age), allowed containers

### 1.4.2 Server Stats
- Show: CPU%, RAM, disk, running containers (with ownership)

### 1.4.3 Live Updates
- Use JavaScript polling or WebSocket for push updates

#### Tests
- Pytest: Simulate pings, high CPU, dashboard reflects state

---

## 1.5 Logging

### 1.5.1 Logging Utility
- Write logs as YAML entries (append-only)
- Log file: configurable location
- Rotate logs by size/age, keep N old logs

### 1.5.2 Error/Warn/Critical Hooks
- Log all unhandled exceptions, failed API/web actions
- Include timestamp, severity, context

#### Tests
- Pytest: Simulate errors, check YAML logs, log rotation

---

# 2. Client Implementation

## 2.1 Client Config/UUID Handling

### 2.1.1 UUID/Token Generation
- On first run, generate UUID/token, store in `config.yaml` (in user home or XDG config dir)
- If `config.yaml` missing/corrupt, regenerate or prompt user to reset

#### Tests
- Pytest: First run, corrupt config, reset

---

### 2.1.2 Config Fetch and Sync
- Fetch config from server (with UUID/token)
- Save to local cache
- Re-fetch on demand or at interval

#### Tests
- Pytest: Fetch, cache, reflect server changes

---

## 2.2 Ping Loop

### 2.2.1 Background Ping Thread
- Every minute, send `/ping` with UUID
- Retry on failure, exponential backoff
- Log persistent failures

#### Tests
- Pytest: Simulate network/server error, retry logic, log failures

---

## 2.3 CLI Command Parsing

### 2.3.1 CLI Parser
- Subcommands: `list`, `start`, `stop`, `persist`, `net`, `help`
- Show available containers for user, print errors/help for invalid usage

#### Tests
- Pytest: Valid/invalid args, help text

---

### 2.3.2 Command Dispatch
- Each CLI command calls appropriate function (container mgmt, config fetch, etc.)

#### Tests
- Pytest: Command triggers correct action

---

## 2.4 Container Management

### 2.4.1 Container Launch
- Use Docker SDK to start container:
    - Set image, env, volumes, network, resource limits from config
    - Support persistent volumes if requested

#### Tests
- Pytest: Mock Docker, verify parameters, handle bad images

---

### 2.4.2 Container Stop/Remove
- Stop by container name/UUID
- Remove volumes if not persistent
- Clean up resources

#### Tests
- Pytest: Stop/cleanup, handle non-existent container

---

### 2.4.3 Error Handling
- Catch and log Docker errors (missing Docker, permission, etc.)
- Show clear user-facing error messages

#### Tests
- Pytest: Simulate Docker missing/permission error, log

---

## 2.5 Multi-User Session Integration

### 2.5.1 Shared Container Detection
- If container is marked "shared", prepare for multi-user session

### 2.5.2 tmux/screen Launch
- Start tmux or screen in container if shared
- On session start, output instructions for users to connect:
    - "To join: ssh into server, then attach using: tmux attach -t <session-name>"

### 2.5.3 SSH Integration (if required)
- Optionally expose SSH server in container, manage access (keys/passwords)
- Document how users connect via SSH and attach to session

#### Tests
- Integration: Two users connect (SSH + tmux/screen), session teardown on stop

---

## 2.6 Client-Side Logging

### 2.6.1 Local Logging
- Log errors/warnings as YAML entries to local log file
- Rotate logs by size/age

#### Tests
- Pytest: Simulate errors, verify YAML logs, rotation

---

# 3. Shared/Utilities

## 3.1 Schema Validation Utilities

### 3.1.1 Reusable Validators
- Centralized YAML schema checks for all config files

#### Tests
- Pytest: Validate all config files, both valid/invalid

---

## 3.2 Hashing/UUID Utilities

### 3.2.1 Password Hashing
- Use PBKDF2 or bcrypt/sha256 for password hashes (admin, user)

### 3.2.2 UUID Generation
- Use Python's uuid4 for all IDs (user, client, container)

#### Tests
- Pytest: Hash/verify password, UUID uniqueness

---

## 3.3 Logging Utilities

### 3.3.1 YAML Logger
- Shared logger for both server and client, default YAML format, persistent

#### Tests
- Pytest: Log entry structure, test log rotation

---

# 4. Packaging & Distribution

## 4.1 PyInstaller Bundling

### 4.1.1 PyInstaller Spec Files
- Provide .spec files for client and server
- Bundle all dependencies and static files
- Build tested and supported on Linux (minimum-viable product target)

#### Tests
- Manual: Build and run on clean Linux VM

---

## 4.2 .deb Packaging (Optional)

### 4.2.1 Debian Control Files
- Create debian/ directory, control, postinst, prerm scripts for .deb package

#### Tests
- Manual: Install/uninstall on Ubuntu/Debian, check config/log persistence

---

# 5. Testing & CI

## 5.1 Pytest Suite

### 5.1.1 Unit Tests
- All modules/functions have comprehensive unit tests

### 5.1.2 Integration Tests
- Test startup, client-server config fetch, container management

### 5.1.3 Mocking
- Use pytest-mock for Docker, psutil, network, and file I/O

### 5.1.4 Code Coverage
- Enforce ≥90% coverage with pytest-cov

#### Tests
- All feature branches must pass tests, coverage check

---

## 5.2 GitHub Actions for Docs

### 5.2.1 Build Docs
- On push: build Sphinx/Markdown docs, fail build if errors

### 5.2.2 Lint YAML/Markdown
- Validate all configs/docs with yamllint/markdownlint

#### Tests
- Simulate doc error, assert build fails

---

# 6. Integration & Evaluation

## 6.1 End-to-End Testing

### 6.1.1 E2E Workflow
- Start server, register users, fetch config, launch containers, monitor, use web admin, exercise all CRUD

### 6.1.2 Performance Testing
- Measure: container launch latency, config fetch time, server CPU/memory under load

### 6.1.3 Error Injection
- Simulate network, Docker, file I/O failures; verify recovery/logging

---

# 7. Branching, Workflow, and Tests

## 7.1 Branching
- Each atomic task: `feature/<component>-<desc>`
- Test-only branches: `test/<component>-<desc>`

## 7.2 Tests Practices
- Test-driven: Write pytest tests before implementing features
- No merge to main without tests and code review

## 7.3 Parallelization
- Client/server can be built and tested in parallel
- Web admin, monitoring, CLI, packaging, and docs can be parallelized

---

# 8. Documentation

## 8.1 User Guide
- CLI usage (commands, flags, expected output)
- Config examples for all YAML files
- Troubleshooting common errors

## 8.2 Admin Guide
- Web admin usage (screenshots, workflows)
- Server setup, upgrade, backup/restore, reference for all config options

## 8.3 Developer Guide
- Code structure/modules, testing/CI, branching strategy, contribution guide (PR, code review, linter)

---

## **Summary Table of Major Tasks**

| Area            | Task/Subtask                                | Test Plan (Pytest)                        |
|-----------------|---------------------------------------------|-------------------------------------------|
| Server Config   | Schema validation, atomic load/save, CRUD   | Valid/invalid YAML, concurrency           |
| REST API        | /get_config, /ping, /monitor, error/rate    | Valid/invalid UUID, malformed, rate limit |
| Web Admin       | Auth, user/container CRUD, CSRF             | CRUD in YAML, session expiry, security    |
| Monitoring      | Dashboard, psutil, Docker SDK               | Simulate clients/CPU/containers           |
| Logging         | YAML logger, error hooks, rotation          | Simulate errors, corrupt logs             |
| Client Config   | UUID/gen, config fetch, sync                | First run, corrupt config, fetch changes  |
| CLI             | Parser, command dispatch                    | All commands, errors, help                |
| Containers      | Launch/stop, persist, net, errors           | Mock Docker, bad image, cleanup           |
| Multi-User      | tmux/screen, SSH, attach/teardown           | Integration: 2 users, teardown            |
| Shared Utils    | Schema/hash/UUID/log utils                  | All utility functions                     |
| Packaging       | PyInstaller/.deb (Linux MVP)                | Manual: clean Linux VM install            |
| Testing         | Pytest, coverage, integration, E2E          | ≥90% coverage, all features tested        |
| CI              | Docs build, lint, publish                   | Simulate doc errors, check build          |
| Docs            | User/admin/dev guides                       | Manual review                             |

---
