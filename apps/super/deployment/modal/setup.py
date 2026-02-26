"""Interactive Modal deployment setup.

Usage:
    uv run python deployment/modal/setup.py          # Full setup
    uv run python deployment/modal/setup.py login     # Login only
    uv run python deployment/modal/setup.py secrets   # Upload secrets only
    uv run python deployment/modal/setup.py deploy    # Deploy only
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
MODAL_APP = os.path.join(os.path.dirname(__file__), "modal_app.py")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")

# Secrets required for the voice executor
_REQUIRED_SECRETS: dict[str, str] = {
    "LIVEKIT_URL": "LiveKit server URL",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "OPENAI_API_KEY": "OpenAI API key",
    "DEEPGRAM_API_KEY": "Deepgram STT API key",
}

_OPTIONAL_SECRETS: dict[str, str] = {
    "SETTINGS_FILE": "Settings module (default: super_services.settings.prod)",
    "ANTHROPIC_API_KEY": "Anthropic API key",
    "CARTESIA_API_KEY": "Cartesia TTS key",
    "MONGO_DSN": "MongoDB connection string",
    "REDIS_URL": "Redis connection URL",
    "SIP_OUTBOUND_TRUNK_ID": "LiveKit SIP trunk ID",
    "AGENT_NAME": "Agent name override",
    "WORKER_HANDLER": "Handler type (livekit or pipecat)",
}


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def _ensure_cli_installed() -> bool:
    """Check if modal CLI is installed, offer to install if not."""
    result = subprocess.run(
        ["which", "modal"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return True

    print("  Modal CLI not found.")
    print("  Install options:")
    print("    1) pip install modal")
    print("    2) uv add --dev modal")
    choice = input("\n  Auto-install via pip? [Y/n]: ").strip().lower()
    if choice == "n":
        print("  Please install manually and retry.")
        return False

    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "modal"],
        text=True,
    )
    if install.returncode != 0:
        print("  Installation failed. Try manually:")
        print("    pip install modal")
        return False

    print("  Modal CLI installed successfully.")
    return True


def _is_logged_in() -> bool:
    """Check if modal CLI is authenticated."""
    result = subprocess.run(
        ["modal", "profile", "current"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _read_env_file(path: str) -> dict[str, str]:
    """Read key=value pairs from a .env file."""
    env: dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                # Strip quotes from values
                val = value.strip().strip('"').strip("'")
                env[key.strip()] = val
    return env


def _prompt_secrets() -> dict[str, str]:
    """Upload all env vars from .env files to Modal secrets."""
    # Read both .env files (super_services/.env overrides root .env)
    root_env = _read_env_file(os.path.join(PROJECT_ROOT, ".env"))
    svc_env = _read_env_file(
        os.path.join(PROJECT_ROOT, "super_services", ".env")
    )
    # Merge: super_services values take priority
    secrets = {**root_env, **svc_env}

    # Strip inline comments from values (e.g. "value  #comment")
    for key in list(secrets):
        val = secrets[key]
        if "  #" in val:
            secrets[key] = val.split("  #")[0].strip()

    # Remove empty values and placeholder values
    secrets = {
        k: v for k, v in secrets.items()
        if v and not v.startswith("<your_")
    }

    print(f"\n  Collected {len(secrets)} env vars from:")
    print(f"    - .env ({len(root_env)} vars)")
    print(f"    - super_services/.env ({len(svc_env)} vars)")

    # Check for missing required secrets
    missing = [v for v in _REQUIRED_SECRETS if v not in secrets]
    if missing:
        print(f"\n  Warning: missing required keys: {', '.join(missing)}")
        for var in missing:
            hint = _REQUIRED_SECRETS[var]
            value = input(f"    {hint}\n    {var}: ").strip()
            if value:
                secrets[var] = value

    return secrets


def _generate_requirements() -> bool:
    """Generate requirements.txt from uv lockfile."""
    print("  Generating requirements.txt from uv.lock...")
    result = subprocess.run(
        [
            "uv", "export",
            "--no-dev",
            "--all-packages",
            "--no-editable",
            "--no-hashes",
            "--format", "requirements.txt",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print(f"  Error: uv export failed: {result.stderr.strip()}")
        return False

    lines = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("./") or stripped.startswith("super"):
            continue
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(line)

    with open(REQUIREMENTS_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    pkg_count = sum(
        1 for ln in lines if ln.strip() and not ln.strip().startswith("#")
    )
    print(f"  Generated requirements.txt ({pkg_count} packages)")
    return True


def step_login() -> bool:
    """Step 1: Login to Modal."""
    print("\n[Step 1/4] Modal Authentication")
    print("=" * 40)

    if not _ensure_cli_installed():
        return False

    if _is_logged_in():
        print("  Already logged in.")
        return True

    print("  Running modal token set...")
    result = _run(["modal", "token", "set"], check=False)
    if result.returncode != 0:
        print("\n  Login failed. Please try again.")
        return False

    print("  Login successful.")
    return True


def step_secrets() -> dict[str, str]:
    """Step 2: Collect and upload secrets to Modal."""
    print("\n[Step 2/4] Configure Secrets")
    print("=" * 40)
    print("  Secrets are stored in Modal's dashboard and injected")
    print("  as environment variables at runtime.\n")

    secrets = _prompt_secrets()

    missing = [v for v in _REQUIRED_SECRETS if v not in secrets]
    if missing:
        print(f"\n  Warning: missing required secrets: {', '.join(missing)}")
        print("  The deployment may fail without these.")
        proceed = input("  Continue anyway? [y/N]: ").strip().lower()
        if proceed != "y":
            sys.exit(1)

    # Build the modal secret create command (--force overwrites if exists)
    print("\n  Uploading secrets to Modal...")
    cmd = ["modal", "secret", "create", "unpod-secrets", "--force"]
    for key, value in secrets.items():
        cmd.append(f"{key}={value}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Warning: failed to set secrets: {result.stderr.strip()}")
        print("  You can set them manually:")
        print("    modal secret create unpod-secrets --force KEY=VALUE ...")
    else:
        print(f"  Saved {len(secrets)} secrets in 'unpod-secrets'.")

    return secrets


def step_review() -> bool:
    """Step 3: Review config before deploying."""
    print("\n[Step 3/4] Review Configuration")
    print("=" * 40)

    print("\n  Modal App: unpod-voice-agent")
    print("  Resources: 4 CPU, 8 GB RAM")
    print("  Min containers: 1")
    print("  Scaledown: 5 minutes")
    print("  Graceful shutdown: 600s")
    print(f"  App file: {MODAL_APP}")

    print()
    proceed = input("  Deploy with this configuration? [Y/n]: ").strip().lower()
    return proceed != "n"


def step_deploy() -> bool:
    """Step 4: Deploy to Modal."""
    print("\n[Step 4/4] Deploying to Modal")
    print("=" * 40)

    if not _ensure_cli_installed():
        return False

    os.chdir(PROJECT_ROOT)

    if not _generate_requirements():
        return False

    print("  Running modal deploy...")
    result = subprocess.run(
        ["modal", "deploy", "--env", "main", MODAL_APP],
        text=True,
        capture_output=False,
    )

    if result.returncode != 0:
        print("\n  Deployment failed.")
        return False

    print("\n  Deployment successful!")
    print("  Monitor:")
    print("    make modal-logs")
    print("    make modal-stop")
    return True


def cmd_full_setup() -> int:
    """Run all steps interactively."""
    print("Modal Deployment Setup")
    print("=" * 40)
    print("This will walk you through:")
    print("  1. Authenticate with Modal")
    print("  2. Upload secrets (API keys)")
    print("  3. Review deployment config")
    print("  4. Deploy the voice executor")
    print()

    proceed = input("Ready to start? [Y/n]: ").strip().lower()
    if proceed == "n":
        return 0

    if not step_login():
        return 1

    step_secrets()

    if not step_review():
        print("Cancelled.")
        return 0

    if not step_deploy():
        return 1

    return 0


def main() -> int:
    subcmd = sys.argv[1] if len(sys.argv) > 1 else "setup"

    commands = {
        "setup": cmd_full_setup,
        "login": lambda: 0 if step_login() else 1,
        "secrets": lambda: 0 if step_secrets() else 1,
        "deploy": lambda: 0 if step_deploy() else 1,
    }

    if subcmd in commands:
        return commands[subcmd]()

    print(f"Unknown command: {subcmd}")
    print(f"Available: {', '.join(commands)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
