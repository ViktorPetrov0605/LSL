#!/bin/bash
# Script to create feature branches and commit changes

BASE_DIR="/home/falken/LSL"
cd "$BASE_DIR" || exit 1

echo "Creating feature branches and committing changes..."

# 1. Client Config/UUID Handling
echo "1. Creating feature/client-config-uuid branch..."
git checkout -b feature/client-config-uuid
git add client/__init__.py client/config.py tests/client/__init__.py tests/client/test_config.py
git commit -m "Implement Client Config/UUID Handling (Task 2.1.1)"
git checkout main

# 2. Config Fetch and Sync
echo "2. Creating feature/client-sync branch..."
git checkout -b feature/client-sync
git add client/sync.py tests/client/test_sync.py
git commit -m "Implement Config Fetch and Sync (Task 2.1.2)"
git checkout main

# 3. Ping Loop
echo "3. Creating feature/client-ping branch..."
git checkout -b feature/client-ping
git add client/ping.py tests/client/test_ping.py
git commit -m "Implement Background Ping Thread (Task 2.2.1)"
git checkout main

# 4. Container Management
echo "4. Creating feature/client-containers branch..."
git checkout -b feature/client-containers
git add client/containers.py tests/client/test_containers.py
git commit -m "Implement Enhanced Container Management (Tasks 2.4.2, 2.4.3)"
git checkout main

# 5. Web Admin UI (In progress)
echo "5. Creating feature/web-admin-ui branch..."
git checkout -b feature/web-admin-ui
git add server/web_admin.py tests/server/test_web_admin.py site/templates/login.html site/templates/sidebar.html
git commit -m "Start implementing Web Admin UI Authentication (Task 1.3.1)"
git checkout main

# 6. Project Structure (README files in todo/done folders)
echo "6. Creating feature/project-structure branch..."
git checkout -b feature/project-structure
git add todo/README.md done/README.md
git commit -m "Update project task tracking and organization"
git checkout main

echo "7. Committing remaining files to backlog branch..."
git checkout -b backlog
git add .
git commit -m "Add remaining project files to backlog"
git checkout main

echo "Feature branches created and changes committed!"
