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
  cerebrium [setup]      Setup + deploy to Cerebrium (interactive)
  cerebrium deploy       Deploy to Cerebrium (skip login/secrets)
  cerebrium logs         View Cerebrium logs
  cerebrium status       Check Cerebrium deployment status
  modal [deploy]         Deploy voice executor to Modal
  modal dev              Run Modal in dev mode (live reload)
  modal logs             View Modal logs
  modal stop             Stop Modal deployment
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
  ./deploy.sh cerebrium                 # Setup + deploy to Cerebrium (interactive)
  ./deploy.sh cerebrium deploy          # Deploy only (skip login/secrets)
  ./deploy.sh modal                     # Deploy to Modal
  ./deploy.sh modal dev                 # Modal dev mode (live reload)
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
        case "${2:-setup}" in
            setup)
                uv run python "$SCRIPT_DIR/deployment/cerebrium/setup.py" setup
                ;;
            deploy)
                uv run python "$SCRIPT_DIR/deployment/cerebrium/setup.py" deploy
                ;;
            logs)
                uv run cerebrium logs unpod-voice-agent
                ;;
            status)
                uv run cerebrium status unpod-voice-agent
                ;;
            *)
                echo "Unknown cerebrium subcommand: ${2}" >&2
                echo "Available: setup, deploy, logs, status"
                exit 1
                ;;
        esac
        ;;
    modal)
        MODAL_SETUP="$SCRIPT_DIR/deployment/modal/setup.py"
        MODAL_APP="$SCRIPT_DIR/deployment/modal/modal_app.py"
        case "${2:-setup}" in
            setup)
                uv run python "$MODAL_SETUP" setup
                ;;
            deploy)
                uv run python "$MODAL_SETUP" deploy
                ;;
            dev)
                cd "$SCRIPT_DIR"
                uv export --no-dev --all-packages --no-editable --no-hashes --format requirements.txt \
                    | grep -v '^\./\|^super\|^$\|^#' > requirements.txt
                modal serve "$MODAL_APP"
                ;;
            logs)
                modal app logs unpod-voice-agent
                ;;
            stop)
                modal app stop unpod-voice-agent
                ;;
            *)
                echo "Unknown modal subcommand: ${2}" >&2
                echo "Available: setup, deploy, dev, logs, stop"
                exit 1
                ;;
        esac
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
