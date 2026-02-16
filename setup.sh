#!/bin/bash
# =============================================================================
# Unpod - Quick Start Setup Script
# =============================================================================
# One command to get everything running:
#   ./setup.sh
#
# What it does:
#   1. Copies environment files (if not exist)
#   2. Installs npm dependencies
#   3. Installs Python dependencies (backend-core)
#   4. Starts Docker containers (PostgreSQL, MongoDB, Redis)
#   5. Waits for databases to be healthy
#   6. Runs Django migrations
#   7. Prints access URLs
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() { echo -e "\n${BLUE}==>${NC} $1"; }
print_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
print_err()  { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "============================================"
echo "  Unpod - Quick Start Setup"
echo "============================================"
echo ""

# -------------------------------------------------------------------
# 1. Check prerequisites
# -------------------------------------------------------------------
print_step "Checking prerequisites..."

missing=""
command -v node  >/dev/null 2>&1 || missing="$missing node"
command -v npm   >/dev/null 2>&1 || missing="$missing npm"
command -v python3 >/dev/null 2>&1 || missing="$missing python3"
command -v docker >/dev/null 2>&1 || missing="$missing docker"

if [ -n "$missing" ]; then
    print_err "Missing required tools:$missing"
    echo "Please install them and try again."
    exit 1
fi

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
    print_err "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_ok "All prerequisites found"

# -------------------------------------------------------------------
# 2. Copy environment files
# -------------------------------------------------------------------
print_step "Setting up environment files..."

if [ ! -f "apps/backend-core/.env.local" ]; then
    cp apps/backend-core/.env.docker apps/backend-core/.env.local
    print_ok "Created apps/backend-core/.env.local from .env.docker"
else
    print_warn "apps/backend-core/.env.local already exists, skipping"
fi

if [ ! -f "apps/web/.env.local" ]; then
    if [ -f "apps/web/.env.local.example" ]; then
        cp apps/web/.env.local.example apps/web/.env.local
        print_ok "Created apps/web/.env.local from example"
    fi
else
    print_warn "apps/web/.env.local already exists, skipping"
fi

# -------------------------------------------------------------------
# 3. Install npm dependencies
# -------------------------------------------------------------------
print_step "Installing npm dependencies..."
npm install --silent 2>&1 | tail -1
print_ok "npm dependencies installed"

# -------------------------------------------------------------------
# 4. Install Python dependencies (backend-core)
# -------------------------------------------------------------------
print_step "Installing Python dependencies for backend-core..."

if [ ! -d "apps/backend-core/.venv" ]; then
    python3 -m venv apps/backend-core/.venv
    print_ok "Created virtual environment at apps/backend-core/.venv"
fi

source apps/backend-core/.venv/bin/activate
pip install --upgrade pip --quiet
pip install -r apps/backend-core/requirements/local.txt --quiet
print_ok "Python dependencies installed"

# -------------------------------------------------------------------
# 5. Start Docker containers
# -------------------------------------------------------------------
print_step "Starting Docker containers (PostgreSQL, MongoDB, Redis)..."
docker compose -f docker-compose.simple.yml up -d

# -------------------------------------------------------------------
# 6. Wait for databases
# -------------------------------------------------------------------
print_step "Waiting for databases to be healthy..."

echo -n "  PostgreSQL: "
until docker exec unpod-postgres pg_isready -U postgres >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}ready${NC}"

echo -n "  MongoDB:    "
until docker exec unpod-mongodb mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}ready${NC}"

echo -n "  Redis:      "
until docker exec unpod-redis redis-cli ping >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}ready${NC}"

# -------------------------------------------------------------------
# 7. Run Django migrations
# -------------------------------------------------------------------
print_step "Running Django migrations..."
cd apps/backend-core
python manage.py migrate --no-input
cd ../..
print_ok "Migrations complete"

deactivate

# -------------------------------------------------------------------
# Done!
# -------------------------------------------------------------------
echo ""
echo "============================================"
echo -e "  ${GREEN}Setup complete!${NC}"
echo "============================================"
echo ""
echo "  Start development:"
echo "    npm run dev          # Frontend (3000) + Backend (8000)"
echo "    npm run dev:web      # Frontend only"
echo ""
echo "  Backend only (activate venv first):"
echo "    source apps/backend-core/.venv/bin/activate"
echo "    cd apps/backend-core && python manage.py runserver"
echo ""
echo "  Access:"
echo "    Frontend:    http://localhost:3000"
echo "    Backend API: http://localhost:8000"
echo "    Admin Panel: http://localhost:8000/unpod-admin/"
echo ""
echo "  Stop Docker:"
echo "    docker compose -f docker-compose.simple.yml down"
echo ""
