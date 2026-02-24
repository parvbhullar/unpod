# Deployment Guide

Production deployment for the Unpod Voice Executor via Docker or Kubernetes.

For environment variables and local dev setup, see the [root README](../README.md).

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

### Environment Differences

| Setting | QA | Prod |
|---------|-----|------|
| Replicas | 1 | 2 |
| CPU request / limit | 2 / 4 | 4 / 8 |
| Memory request / limit | 4Gi / 8Gi | 8Gi / 16Gi |
| HPA min / max replicas | 1 / 5 | 2 / 10 |

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
  overlays/
    qa/                     # QA patches (1 replica, 4CPU/8Gi)
    prod/                   # Prod patches (2 replicas, 8CPU/16Gi, HPA 2-10)
```

## CLI Reference

The voice executor (`voice_executor_v3.py`) accepts these subcommands:

| Command | Purpose | Used by |
|---------|---------|---------|
| `start` | Production mode | Docker ENTRYPOINT, K8s, systemd |
| `dev` | Dev mode with debug logging | Local development |
| `download-files` | Pre-download ML models | Dockerfile build stage |
| `setup` | Set up local venv + .env | First-time dev setup |
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
./deploy.sh setup                # Set up local dev environment
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
  setup           Set up local dev environment (venv + .env)
  local           Run locally in dev mode
  validate        Check required env vars
  health          Check service connectivity
  test            Run unit tests
  k8s-qa          Deploy to K8s QA
  k8s-prod        Deploy to K8s Prod
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
