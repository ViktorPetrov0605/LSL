#!/bin/bash

# Script to merge all feature branches into main

# Array of branches to merge
BRANCHES=(
  "feature/project-structure" 
  "feature/client-config-uuid" 
  "feature/client-sync"
  "feature/client-ping"
  "feature/client-containers"
  "feature/web-admin-ui"
)

# Make sure we're on main
git checkout main || { echo "Failed to checkout main"; exit 1; }

# Create directories if they don't exist
mkdir -p client server shared config logs tests site

# Merge each branch
for branch in "${BRANCHES[@]}"; do
  echo "Merging $branch into main..."
  git merge --no-ff "$branch" -m "Merge branch '$branch' into main" || { 
    echo "Failed to merge $branch - resolving conflict..."; 
    git checkout --theirs . || echo "Failed to checkout theirs";
    git add . || echo "Failed to add files";
    git commit -m "Resolved merge conflict by taking changes from $branch" || echo "Failed to commit resolved conflicts";
  }
done

# Copy important files from backlog
echo "Copying important files from backlog..."
git checkout backlog -- shared/ server/ config/ site/templates/ || echo "Failed to copy some directories from backlog"

# Add the copied files
git add shared/ server/ config/ site/templates/ 2>/dev/null || echo "No new files to add from backlog"

# Commit the copied files if there are any changes
git diff --staged --quiet || git commit -m "Add missing files from backlog"

echo "Merge complete! Check for any remaining issues."
