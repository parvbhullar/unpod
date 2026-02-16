import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dotenv import load_dotenv

# Load root .env (monorepo unified config), fallback to service-local .env
_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent  # executors/ → orchestration/ → super_services/ → super/ → apps/ → root
_root_env = _MONOREPO_ROOT / ".env"
if _root_env.exists():
    load_dotenv(str(_root_env), override=True)
else:
    load_dotenv(override=True)

from super_services.libs.core.utils import get_env_name
from super.core.voice.superkik import SuperkikAgentHandler

from super_services.db.services.repository.conversation_block import (
    _extract_user_from_message,
    save_message_block,
)
from super_services.voice.models.config import ModelConfig

from super_services.libs.core.block_processor import send_block_to_channel
from super_services.libs.logger import logger

from super.core.callback.base import BaseCallback
from super.core.context.schema import Message, Event


class MessageCallBack(BaseCallback):
    def __init__(self, *args, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def send(self, message: Message, thread_id: str):
        # Skip saving if thread_id is empty or None
        if not thread_id:
            logger.warning(
                "[MessageCallBack] Skipping block save - no thread_id available"
            )
            return

        if not isinstance(message, Message):
            message = Message.add_assistant_message(message)

        # Skip empty messages
        content = message.message
        data = message.data
        if not content and (not data or not isinstance(data, dict)):
            return

        # Debug: Log block save attempt
        logger.info(
            f"[MessageCallBack-SuperKik] Saving block for thread_id={thread_id}, "
            f"role={message.sender.role}, content_len={len(content or '')}"
        )

        # Save block using Message-based function
        block = save_message_block(message, thread_id)
        if not block:
            logger.warning(
                f"[MessageCallBack-SuperKik] save_message_block returned empty for thread_id={thread_id}"
            )
            return

        # Debug: Log successful save
        logger.info(
            f"[MessageCallBack-SuperKik] Block saved: block_id={block.get('block_id')}, "
            f"thread_id={thread_id}"
        )

        # Extract user for channel broadcast
        sender_user, _ = _extract_user_from_message(message)

        # Determine event type for channel
        event = (
            "block"
            if message.event not in [Event.TASK_END, Event.TASK_START]
            else message.event
        )
        send_block_to_channel(thread_id, block, sender_user, event=event)

    def receive(self, message: Message):
        print("Receive", message)


def main():
    env = get_env_name()
    AGENT_NAME = os.environ.get("AGENT_NAME", f"superkik-{env}-assistant-agent-v1")

    # SuperKik-specific config
    superkik_config = {
        "superkik": {
            "use_compact_prompt": os.environ.get("SUPERKIK_COMPACT_PROMPT", "false").lower() == "true",
            "enable_call_patching": os.environ.get("SUPERKIK_ENABLE_CALLS", "true").lower() == "true",
            "enable_booking": os.environ.get("SUPERKIK_ENABLE_BOOKING", "true").lower() == "true",
            "enable_preferences": os.environ.get("SUPERKIK_ENABLE_PREFERENCES", "true").lower() == "true",
            "max_search_results": int(os.environ.get("SUPERKIK_MAX_RESULTS", "5")),
            "default_search_radius_km": float(os.environ.get("SUPERKIK_SEARCH_RADIUS", "5.0")),
        },
        # STT configuration - deepgram nova-3 multilingual
        "stt_provider": os.environ.get("STT_PROVIDER", "deepgram"),
        "stt_model": os.environ.get("STT_MODEL", "nova-3"),
        "stt_language": os.environ.get("STT_LANGUAGE", "multi"),
        # TTS configuration - cartesia sonic-3
        "tts_provider": os.environ.get("TTS_PROVIDER", "cartesia"),
        "tts_model": os.environ.get("TTS_MODEL", "sonic-3"),
        "tts_voice": os.environ.get("TTS_VOICE", "95d51f79-c397-46f9-b49a-23763d3eaa2d"),
        "google_places": {
            "api_key": os.environ.get("GOOGLE_PLACES_API_KEY", ""),
        },
        "telephony": {
            "sip_domain": os.environ.get("SIP_DOMAIN", ""),
            "sip_username": os.environ.get("SIP_USERNAME", ""),
            "sip_password": os.environ.get("SIP_PASSWORD", ""),
        },
        'use_multilingual_turn_detection': "true",
        "enable_exa_search": True,  # Enable/disable plugin
        "tool_plugins": {
            "exa": {
                "max_results": 5,
                "include_twitter": True,
                "enable_research": True
            }
        },
    }

    model_config = ModelConfig()
    # Merge superkik config into model config
    if hasattr(model_config, 'config') and isinstance(model_config.config, dict):
        model_config.config.update(superkik_config)
    else:
        model_config.config = superkik_config

    superkik_agent = SuperkikAgentHandler(
        callback=MessageCallBack(),
        model_config=model_config,
        agent_name=AGENT_NAME,
    )
    superkik_agent.execute_agent()


if __name__ == "__main__":
    main()
