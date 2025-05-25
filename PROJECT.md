# 1. Server Implementation

## 1.1 YAML Configuration Management

### 1.1.1 Schema Definition & Validation
- Define JSONSchema or PyYAML-based schemas for:
    - `main.yaml`
    - `users.yaml`
    - `containers.yaml`
    - Per-user config
- Implement schema validation utility in `shared/schemas.py`
    - Validate on load and before save
    - Raise clear errors on failure

#### Tests
- Pytest: Load each config with valid/invalid data
- Pytest: Missing required fields, wrong types, extra fields
- Pytest: Attempt to save invalid config, assert error raised

---

### 1.1.2 Atomic Load/Save with Locking
- Implement atomic file read/write with OS-level file locks
- Ensure no partial writes (use temp file + move)
- Handle concurrent admin/web edits

#### Tests
- Pytest: Simulate concurrent writes, assert no corruption
- Pytest: Force crash mid-write, verify recovery

---

### 1.1.3 CRUD Operations
- Utility functions:
    - Add/remove/update user
    - Add/remove/update container
    - Update admin credentials

#### Tests
- Pytest: Add user, verify in YAML
- Pytest: Remove container, verify not present
- Pytest: Update admin hash, verify persistence

---

## 1.2 REST API for Client Interaction

### 1.2.1 API Server Setup
- Flask/FastAPI app in `lsl_server.py`
- Load configs at startup, reload on SIGHUP

#### Tests
- Pytest: Start server, check `/ping` returns 200

---

### 1.2.2 /get_config Endpoint
- Auth via UUID/token (in `users.yaml`)
- Return user/container config as JSON

#### Tests
- Pytest: Valid UUID returns config
- Pytest: Invalid UUID returns 401
- Pytest: Malformed request returns 400

---

### 1.2.3 /ping Endpoint
- Accepts UUID, updates last seen timestamp
- Stores in memory and persists periodically

#### Tests
- Pytest: Valid ping updates timestamp
- Pytest: Invalid UUID returns error

---

### 1.2.4 /monitor Endpoint
- Returns:
    - Server CPU (psutil)
    - List of running containers (Docker SDK)
    - Last ping for each user

#### Tests
- Pytest: Mock psutil/Docker, assert correct data
- Pytest: No clients, no containers edge case

---

### 1.2.5 Error Handling & Rate Limiting
- Return clear JSON errors for all endpoints
- Limit pings/requests per client per minute

#### Tests
- Pytest: Exceed rate limit, assert error
- Pytest: Malformed JSON, assert error

---

## 1.3 Web Admin UI

### 1.3.1 Authentication
- Login screen (admin credentials from `main.yaml`)
- Secure session cookie
- Logout

#### Tests
- Pytest: Valid/invalid login, session expiry

---

### 1.3.2 User Management
- List users
- Add user (username, password hash, containers, UUID auto-gen)
- Edit user (password, containers)
- Delete user

#### Tests
- Pytest: Add user, verify YAML updated
- Pytest: Edit user, verify changes
- Pytest: Delete user, verify removal

---

### 1.3.3 Container Management
- List containers
- Add container (all config fields)
- Edit container
- Delete container

#### Tests
- Pytest: Add/edit/delete container, verify YAML

---

### 1.3.4 Web Error Handling & Permissions
- All actions require login
- CSRF protection

#### Tests
- Pytest: Unauthenticated access denied
- Pytest: CSRF token required

---

## 1.4 Monitoring Dashboard

### 1.4.1 Client Status Table
- Show: username, UUID, last ping (age), allowed containers

### 1.4.2 Server Stats
- Show: CPU%, memory, disk (psutil)
- Show: Running containers (Docker SDK)

### 1.4.3 Live Updates
- Auto-refresh or WebSocket for live stats

#### Tests
- Pytest: Simulate pings, check dashboard updates
- Pytest: Simulate high CPU, verify display

---

## 1.5 Logging

### 1.5.1 Logging Utility
- Write JSON lines per schema to log file
- Rotate logs (size/age)

### 1.5.2 Error/Warn/Critical Hooks
- Log all unhandled exceptions
- Log all failed API/web actions

#### Tests
- Pytest: Simulate error, check log file
- Pytest: Corrupt log file, verify recovery

---

# 2. Client Implementation

## 2.1 Client Config/UUID Handling

### 2.1.1 UUID/Token Generation
- On first run, generate UUID/token, store in `config.yaml`
- If config.yaml missing/corrupt, regenerate or prompt

#### Tests
- Pytest: First run creates config
- Pytest: Corrupt config handled

---

### 2.1.2 Config Fetch and Sync
- Fetch config from server with UUID/token
- Save to local cache
- Re-fetch on CLI command or interval

#### Tests
- Pytest: Mock server, fetch config
- Pytest: Server config change reflected after fetch

---

## 2.2 Ping Loop

### 2.2.1 Background Ping Thread
- Every minute, send `/ping` with UUID
- Retry on failure, exponential backoff

#### Tests
- Pytest: Simulate network error, assert retry
- Pytest: Server sees updated ping

---

## 2.3 CLI Command Parsing

### 2.3.1 CLI Parser
- Support: list, start, stop, persist, net mode, help
- Validate input, print errors/help

#### Tests
- Pytest: All commands, valid/invalid args
- Pytest: Help output

---

### 2.3.2 Command Dispatch
- Map CLI commands to functions (container mgmt, config fetch, etc.)

#### Tests
- Pytest: Each command triggers correct function

---

## 2.4 Container Management

### 2.4.1 Container Launch
- Use Docker SDK to start container:
    - Image, env, volumes, net mode from config
    - Persist volumes if requested

#### Tests
- Pytest: Mock Docker, assert correct params
- Pytest: Bad image, assert error

---

### 2.4.2 Container Stop/Remove
- Stop running container by name/UUID
- Remove volumes if not persistent

#### Tests
- Pytest: Stop running container, assert cleanup
- Pytest: Attempt to stop nonexistent container, assert error

---

### 2.4.3 Error Handling
- Detect and log Docker errors (missing Docker, permission, etc.)

#### Tests
- Pytest: Simulate Docker not running, assert error logged

---

## 2.5 Multi-User Session Integration

### 2.5.1 Shared Container Detection
- If container is marked \"shared\", prepare for multi-user session

### 2.5.2 tmux/screen Launch
- Start tmux/screen in container
- Provide attach command/instructions to user

### 2.5.3 SSH Integration (if required)
- Optionally set up SSH server in container, manage access

#### Tests
- Integration test: Two users attach to same session
- Pytest: Session teardown on container stop

---

## 2.6 Client-Side Logging

### 2.6.1 Local Logging
- Write errors/warnings to log file (JSON lines)
- Rotate logs

#### Tests
- Pytest: Simulate error, check log file

---

# 3. Shared/Utilities

## 3.1 Schema Validation Utilities

### 3.1.1 Reusable Validators
- Centralize schema checks for YAML files

#### Tests
- Pytest: Validate all config files, good/bad data

---

## 3.2 Hashing/UUID Utilities

### 3.2.1 Password Hashing
- Use PBKDF2/sha256 for admin/user passwords

### 3.2.2 UUID Generation
- Use Python uuid4 for user/client/container IDs

#### Tests
- Pytest: Hash/verify password
- Pytest: UUID uniqueness

---

## 3.3 Logging Utilities

### 3.3.1 JSON Logger
- Shared logger for server/client

#### Tests
- Pytest: Log entry format

---

# 4. Packaging & Distribution

## 4.1 PyInstaller Bundling

### 4.1.1 PyInstaller Spec Files
- Create spec for client and server
- Bundle all dependencies

#### Tests
- Manual: Build and run on clean VM

---

## 4.2 .deb Packaging (Optional)

### 4.2.1 Debian Control Files
- Create debian/ directory, control, postinst, prerm scripts

#### Tests
- Manual: Install/uninstall on Ubuntu/Debian

---

# 5. Testing & CI

## 5.1 Pytest Suite

### 5.1.1 Unit Tests
- Each module/function has unit tests

### 5.1.2 Integration Tests
- Spin up test server, multiple clients, run full workflows

### 5.1.3 Mocking
- Use pytest-mock for Docker, psutil, network, etc.

### 5.1.4 Code Coverage
- Enforce ≥90% with pytest-cov

#### Tests
- All feature branches must have passing tests

---

## 5.2 GitHub Actions for Docs

### 5.2.1 Build Docs
- On push, build Sphinx/Markdown docs

### 5.2.2 Lint YAML/Markdown
- Validate all docs/configs

#### Tests
- Simulate doc error, assert build fails

---

# 6. Integration & Evaluation

## 6.1 End-to-End Testing

### 6.1.1 E2E Workflow
- Start server, register users, fetch config, launch containers, monitor, web admin CRUD

### 6.1.2 Performance Testing
- Measure container launch latency, config fetch time, server CPU under load

### 6.1.3 Error Injection
- Simulate network/Docker failures, verify logs and recovery

---

# 7. Branching, Workflow, and Tests

## 7.1 Branching
- Each atomic task in its own branch: `feature/<component>-<desc>`
- Test branch if needed: `test/<component>-<desc>`

## 7.2 Tests Practices
- Write test first (pytest), then implement feature
- No merge to main without tests and code review

## 7.3 Parallelization
- Client and server can be developed/tested in parallel
- Web admin, monitoring, CLI, packaging can be parallelized

---

# 8. Documentation

## 8.1 User Guide
- CLI usage, config examples, troubleshooting

## 8.2 Admin Guide
- Web admin, server setup, config reference

## 8.3 Developer Guide
- Code structure, testing, branching, contribution

---



## **Summary Table of Major Tasks**

| Area            | Task/Subtask                                | Test Plan (Pytest)                        |
|-----------------|---------------------------------------------|-------------------------------------------|
| Server Config   | Schema validation, atomic load/save, CRUD   | Valid/invalid YAML, concurrency           |
| REST API        | /get_config, /ping, /monitor, error/rate    | Valid/invalid UUID, malformed, rate limit |
| Web Admin       | Auth, user/container CRUD, CSRF             | CRUD reflected in YAML, session expiry    |
| Monitoring      | Dashboard, psutil, Docker SDK               | Simulate clients/CPU/containers           |
| Logging         | JSON logger, error hooks, rotation          | Simulate errors, corrupt logs             |
| Client Config   | UUID/gen, config fetch, sync                | First run, corrupt config, fetch changes  |
| CLI             | Parser, command dispatch                    | All commands, errors, help                |
| Containers      | Launch/stop, persist, net, errors           | Mock Docker, bad image, cleanup           |
| Multi-User      | tmux/screen, SSH, attach/teardown           | Integration: 2 users, session teardown    |
| Shared Utils    | Schema/hash/UUID/log utils                  | All utility functions                     |
| Packaging       | PyInstaller/.deb                            | Manual: clean VM install                  |
| Testing         | Pytest, coverage, integration, E2E          | ≥90% coverage, all features tested        |
| CI              | Docs build, lint, publish                   | Simulate doc errors, check build          |
| Docs            | User/admin/dev guides                       | Manual review                             |

---

