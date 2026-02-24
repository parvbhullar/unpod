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


def cmd_setup() -> int:
    """Set up local development environment."""
    import subprocess
    import shutil

    uv = shutil.which("uv")
    if not uv:
        print("Error: uv not found. Install it first:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1

    print("Setting up local environment...")

    # Sync dependencies
    print("\n[1/3] Syncing dependencies with uv...")
    ret = subprocess.call([uv, "sync", "--frozen"])
    if ret != 0:
        print("Failed to sync dependencies.", file=sys.stderr)
        return ret

    # Create .env from example if missing
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("\n[2/3] Creating .env from .env.example...")
        shutil.copy(".env.example", ".env")
        print("  Created .env — edit it with your API keys.")
    else:
        print("\n[2/3] .env already exists, skipping.")

    # Validate env
    print("\n[3/3] Validating environment...")
    ret = cmd_validate_env()
    if ret != 0:
        print(
            "\nSetup complete but some env vars are missing."
            " Edit .env and fill in the required values."
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


COMMANDS = {
    "validate-env": cmd_validate_env,
    "health": cmd_health,
    "test": cmd_test,
    "setup": cmd_setup,
    # start/dev/download-files handled by LiveKit cli.run_app
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

    # LiveKit commands (start, dev, download-files) pass through
    # to execute_agent which calls cli.run_app(sys.argv)
    cmd_start()
