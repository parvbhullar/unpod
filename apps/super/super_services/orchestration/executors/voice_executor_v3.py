import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dotenv import load_dotenv
load_dotenv(override=True)

from super_services.libs.core.utils import get_env_name
from super.core.voice.voice_agent_handler import VoiceAgentHandler

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
            f"[MessageCallBack-Voice] Saving block for thread_id={thread_id}, "
            f"role={message.sender.role}, content_len={len(content or '')}"
        )

        # Save block using Message-based function
        block = save_message_block(message, thread_id)
        if not block:
            logger.warning(
                f"[MessageCallBack-Voice] save_message_block returned empty for thread_id={thread_id}"
            )
            return

        # Debug: Log successful save
        logger.info(
            f"[MessageCallBack-Voice] Block saved: block_id={block.get('block_id')}, "
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
    env  = get_env_name()
    AGENT_NAME = os.environ.get("AGENT_NAME", f"unpod-{env}-general-agent-v3")
    # AGENT_NAME = os.environ.get("AGENT_NAME", f"superkik-{env}-assistant-agent-v1")


    voice_agent = VoiceAgentHandler(
        callback=MessageCallBack(), model_config=ModelConfig(), agent_name=AGENT_NAME, handler_type=os.environ.get("WORKER_HANDLER", "livekit")
    )
    voice_agent.execute_agent()


if __name__ == "__main__":
    main()
