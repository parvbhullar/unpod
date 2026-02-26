import os
import sys

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

from super_services.libs.logger import logger

# Required env vars for the voice executor to function
REQUIRED_ENV_VARS = [
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "OPENAI_API_KEY",
    "DEEPGRAM_API_KEY",
]

DEFAULT_AGENT_TEMPLATE = "unpod-{env}-general-agent-v3"
DEFAULT_HANDLER_TYPE = "livekit"


def _lazy_imports():
    """Import heavy modules only when needed (not for health/validate)."""
    from super.core.voice.voice_agent_handler import VoiceAgentHandler
    from super_services.db.services.repository.conversation_block import (
        _extract_user_from_message,
        save_message_block,
    )
    from super_services.voice.models.config import ModelConfig
    from super_services.libs.core.block_processor import send_block_to_channel
    from super.core.callback.base import BaseCallback
    from super.core.context.schema import Message, Event

    return {
        "VoiceAgentHandler": VoiceAgentHandler,
        "_extract_user_from_message": _extract_user_from_message,
        "save_message_block": save_message_block,
        "ModelConfig": ModelConfig,
        "send_block_to_channel": send_block_to_channel,
        "BaseCallback": BaseCallback,
        "Message": Message,
        "Event": Event,
    }


class MessageCallBack:
    """Callback for saving and broadcasting voice message blocks.

    Defined at module level so multiprocessing can serialize it.
    Heavy imports are deferred to method calls.
    """

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def send(self, message, thread_id: str) -> None:
        from super_services.db.services.repository.conversation_block import (
            _extract_user_from_message,
            save_message_block,
        )
        from super_services.libs.core.block_processor import (
            send_block_to_channel,
        )
        from super.core.context.schema import Message, Event

        if not thread_id:
            logger.warning(
                "[MessageCallBack] Skipping block save"
                " - no thread_id available"
            )
            return

        if not isinstance(message, Message):
            message = Message.add_assistant_message(message)

        content = message.message
        data = message.data
        if not content and (
            not data or not isinstance(data, dict)
        ):
            return

        logger.info(
            f"[MessageCallBack-Voice] Saving block for"
            f" thread_id={thread_id},"
            f" role={message.sender.role},"
            f" content_len={len(content or '')}"
        )

        block = save_message_block(message, thread_id)
        if not block:
            logger.warning(
                "[MessageCallBack-Voice]"
                " save_message_block returned empty"
                f" for thread_id={thread_id}"
            )
            return

        logger.info(
            f"[MessageCallBack-Voice] Block saved:"
            f" block_id={block.get('block_id')},"
            f" thread_id={thread_id}"
        )

        sender_user, _ = _extract_user_from_message(message)

        event = (
            "block"
            if message.event
            not in [Event.TASK_END, Event.TASK_START]
            else message.event
        )
        send_block_to_channel(
            thread_id, block, sender_user, event=event
        )

    def receive(self, message) -> None:
        print("Receive", message)


# --- CLI Commands ---


def cmd_validate_env() -> int:
    """Check all required environment variables are set."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        for v in missing:
            print(f"  MISSING: {v}", file=sys.stderr)
        print(
            f"\n{len(missing)} required env var(s) missing.",
            file=sys.stderr,
        )
        return 1
    print("All required env vars set.")
    return 0


def cmd_health() -> int:
    """Check connectivity to external services."""
    checks: list[tuple[str, bool]] = []

    # MongoDB
    try:
        from pymongo import MongoClient

        dsn = os.environ.get("MONGO_DSN", "")
        if dsn:
            client = MongoClient(dsn, serverSelectionTimeoutMS=3000)
            client.server_info()
            checks.append(("MongoDB", True))
        else:
            checks.append(("MongoDB", False))
    except Exception:
        checks.append(("MongoDB", False))

    # Redis
    try:
        import redis

        url = os.environ.get("REDIS_URI", "")
        if url:
            r = redis.from_url(url, socket_timeout=3)
            r.ping()
            checks.append(("Redis", True))
        else:
            checks.append(("Redis (optional)", True))
    except Exception:
        checks.append(("Redis", False))

    # LiveKit (check URL is reachable)
    try:
        import urllib.request

        lk_url = os.environ.get("LIVEKIT_URL", "")
        if lk_url:
            http_url = lk_url.replace("wss://", "https://").replace(
                "ws://", "http://"
            )
            req = urllib.request.Request(
                http_url, method="HEAD"
            )
            urllib.request.urlopen(req, timeout=5)
            checks.append(("LiveKit", True))
        else:
            checks.append(("LiveKit", False))
    except Exception:
        # LiveKit may not respond to HEAD but URL is set
        lk_url = os.environ.get("LIVEKIT_URL", "")
        checks.append(("LiveKit", bool(lk_url)))

    all_ok = all(ok for _, ok in checks)
    for name, ok in checks:
        status = "OK" if ok else "FAIL"
        print(f"  {name}: {status}")

    if all_ok:
        print("\nAll health checks passed.")
    else:
        print("\nSome health checks failed.")
    return 0 if all_ok else 1


def cmd_test() -> int:
    """Run unit tests via pytest."""
    import subprocess

    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/", "-v"]
    )


def _read_env_file(path: str = ".env") -> dict[str, str]:
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


def _write_env_file(env: dict[str, str], path: str = ".env") -> None:
    """Write key=value pairs to a .env file, preserving comments."""
    lines: list[str] = []
    existing_keys: set[str] = set()

    # Preserve existing file structure (comments, blanks, ordering)
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                raw = line.rstrip("\n")
                stripped = raw.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    existing_keys.add(key)
                    if key in env:
                        lines.append(f"{key}={env[key]}")
                        continue
                lines.append(raw)

    # Append any new keys not already in the file
    for key, value in env.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# Descriptions shown when prompting for each required var
_ENV_VAR_HINTS: dict[str, str] = {
    "LIVEKIT_URL": "LiveKit server URL (e.g. wss://your-server.livekit.cloud)",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "OPENAI_API_KEY": "OpenAI API key",
    "DEEPGRAM_API_KEY": "Deepgram STT API key",
}

# Optional vars to offer during setup (key -> hint)
_OPTIONAL_ENV_HINTS: dict[str, str] = {
    "SETTINGS_FILE": "Settings module (default: super_services.settings.qa)",
    "ANTHROPIC_API_KEY": "Anthropic API key (fallback LLM)",
    "CARTESIA_API_KEY": "Cartesia TTS key",
    "MONGO_DSN": "MongoDB connection string",
    "REDIS_URI": "Redis connection URI",
    "PREFECT_POSTGRES_URL": "Prefect Postgres URL (e.g. postgresql+asyncpg://user:pass@host/prefect)",
    "PREFECT_REDIS_URL": "Prefect Redis URL (QA/prod messaging)",
    "DOCKER_REGISTRY_URL": "Docker/OCIR registry URL",
    "DOCKER_REGISTRY_USER": "Docker registry username",
    "DOCKER_REGISTRY_PASSWORD": "Docker registry password",
}


def _prompt_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Interactively prompt for required env vars. Returns updated env."""
    print("\nConfiguring required environment variables...")
    print("(Press Enter to keep existing value, or type a new one)\n")

    for var in REQUIRED_ENV_VARS:
        current = env.get(var, "")
        hint = _ENV_VAR_HINTS.get(var, var)
        if current:
            display = current[:8] + "..." if len(current) > 12 else current
            value = input(f"  {hint}\n  {var} [{display}]: ").strip()
        else:
            value = input(f"  {hint}\n  {var}: ").strip()
        if value:
            env[var] = value

    print("\nOptional variables (press Enter to skip):\n")
    for var, hint in _OPTIONAL_ENV_HINTS.items():
        current = env.get(var, "")
        if current:
            display = current[:8] + "..." if len(current) > 12 else current
            value = input(f"  {hint}\n  {var} [{display}]: ").strip()
        else:
            value = input(f"  {hint}\n  {var}: ").strip()
        if value:
            env[var] = value

    return env


def cmd_setup() -> int:
    """Set up local development environment."""
    import shutil

    print("Setting up environment...\n")

    # Step 1: Create .env from example if missing
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("[1/3] Creating .env from .env.example...")
        shutil.copy(".env.example", ".env")
    elif not os.path.exists(".env"):
        print("[1/3] Creating empty .env...")
        with open(".env", "w") as f:
            f.write("")
    else:
        print("[1/3] .env already exists.")

    # Step 2: Prompt for env vars
    print("\n[2/3] Configuring environment variables...")
    env = _read_env_file(".env")
    env = _prompt_env_vars(env)
    _write_env_file(env, ".env")
    print("\n  Saved to .env")

    # Step 3: Validate
    print("\n[3/3] Validating environment...")
    # Reload env vars into os.environ so validation works
    for key, value in env.items():
        os.environ[key] = value
    ret = cmd_validate_env()
    if ret != 0:
        print(
            "\nSetup complete but some required vars are still empty."
            " Edit .env to fill them in."
        )
    else:
        print("\nSetup complete! Run with: make local")

    return 0


def cmd_start():
    """Start the voice agent (production mode).

    Delegates to LiveKit cli.run_app() which reads sys.argv.
    """
    from super_services.libs.core.utils import get_env_name

    deps = _lazy_imports()
    env = get_env_name()
    agent_name = os.environ.get(
        "AGENT_NAME", DEFAULT_AGENT_TEMPLATE.format(env=env)
    )
    handler_type = os.environ.get(
        "WORKER_HANDLER", DEFAULT_HANDLER_TYPE
    )

    voice_agent = deps["VoiceAgentHandler"](
        callback=MessageCallBack(),
        model_config=deps["ModelConfig"](),
        agent_name=agent_name,
        handler_type=handler_type,
    )
    voice_agent.execute_agent()


def cmd_download_files() -> int:
    """Pre-download ML models without connecting to any databases.

    Only imports LiveKit agents CLI — no DB or service imports needed.
    Safe to run during Docker build where DB is unreachable.
    """
    from livekit.agents import cli, WorkerOptions

    # Minimal entrypoint stub — download-files doesn't invoke it
    async def _noop(ctx):
        pass

    # Ensure sys.argv has the download-files subcommand for LiveKit CLI
    sys.argv = [sys.argv[0], "download-files"]
    cli.run_app(
        WorkerOptions(entrypoint_fnc=_noop, agent_name="download"),
    )
    return 0


COMMANDS = {
    "validate-env": cmd_validate_env,
    "health": cmd_health,
    "test": cmd_test,
    "setup": cmd_setup,
    "download-files": cmd_download_files,
}

USAGE = """\
Usage: python voice_executor_v3.py <command>

Commands:
  start            Start voice agent (production)
  dev              Start voice agent (dev mode, debug logging)
  download-files   Pre-download ML models
  health           Check MongoDB, Redis, LiveKit connectivity
  validate-env     Validate required environment variables
  test             Run unit tests via pytest
  setup            Set up local dev environment (venv + .env)
"""


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1]

    # Custom commands handled here
    if command in COMMANDS:
        sys.exit(COMMANDS[command]())

    # LiveKit commands (start, dev) pass through
    # to execute_agent which calls cli.run_app(sys.argv)
    cmd_start()
