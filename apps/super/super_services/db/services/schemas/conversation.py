from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Union, List
from enum import Enum
from super_services.libs.core.constant import DATETIME_FORMAT


class BlockEnum(str, Enum):
    html = "html"
    text = "text"
    media = "media"
    notebook = "notebook"
    status = "status"


class BlockTypeEnum(str, Enum):
    reply = "reply"
    text_msg = "text_msg"
    image_msg = "image_msg"
    video_msg = "video_msg"
    sys_msg = "sys_msg"
    content_block = "content_block"
    heading_block = "heading_block"
    pilot_response = "pilot_response"
    pilot_warning = "pilot_warning"
    question = "question"
    write = "write"
    notebook = "notebook"
    # SDK-specific block types
    location = "location"
    cards = "cards"
    json = "json"
    audio_msg = "audio_msg"
    file_msg = "file_msg"
    call = "call"
    callee_msg = "callee_msg"


class ReactionType(str, Enum):
    like = "like"
    dislike = "dislike"
    clap = "clap"


class BlockModelSchema(BaseModel):
    thread_id: str
    block_id: str
    user_id: Union[int, str]
    user: Dict = Field(default_factory=dict)
    block: BlockEnum
    block_type: BlockTypeEnum
    data: Dict = Field(default_factory=dict)
    media: Dict = Field(default_factory=dict)
    seq_number: int = Field(default=1)
    mentions: Optional[List[str]] = Field(default_factory=list)
    parent_id: Optional[str] = Field(default=None)
    parent: Optional[Dict] = Field(default_factory=dict)
    reaction_count: int = Field(default=0)
    pilot_handle: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)


class BlockList(BaseModel):
    thread_id: str
    block_id: str
    user_id: Union[int, str]
    user: Dict = Field(default_factory=dict)
    block: BlockEnum
    block_type: str
    data: Dict = Field(default_factory=dict)
    media: Dict = Field(default_factory=dict)
    seq_number: int = Field(default=1)
    reaction_count: int = Field(default=0)
    parent_id: Optional[str]
    parent: Optional[Dict] = Field(default_factory=dict)
    pilot_handle: Optional[str]
    created: datetime

    class Config:
        json_encoders = {datetime: lambda dt: dt.strftime(DATETIME_FORMAT)}


class BlockReactionSchema(BaseModel):
    thread_id: str
    block_id: str
    user_id: Union[int, str]
    reaction_type: ReactionType = Field(default=ReactionType.clap)
    reaction_count: int = Field(default=1)


class BlockCreateSchema(BaseModel):
    reaction_type: ReactionType = Field(default=ReactionType.clap)
    reaction_count: int = Field(default=1)


class CheggQuestionSolverLogs(BaseModel):
    thread_id: str
    user_id: Union[int, str]
    user: Dict
    pilot: str
    files: Union[List[Dict], Dict] = Field(default_factory=dict)
    response: Dict = Field(default_factory=dict)
    status: int = Field(default=1)
