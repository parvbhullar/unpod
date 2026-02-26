# Deployment Guide

Production deployment for the Unpod Voice Executor via Docker, Kubernetes, Cerebrium, or systemd.

For environment variables and local dev setup, see the [root README](../README.md).

## Prerequisites

`uv` is required for all local and systemd workflows. If it's not installed,
both `make` and `deploy.sh` will auto-install it via the
[official installer](https://docs.astral.sh/uv/getting-started/installation/).

## Docker

### Build and Run

```bash
# Build image
make build

# Build + run
make run

# Custom Python version (default: 3.12)
PYTHON_VERSION=3.10 make build

# Using deploy.sh
./deploy.sh docker build
./deploy.sh docker run
```

### Production Docker Compose

```bash
cd deployment
docker compose -f docker-compose.prod.yml up -d
```

Resource limits: 4 CPUs, 8G RAM. Logs rotated at 100MB / 5 files.

## Kubernetes

Uses [kustomize](https://kustomize.io/) with base manifests and per-environment overlays.

### 1. Create secrets

```bash
# From .env file
kubectl create secret generic voice-executor-secrets --from-env-file=.env

# Or apply the template and fill values manually
kubectl apply -f deployment/k8s/base/secret.yaml
```

### 2. Deploy

```bash
# QA
make k8s-qa
# or
kubectl apply -k deployment/k8s/overlays/qa/

# Prod
make k8s-prod
# or
kubectl apply -k deployment/k8s/overlays/prod/
```

### Design Notes

Based on the [LiveKit agent deployment reference](https://github.com/livekit-examples/agent-deployment/blob/main/kubernetes/agent-manifest.yaml):

- **`terminationGracePeriodSeconds: 600`** — Gives agents 10 minutes to finish active conversations before pod shutdown. Critical for graceful scaling and rolling updates.
- **Guaranteed QoS (requests = limits)** — Base and prod use equal requests/limits for predictable voice performance. QA uses burstable for cost savings.
- **Base resources: 4 CPU / 8Gi** — Good for ~30 concurrent 1:1 AI conversations per pod.

### Environment Differences

| Setting | Base | QA | Prod |
|---------|------|-----|------|
| Replicas | 1 | 1 | 2 |
| CPU request / limit | 4 / 4 | 2 / 4 | 8 / 8 |
| Memory request / limit | 8Gi / 8Gi | 4Gi / 8Gi | 16Gi / 16Gi |
| QoS class | Guaranteed | Burstable | Guaranteed |
| HPA min / max replicas | 1 / 5 | 1 / 5 | 2 / 10 |
| Graceful shutdown | 600s | 600s | 600s |

### Prefect on Kubernetes

Prefect server + worker can also be deployed to K8s with horizontal scaling.

```bash
# Deploy only Prefect
make k8s-prefect-qa
make k8s-prefect-prod

# Or deploy everything (executor + Prefect)
make k8s-qa
make k8s-prod
```

The K8s deployment uses the `kubernetes` work pool type (`call-work-pool-k8s`) instead
of `docker`. Each flow run spawns a K8s Job, enabling autoscaling via HPA.

#### Prefect K8s Environment Differences

| Setting | QA | Prod |
|---------|-----|------|
| Server replicas | 1 | 2 |
| Server CPU req / limit | 1 / 2 | 2 / 4 |
| Server memory req / limit | 2Gi / 4Gi | 4Gi / 8Gi |
| Worker replicas | 1 | 2 |
| Worker CPU req / limit | 500m / 1 | 1 / 2 |
| Worker memory req / limit | 512Mi / 1Gi | 1Gi / 2Gi |
| Worker HPA min / max | 1 / 5 | 2 / 10 |

### Manifest Structure

```
deployment/k8s/
  base/                     # Shared manifests
    deployment.yaml         # Pod spec, probes, resources
    service.yaml            # ClusterIP service
    configmap.yaml          # SETTINGS_FILE, AGENT_NAME, WORKER_HANDLER
    secret.yaml             # API keys template (fill in or use kubectl create)
    hpa.yaml                # HorizontalPodAutoscaler (CPU 70%, memory 80%)
    kustomization.yaml
    prefect/                # Prefect K8s manifests
      server-deployment.yaml
      server-service.yaml
      worker-deployment.yaml
      worker-rbac.yaml      # ServiceAccount, Role, RoleBinding for Jobs
      worker-hpa.yaml
      migrate-job.yaml      # DB migration (run once)
      configmap.yaml
      secret.yaml
      kustomization.yaml
  overlays/
    qa/                     # QA patches (1 replica, 4CPU/8Gi)
      prefect-patches.yaml  # Prefect QA resource overrides
    prod/                   # Prod patches (2 replicas, 8CPU/16Gi, HPA 2-10)
      prefect-patches.yaml  # Prefect Prod resource overrides
```

## Cerebrium

Deploy the voice executor to [Cerebrium](https://www.cerebrium.ai/) for managed
cloud hosting with autoscaling.

### Prerequisites

1. Install the Cerebrium CLI: `pip install cerebrium`
2. Authenticate: `cerebrium login`
3. Upload environment variables (API keys) via the
   [Cerebrium dashboard](https://dashboard.cerebrium.ai/) secrets tab.
   Required: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`,
   `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`.

### Deploy

```bash
# One-click deploy
make cerebrium-deploy

# Or using deploy.sh
./deploy.sh cerebrium

# View logs
make cerebrium-logs
```

### Configuration

Config lives in `deployment/cerebrium/`:

| File | Purpose |
|------|---------|
| `cerebrium.toml` | Project config (hardware, scaling, dependencies) |
| `Dockerfile` | Container spec (simpler than root Dockerfile) |

Default scaling: 1-5 replicas, 4 CPU, 8 GB RAM. Edit `cerebrium.toml` to adjust.

### How It Works

Cerebrium builds the custom Dockerfile, which:
1. Installs dependencies from `requirements-livekit.txt`
2. Copies `super/` and `super_services/`
3. Pre-downloads ML models via `download-files`
4. Runs the voice executor on port 8600

Environment variables are injected automatically from Cerebrium's secrets manager.

## Systemd (Linux)

Deploy the voice executor as a systemd service on a Linux box. This is the
simplest way to run on a bare VM (Ubuntu/Debian).

### Quick deploy

```bash
# Clone the repo, then from the project root:

# Step 1: Install uv + deps, configure .env (prompts for API keys)
make setup

# Step 2: Deploy the systemd service
make deploy-service
```

**`make setup`** handles everything needed before running:

1. Auto-installs `uv` if missing
2. Runs `uv sync` to install Python dependencies
3. Interactively prompts for required API keys (LiveKit, OpenAI, Deepgram)
   and optional ones (Anthropic, Cartesia, MongoDB, Redis)
4. Saves all values to `.env`

**`make deploy-service`** then deploys the service:

1. Copies the service file to `/etc/systemd/system/`, setting
   `WorkingDirectory` to the current repo path
2. Reloads systemd, enables, and restarts the service

### Manual steps

```bash
# Copy service file (adjusting WorkingDirectory)
sudo sed 's|WorkingDirectory=.*|WorkingDirectory=/your/repo/path|' \
    deployment/services/voice_lk_executor_v3.service \
    | sudo tee /etc/systemd/system/voice_lk_executor_v3.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable voice_lk_executor_v3
sudo systemctl start voice_lk_executor_v3
```

### Managing the service

```bash
sudo systemctl status voice_lk_executor_v3   # Check status
sudo systemctl restart voice_lk_executor_v3  # Restart
sudo journalctl -u voice_lk_executor_v3 -f   # Follow logs
```

Logs are also written to:
- `/var/log/voice_lk_executor_v3.out.log` (stdout)
- `/var/log/voice_lk_executor_v3.err.log` (stderr)

Memory limits: 8G max, 7G high watermark (configured in the service file).

## CLI Reference

The voice executor (`voice_executor_v3.py`) accepts these subcommands:

| Command | Purpose | Used by |
|---------|---------|---------|
| `start` | Production mode | Docker ENTRYPOINT, K8s, systemd |
| `dev` | Dev mode with debug logging | Local development |
| `download-files` | Pre-download ML models | Dockerfile build stage |
| `setup` | Set up local venv + .env | First-time setup (`make setup`) |
| `health` | Check MongoDB, Redis, LiveKit | K8s probes, Docker HEALTHCHECK |
| `validate-env` | Check required env vars | deploy.sh pre-flight |
| `test` | Run pytest | CI, local dev |

```bash
# Examples
uv run python super_services/orchestration/executors/voice_executor_v3.py start
uv run python super_services/orchestration/executors/voice_executor_v3.py health
uv run python super_services/orchestration/executors/voice_executor_v3.py validate-env
```

## deploy.sh

```bash
./deploy.sh docker build         # Build Docker image
./deploy.sh docker run           # Build + run container
./deploy.sh k8s qa               # Deploy K8s QA overlay
./deploy.sh k8s prod             # Deploy K8s Prod overlay
./deploy.sh cerebrium            # Deploy to Cerebrium cloud
./deploy.sh setup                # Install deps + configure .env (interactive)
./deploy.sh validate             # Check required env vars
./deploy.sh health               # Check service connectivity
./deploy.sh local                # Run locally in dev mode
./deploy.sh test                 # Run unit tests
```

## Makefile Targets

```
$ make help
  build           Build Docker image
  run             Build + run Docker container
  setup           Install deps + configure .env (interactive)
  local           Run locally in dev mode
  validate        Check required env vars
  health          Check service connectivity
  test            Run voice agent test suite
  deploy-service  Deploy systemd service (run make setup first)
  prefect-up      Start Prefect server + worker (local)
  prefect-down    Stop Prefect server + worker (local)
  prefect-deploy  Register Prefect flow deployments
  prefect-refresh Sync deps + rebuild task image + re-register
  prefect-remote  Start Prefect for qa/prod (ENV=qa|prod)
  k8s-qa          Deploy all to K8s QA (executor + Prefect)
  k8s-prod        Deploy all to K8s Prod (executor + Prefect)
  k8s-prefect-qa  Deploy only Prefect to K8s QA
  k8s-prefect-prod Deploy only Prefect to K8s Prod
  cerebrium-deploy Deploy to Cerebrium cloud
  cerebrium-logs  View Cerebrium deployment logs
  help            Show this help
```

## Troubleshooting

### Missing environment variables

```bash
make validate
# Prints which required vars are missing
```

### Health check failing

```bash
make health
# Shows status of MongoDB, Redis, LiveKit
```

### Docker build fails on native extensions

The root Dockerfile includes gcc/g++/python3-dev in the builder stage. If you're using a custom base image, ensure these are installed.

### LiveKit agent not connecting

1. Verify `LIVEKIT_URL` is reachable: `curl -I https://your-livekit-server.com`
2. Check `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are correct
3. Ensure `SIP_OUTBOUND_TRUNK_ID` starts with `ST_` if using SIP

### Out of memory in Kubernetes

Increase resource limits in the overlay patches (`deployment/k8s/overlays/<env>/patches.yaml`) or adjust HPA thresholds.
