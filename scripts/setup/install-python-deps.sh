#!/bin/bash

set -e

echo "Installing Python dependencies..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install from pyproject.toml if poetry is available
if command -v poetry &> /dev/null; then
    echo "Installing dependencies with Poetry..."
    poetry install
else
    echo "Installing dependencies with pip..."

    # Install backend requirements
    if [ -f "apps/backend-core/requirements/local.txt" ]; then
        pip install -r apps/backend-core/requirements/local.txt
    fi
fi

# Install shared libraries in editable mode
echo "Installing shared Python libraries..."
for lib in libs/python/*/; do
    if [ -f "$lib/setup.py" ]; then
        echo "Installing $(basename $lib)..."
        pip install -e "$lib"
    fi
done

echo ""
echo "Python dependencies installed successfully!"
echo "Virtual environment: .venv"
echo ""
echo "To activate: source .venv/bin/activate"
