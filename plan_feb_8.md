# Plan: Make Unpod Repository Public with Simple Docker Setup

## Goal
Transform the repository for public open source use with simple Docker commands that anyone can use.

## Current State Summary
- **Only `backend-core` has actual code** - 5 other microservices are empty stubs
- Docker setup is complex: 6 PostgreSQL instances, MongoDB, Redis, Kafka
- Hardcoded credentials in multiple files (security issue)
- CLAUDE.md references non-existent infrastructure (k8s, terraform, helm)
- No simple "quick start" path for newcomers

---

## Implementation Plan

### Phase 1: Create Simple Docker Setup

**New File: `/docker-compose.simple.yml`**
Minimal setup with just what's needed to run backend-core:
- 1 PostgreSQL (port 5432)
- 1 MongoDB (port 27017)
- 1 Redis (port 6379)
- No Kafka (optional, in full docker-compose.yml)

**Keep existing `/docker-compose.yml`** for full microservices architecture with Kafka.

### Phase 2: Security Cleanup

**Files to fix:**
| File | Issue | Fix |
|------|-------|-----|
| `/apps/backend-core/docker-compose.yml` | Hardcoded MySQL password `Admin@123` | Delete file (redundant) |
| `/infrastructure/docker/services/postgres/init.sql` | Hardcoded `app_password` | Remove user creation, use env vars |
| `/scripts/database/create-databases.sh` | Wrong container names, hardcoded secrets | Fix container names, use env vars |

### Phase 3: Environment Files

**New files:**
1. `/.env.example` - Root level Docker env vars
2. `/apps/backend-core/.env.docker` - Docker-ready defaults (copy to .env.local)
3. `/apps/backend-core/.env.minimal` - Absolute minimum config

**Update `/apps/backend-core/.env.example`:**
- Add section headers: REQUIRED / OPTIONAL
- Document which services are needed for which features

### Phase 4: Quick Start Tools

**New File: `/Makefile`**
```
make quick-start  # One command to rule them all
make setup        # Initial setup
make dev          # Start development
make clean        # Stop and cleanup
```

**New File: `/setup.sh`**
```bash
./setup.sh  # One-liner for quick start
```

Both will:
1. Copy .env.docker to .env.local if not exists
2. Install npm dependencies
3. Install Python dependencies
4. Start Docker containers
5. Wait for databases
6. Run migrations
7. Print access URLs

### Phase 5: Documentation Updates

**Update `/CLAUDE.md`:**
1. Add "Getting Started (5 minutes)" section at TOP
2. Remove references to non-existent: `kubernetes/`, `terraform/`, `helm/`, `admin/`
3. Change `admin` app reference to `unpod-tauri`
4. Mark microservices as "template stubs for future development"
5. Add section explaining docker-compose.simple.yml vs docker-compose.yml

**Update `/README.md`:**
1. Add prominent Quick Start at TOP
2. Add "Project Status" section (what's working vs planned)
3. Simplify architecture to reflect reality
4. Mark infrastructure as "planned" where applicable

### Phase 6: Package.json Updates

Add new npm scripts:
```json
"docker:simple": "docker-compose -f docker-compose.simple.yml up -d",
"docker:simple:down": "docker-compose -f docker-compose.simple.yml down",
"quick-start": "npm run docker:simple && npm run migrate"
```

---

## Files to Create
| File | Purpose |
|------|---------|
| `/docker-compose.simple.yml` | Minimal Docker (PostgreSQL, MongoDB, Redis) |
| `/Makefile` | Make commands for easy setup |
| `/setup.sh` | One-liner setup script |
| `/.env.example` | Root Docker environment template |
| `/apps/backend-core/.env.docker` | Docker-ready env defaults |
| `/apps/backend-core/.env.minimal` | Minimum required env vars |

## Files to Update
| File | Changes |
|------|---------|
| `/CLAUDE.md` | Add Quick Start, fix inaccuracies |
| `/README.md` | Add Quick Start, clarify project status |
| `/package.json` | Add docker:simple scripts |
| `/infrastructure/docker/services/postgres/init.sql` | Remove hardcoded credentials |
| `/scripts/database/create-databases.sh` | Fix container names, use env vars |
| `/apps/backend-core/.env.example` | Add REQUIRED/OPTIONAL sections |

## Files to Delete
| File | Reason |
|------|--------|
| `/apps/backend-core/docker-compose.yml` | Inconsistent MySQL setup, redundant |

---

## Expected User Experience After Implementation

```bash
# Clone the repo
git clone https://github.com/your-org/unpod.git
cd unpod

# Option 1: One command
./setup.sh

# Option 2: Make
make quick-start

# Option 3: Manual
docker-compose -f docker-compose.simple.yml up -d
npm install
pip install -r apps/backend-core/requirements/local.txt
cd apps/backend-core && python manage.py migrate

# Start development
make dev
# OR
npm run dev
```

**Access:**
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/unpod-admin/
- Frontend: http://localhost:3000

---

## Verification

After implementation, test the complete flow:

1. **Fresh clone test:**
   ```bash
   rm -rf /tmp/unpod-test
   git clone . /tmp/unpod-test
   cd /tmp/unpod-test
   ./setup.sh
   ```

2. **Verify services:**
   - `docker ps` shows postgres, mongodb, redis running
   - `curl http://localhost:8000/health/` returns OK
   - Admin panel loads at http://localhost:8000/unpod-admin/

3. **Verify no secrets committed:**
   - `grep -r "Admin@123" .` returns nothing
   - `grep -r "app_password" .` returns nothing (except comments)

4. **Documentation check:**
   - README.md Quick Start section is first thing visible
   - CLAUDE.md doesn't reference non-existent directories
