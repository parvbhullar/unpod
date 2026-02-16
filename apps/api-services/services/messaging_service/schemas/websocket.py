from typing import Dict, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from services.messaging_service.schemas.conversation import BlockEnum, BlockTypeEnum


class MessageEvent(str, Enum):
    block = "block"
    ping = "ping"
    action = "action"


class BlockEventData(BaseModel):
    block: BlockEnum
    block_type: BlockTypeEnum
    data: Dict = Field(default_factory=dict)
    parent_id: Optional[str]
    space: Optional[Dict] = Field(default_factory=dict)


class MessageReceived(BaseModel):
    event: MessageEvent
    data: Union[BlockEventData, Dict]
    pilot: Optional[str] = None


class MessageSend(MessageReceived):
    timestamp: int
