"""Interactive Cerebrium deployment setup.

Usage:
    uv run python deployment/cerebrium/setup.py          # Full setup (login + secrets + deploy)
    uv run python deployment/cerebrium/setup.py login     # Login only
    uv run python deployment/cerebrium/setup.py secrets   # Upload secrets only
    uv run python deployment/cerebrium/setup.py deploy    # Deploy only
    uv run python deployment/cerebrium/setup.py status    # Check deployment status
"""

import os
import subprocess
import sys

CEREBRIUM_TOML = os.path.join(os.path.dirname(__file__), "cerebrium.toml")
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")

# Secrets required for the voice executor to run on Cerebrium
_REQUIRED_SECRETS: dict[str, str] = {
    "LIVEKIT_URL": "LiveKit server URL (e.g. wss://your-server.livekit.cloud)",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "OPENAI_API_KEY": "OpenAI API key",
    "DEEPGRAM_API_KEY": "Deepgram STT API key",
}

_OPTIONAL_SECRETS: dict[str, str] = {
    "SETTINGS_FILE": "Settings module (default: super_services.settings.prod)",
    "ANTHROPIC_API_KEY": "Anthropic API key (fallback LLM)",
    "CARTESIA_API_KEY": "Cartesia TTS key",
    "MONGO_DSN": "MongoDB connection string",
    "REDIS_URI": "Redis connection URI",
}


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def _ensure_cli_installed() -> bool:
    """Check if cerebrium CLI is installed, offer to install if not."""
    result = subprocess.run(
        ["which", "cerebrium"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return True

    print("  Cerebrium CLI not found.")
    print("  Install options:")
    print("    1) pip install cerebrium")
    print("    2) brew tap cerebriumai/tap && brew install cerebrium")
    choice = input("\n  Auto-install via pip? [Y/n]: ").strip().lower()
    if choice == "n":
        print("  Please install manually and retry.")
        return False

    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "cerebrium"],
        text=True,
    )
    if install.returncode != 0:
        print("  Installation failed. Try manually:")
        print("    pip install cerebrium")
        return False

    print("  Cerebrium CLI installed successfully.")
    return True


def _is_logged_in() -> bool:
    """Check if cerebrium CLI is authenticated by listing projects."""
    result = subprocess.run(
        ["cerebrium", "projects", "list"],
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
                env[key.strip()] = value.strip()
    return env


def _prompt_secrets() -> dict[str, str]:
    """Prompt for secrets, pre-filling from .env if available."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    env = _read_env_file(env_path)
    secrets: dict[str, str] = {}

    print("\n  Required secrets (press Enter to use value from .env):\n")
    for var, hint in _REQUIRED_SECRETS.items():
        current = env.get(var, "")
        if current:
            display = current[:8] + "..." if len(current) > 12 else current
            value = input(f"    {hint}\n    {var} [{display}]: ").strip()
            secrets[var] = value if value else current
        else:
            value = input(f"    {hint}\n    {var}: ").strip()
            if value:
                secrets[var] = value

    print("\n  Optional secrets (press Enter to skip):\n")
    for var, hint in _OPTIONAL_SECRETS.items():
        current = env.get(var, "")
        if current:
            display = current[:8] + "..." if len(current) > 12 else current
            value = input(f"    {hint}\n    {var} [{display}]: ").strip()
            secrets[var] = value if value else current
        else:
            value = input(f"    {hint}\n    {var}: ").strip()
            if value:
                secrets[var] = value

    return secrets


def step_login() -> bool:
    """Step 1: Login to Cerebrium."""
    print("\n[Step 1/4] Cerebrium Authentication")
    print("=" * 40)

    if not _ensure_cli_installed():
        return False

    if _is_logged_in():
        print("  Already logged in.")
        return True

    print("  Opening Cerebrium login...")
    result = _run(["cerebrium", "login"], check=False)
    if result.returncode != 0:
        print("\n  Login failed. Please try again.")
        return False

    print("  Login successful.")
    return True


def step_secrets() -> dict[str, str]:
    """Step 2: Collect and upload secrets."""
    print("\n[Step 2/4] Configure Secrets")
    print("=" * 40)
    print("  Secrets are uploaded to Cerebrium's dashboard and injected")
    print("  as environment variables at runtime.\n")

    secrets = _prompt_secrets()

    missing = [v for v in _REQUIRED_SECRETS if v not in secrets]
    if missing:
        print(f"\n  Warning: missing required secrets: {', '.join(missing)}")
        print("  The deployment may fail without these.")
        proceed = input("  Continue anyway? [y/N]: ").strip().lower()
        if proceed != "y":
            sys.exit(1)

    # Upload each secret via cerebrium CLI
    print("\n  Uploading secrets to Cerebrium...")
    for key, value in secrets.items():
        result = subprocess.run(
            ["cerebrium", "secret", "set", key, value],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"    Set {key}")
        else:
            print(f"    Warning: failed to set {key}: {result.stderr.strip()}")

    print(f"  Uploaded {len(secrets)} secrets.")
    return secrets


def step_review() -> bool:
    """Step 3: Review config before deploying."""
    print("\n[Step 3/4] Review Configuration")
    print("=" * 40)

    if os.path.exists(CEREBRIUM_TOML):
        with open(CEREBRIUM_TOML) as f:
            print(f"\n  Config: {CEREBRIUM_TOML}")
            for line in f:
                print(f"    {line.rstrip()}")
    else:
        print(f"  Error: {CEREBRIUM_TOML} not found")
        return False

    print()
    proceed = input("  Deploy with this configuration? [Y/n]: ").strip().lower()
    return proceed != "n"


def _generate_requirements() -> bool:
    """Generate requirements.txt from uv lockfile, stripping local workspace refs."""
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
    )
    if result.returncode != 0:
        print(f"  Error: uv export failed: {result.stderr.strip()}")
        return False

    # Filter out local workspace paths (./super, ./super_services, etc.)
    # and comment lines with "via" annotations
    lines = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        # Skip local path refs (installed via COPY in Dockerfile)
        if stripped.startswith("./") or stripped.startswith("super"):
            continue
        # Skip blank lines and comment-only lines
        if not stripped or stripped.startswith("#"):
            continue
        # Keep indented "# via" comments for readability
        if stripped.startswith("# via"):
            lines.append(line)
            continue
        lines.append(line)

    with open(REQUIREMENTS_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    pkg_count = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
    print(f"  Generated requirements.txt ({pkg_count} packages)")
    return True


def step_deploy() -> bool:
    """Step 4: Deploy to Cerebrium."""
    print("\n[Step 4/4] Deploying to Cerebrium")
    print("=" * 40)

    if not _ensure_cli_installed():
        return False

    os.chdir(PROJECT_ROOT)

    if not _generate_requirements():
        return False

    result = subprocess.run(
        ["cerebrium", "deploy", "--config-file", CEREBRIUM_TOML],
        text=True,
        capture_output=False,
    )

    # cerebrium deploy may return 0 even on remote build failures
    if result.returncode != 0:
        print("\n  Deployment command failed.")
        return False

    print("\n  Deploy submitted. Check build status:")
    print("    make cerebrium-logs")
    print("    make cerebrium-status")
    return True


def cmd_full_setup() -> int:
    """Run all steps interactively."""
    print("Cerebrium Deployment Setup")
    print("=" * 40)
    print("This will walk you through:")
    print("  1. Authenticate with Cerebrium")
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


def cmd_status() -> int:
    """Check deployment status."""
    print("Checking Cerebrium deployment status...")
    result = _run(["cerebrium", "status", "unpod-voice-agent"], check=False)
    return result.returncode


def main() -> int:
    subcmd = sys.argv[1] if len(sys.argv) > 1 else "setup"

    commands = {
        "setup": cmd_full_setup,
        "login": lambda: 0 if step_login() else 1,
        "secrets": lambda: 0 if step_secrets() else 1,
        "deploy": lambda: 0 if step_deploy() else 1,
        "status": cmd_status,
    }

    if subcmd in commands:
        return commands[subcmd]()

    print(f"Unknown command: {subcmd}")
    print(f"Available: {', '.join(commands)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
