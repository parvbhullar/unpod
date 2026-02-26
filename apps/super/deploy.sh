#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure uv is available; auto-install if missing (macOS + Linux)
if ! command -v uv &>/dev/null; then
    echo "uv not found — installing via astral.sh..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Load .env if present (safe parsing — handles values with special chars)
if [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and blank lines
        case "$line" in
            \#*|"") continue ;;
        esac
        # Only export lines that look like KEY=VALUE
        if echo "$line" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*='; then
            export "$line"
        fi
    done < "$SCRIPT_DIR/.env"
fi

usage() {
    cat <<EOF
Usage: ./deploy.sh <command> [args]

Commands:
  docker [build|run]     Build and/or run with Docker
  k8s <qa|prod>          Deploy to Kubernetes via kustomize
  cerebrium              Deploy to Cerebrium cloud
  setup                  Set up local dev environment (venv + .env)
  validate               Validate required environment variables
  health                 Check service connectivity
  local                  Run locally with uv (dev mode)
  test                   Run unit tests

Examples:
  ./deploy.sh docker build              # Build Docker image
  ./deploy.sh docker run                # Build + run Docker container
  ./deploy.sh k8s qa                    # Deploy to K8s QA overlay
  ./deploy.sh k8s prod                  # Deploy to K8s Prod overlay
  ./deploy.sh cerebrium                 # Deploy to Cerebrium cloud
  ./deploy.sh local                     # Run locally in dev mode
EOF
}

EXECUTOR="super_services/orchestration/executors/voice_executor_v3.py"

case "${1:-}" in
    docker)
        case "${2:-run}" in
            build)
                docker build -t voice-executor:"${IMAGE_TAG:-latest}" \
                    --build-arg PYTHON_VERSION="${PYTHON_VERSION:-3.12}" \
                    "$SCRIPT_DIR"
                ;;
            run)
                docker build -t voice-executor:"${IMAGE_TAG:-latest}" \
                    --build-arg PYTHON_VERSION="${PYTHON_VERSION:-3.12}" \
                    "$SCRIPT_DIR"
                docker run --rm --env-file "$SCRIPT_DIR/.env" \
                    voice-executor:"${IMAGE_TAG:-latest}" start
                ;;
            *)
                echo "Unknown docker subcommand: ${2}" >&2
                usage
                exit 1
                ;;
        esac
        ;;
    k8s)
        OVERLAY="${2:?Specify overlay: qa or prod}"
        if [ ! -d "$SCRIPT_DIR/deployment/k8s/overlays/$OVERLAY" ]; then
            echo "Unknown overlay: $OVERLAY (available: qa, prod)" >&2
            exit 1
        fi
        kubectl apply -k "$SCRIPT_DIR/deployment/k8s/overlays/$OVERLAY/"
        ;;
    cerebrium)
        uv run cerebrium deploy --config-file "$SCRIPT_DIR/deployment/cerebrium/cerebrium.toml"
        ;;
    setup)
        cd "$SCRIPT_DIR"
        uv sync
        uv run python "$EXECUTOR" setup
        ;;
    validate)
        cd "$SCRIPT_DIR"
        uv run python "$EXECUTOR" validate-env
        ;;
    health)
        cd "$SCRIPT_DIR"
        uv run python "$EXECUTOR" health
        ;;
    local)
        cd "$SCRIPT_DIR"
        uv run python "$EXECUTOR" validate-env
        uv run python "$EXECUTOR" dev
        ;;
    test)
        cd "$SCRIPT_DIR"
        uv run python "$EXECUTOR" test
        ;;
    *)
        usage
        ;;
esac
