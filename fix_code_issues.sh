#!/bin/bash

echo "Starting code quality check and fix..."

# Create missing __init__.py files in packages
find . -type d -not -path "./.git*" -not -path "./venv*" -not -path "./.venv*" -not -path "./logs*" -not -path "./__pycache__*" | while read dir; do
    if [ -d "$dir" ] && [ -z "$(find "$dir" -maxdepth 1 -name "*.py")" ]; then
        continue  # Skip directories without Python files
    fi
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        echo "Creating __init__.py in $dir"
        echo "# Auto-generated __init__.py" > "$dir/__init__.py"
    fi
done

# Check for missing imports
echo "Checking for import issues..."

# Fix import issues in client modules
for file in $(find client -name "*.py"); do
    if grep -q "from client" "$file"; then
        echo "Fixing relative imports in $file"
        sed -i 's/from client\./from ./g' "$file"
    fi
done

# Fix import issues in server modules
for file in $(find server -name "*.py"); do
    if grep -q "from server" "$file"; then
        echo "Fixing relative imports in $file"
        sed -i 's/from server\./from ./g' "$file"
    fi
done

# Fix import issues in shared modules
for file in $(find shared -name "*.py"); do
    if grep -q "from shared" "$file"; then
        echo "Fixing relative imports in $file"
        sed -i 's/from shared\./from ./g' "$file"
    fi
done

# Create missing directories for logs
mkdir -p logs

echo "Code quality check and fix complete!"
