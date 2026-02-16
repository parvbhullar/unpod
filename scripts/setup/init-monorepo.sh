#!/bin/bash

set -e

echo "=========================================="
echo "Initializing Unpod Monorepo"
echo "=========================================="

# Check for required tools
echo "Checking required tools..."

if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed."
    exit 1
fi

echo "All required tools are available!"
echo ""

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v poetry &> /dev/null; then
    poetry install
else
    echo "Poetry not found, using pip..."
    pip install -r apps/backend-core/requirements/local.txt
fi

# Install shared Python libraries
echo "Installing shared Python libraries..."
for lib in libs/python/*/; do
    if [ -f "$lib/setup.py" ]; then
        echo "Installing $(basename $lib)..."
        pip install -e "$lib"
    fi
done

# Create environment files
echo "Creating environment files..."

# Backend .env
if [ ! -f "apps/backend-core/.env" ]; then
    if [ -f "apps/backend-core/.env.example" ]; then
        cp "apps/backend-core/.env.example" "apps/backend-core/.env"
        echo "Created apps/backend-core/.env from template"
    fi
fi

# Frontend .env.local
if [ ! -f "apps/web/.env.local" ]; then
    if [ -f "apps/web/.env.example" ]; then
        cp "apps/web/.env.example" "apps/web/.env.local"
        echo "Created apps/web/.env.local from template"
    fi
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x scripts/database/*.sh
chmod +x scripts/setup/*.sh

echo ""
echo "=========================================="
echo "Monorepo initialized successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start Docker services:    npm run docker:up"
echo "  2. Wait for databases:       npm run db:create"
echo "  3. Run migrations:           npm run migrate"
echo "  4. Start development:        npm run dev"
echo ""
echo "Useful commands:"
echo "  npm run dev          - Start frontend and backend"
echo "  npm run dev:web      - Start frontend only"
echo "  npm run dev:backend  - Start backend only"
echo "  npm run test:all     - Run all tests"
echo "  npm run lint:all     - Lint all projects"
echo "  npm run graph        - View project dependency graph"
echo ""
