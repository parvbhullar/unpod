import enum
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Type, Any, Optional, List, Union

# from pydantic import field_validator, model_validator, BaseModel, create_model
from pydantic import BaseModel, Field, create_model

from super.core.context.unit_of_work import UOW
from super.core.resource.model_providers.schema import LanguageModelResponse


def clean_path(url):
    url = url.replace("\\", "/")
    if not url.startswith("https://"):
        url = url.replace("https:/", "https://")
    return url


class ContentType(str, enum.Enum):
    # TBD what these actually are.
    MARKDOWN = "markdown"
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    FOLDER = "folder"
    DICT = "dict"
    LIST = "dict"
    XML = "xml"
    EXCEPTION = "exception"
    CLASS_OBJECT = "class_object"


class ContentItem(ABC):
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the content item"""
        ...

    @property
    @abstractmethod
    def type(self) -> ContentType:
        """Type of the content item"""
        ...

    @property
    @abstractmethod
    def source(self) -> Optional[str]:
        """A string indicating the source location of the content item"""
        ...

    @property
    @abstractmethod
    def content(self) -> str:
        """The content represented by the content item"""
        ...

    def __str__(self) -> str:
        return (
            f"{self.description}, source: {self.source})\n"
            "```\n"
            f"{self.content}\n"
            "```"
        )

    @property
    def summary(self) -> str:
        # TODO write a function to summarise the content
        return self.content


@dataclass
class FileContentItem(ContentItem):
    file_path: Path
    type = ContentType.FILE

    @property
    def source(self) -> str:
        return f"local file '{self.file_path}'"

    @property
    def content(self) -> str:
        return clean_path(str(self.file_path))

    @property
    def description(self) -> str:
        return f"The contents of the file '{self.file_path}' in the workspace"


@dataclass
class ImageContentItem(ContentItem):
    file_path: Path
    type = ContentType.IMAGE

    @property
    def source(self) -> str:
        return f"local file '{self.file_path}'"

    @property
    def content(self) -> str:
        return clean_path(str(self.file_path))

    @property
    def description(self) -> str:
        return f"The contents of the image '{self.file_path}' in the workspace"


@dataclass
class FolderContentItem(ContentItem):
    path: Path
    type = ContentType.FOLDER

    def __post_init__(self) -> None:
        assert self.path.exists(), "Selected path does not exist"
        assert self.path.is_dir(), "Selected path is not a directory"

    @property
    def description(self) -> str:
        return f"The contents of the folder '{self.path}' in the workspace"

    @property
    def source(self) -> str:
        return f"local folder '{self.path}'"

    @property
    def content(self) -> str:
        items = [f"{p.name}{'/' if p.is_dir() else ''}" for p in self.path.iterdir()]
        items.sort()
        return "\n".join(items)


@dataclass
class ObjectContent(ContentItem):
    @property
    def source(self) -> Optional[str]:
        return self.obj_source

    @property
    def content(self) -> str:
        return str(self.obj_content)

    @property
    def type(self) -> ContentType:
        return self.obj_type

    obj_content: Union[List, Dict]
    obj_source: Optional[str] = None
    obj_type = ContentType.CLASS_OBJECT

    @property
    def description(self) -> str:
        return f"The is object of '{self.source}'"

    @staticmethod
    def add(content: dict | list, source: str = None):
        knowledge = ObjectContent(content, source)
        knowledge.content_type = (
            isinstance(content, dict) and ContentType.DICT or ContentType.LIST
        )
        return knowledge


class Content(ContentItem):
    @property
    def type(self) -> ContentType:
        return self.content_type

    @property
    def description(self) -> str:
        return f"The content of object of '{self.type}'"

    content: str = ""
    content_type: ContentType = ContentType.TEXT
    source: Optional[str] = None
    content_metadata: Dict[str, Any] = {}
    content_model: BaseModel = str

    @staticmethod
    def add_content_item(
        content: str = None,
        content_type: str = "text",
        source: str = None,
        content_metadata: Dict[str, Any] = {},
    ):
        knowledge = Content()
        knowledge.content = content
        knowledge.content_type = content_type
        knowledge.source = source
        knowledge.content_metadata = content_metadata
        return knowledge

    @classmethod
    def create_model_class(cls, class_name: str, mapping: Dict[str, Type]):
        new_class = create_model(class_name, **mapping)

        # @field_validator("*")
        @classmethod
        def check_name(v, field):
            if field.name not in mapping.keys():
                raise ValueError(f"Unrecognized block: {field.name}")
            return v

        # @model_validator(mode="before")
        @classmethod
        def check_missing_fields(values):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")
            return values

        new_class.__validator_check_name = classmethod(check_name)
        new_class.__root_validator_check_missing_fields = classmethod(
            check_missing_fields
        )
        return new_class


class Role(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    SYSTEM = "system"

    def __str__(self):
        return self.value


class Event(str, enum.Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    AGENT_MESSAGE = "agent_message"
    USER_MESSAGE = "user_message"
    QUESTION = "question"
    TASK_START = "task_start"
    TASK_END = "task_end"
    STREAM = "stream"
    NOTIFICATION = "notification"

    def __str__(self):
        return self.value


class User(BaseModel):
    """Struct for metadata about a sender."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: Role
    data: dict = {}

    @property
    def username(self):
        return f"{self.name} ({self.role})"

    @classmethod
    def add_user(
        cls,
        name: str = "System",
        role: Role = Role.SYSTEM,
        _id: str = str(uuid.uuid4()),
        data: dict = None,
    ):
        if not data:
            data = {}
        return cls(id=_id, name=name, role=role, data=data)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "role": self.role, "data": self.data}

    def __str__(self):
        return self.name + ":{" + str(self.data) + "}"


class MessageContent(BaseModel):
    pass


class Focus(str, enum.Enum):
    PUBLIC = "public"
    MY_AGENTS = "my_agents"
    SELECTED_AGENT = "selected_agent"
    MY_SPACE = "my_space"

    def __str__(self):
        return self.value


class Message(UOW):
    """Struct for a message and its metadata."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: User
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = [""]
    recipient: User = User.add_user(name="System", role=Role.SYSTEM)
    attachments: list[ContentItem] = []
    event: Event = Event.USER_MESSAGE
    focus: Focus = Focus.PUBLIC
    history: list["Message"] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v),
            enum.Enum: lambda v: v.value,
            BaseModel: lambda v: v.dict(),
            Content: lambda v: {
                "content": v.content,
                "content_type": v.type.value,
                "source": v.source,
                "content_metadata": v.content_metadata,
            },
        }

    @classmethod
    def create(
        cls,
        message: str,
        user: User = None,
        event: Event = Event.USER_MESSAGE,
        attachments: list[ContentItem] = None,
        data: Any = None,
        focus: Focus = Focus.PUBLIC,
        **kwargs,
    ):
        if not attachments:
            attachments = []
        if not user:
            user = User.add_user()
        if data is None:
            data = {}

        return cls(
            sender=user,
            message=message,
            attachments=attachments,
            event=event,
            data=data,
            focus=focus,
            **kwargs,
        )

    @classmethod
    def from_model_response(
        cls, lmr: LanguageModelResponse, session_id=None, user: User = None, **kwargs
    ):
        """Create a Message instance from a LanguageModelResponse object."""
        # Extract the message content from the LanguageModelResponse
        content = lmr.content.get("response", lmr.content.get("content", ""))
        if not user:
            # Assume 'assistant' is a role; adjust as needed
            user = User.add_user(lmr.model_info.model_name, Role.ASSISTANT)
        # Set the event to LANGUAGE_MODEL_RESPONSE or appropriate event
        event = Event.AGENT_MESSAGE
        # Use the entire lmr as data
        data = {}
        if lmr.model_info is not None:
            data = lmr.model_info.dict()
        #data=lmr.model_info.dict()
        data['total_cost']=lmr.total_cost
        data['prompt_tokens']=lmr.prompt_tokens_used
        data['completion_tokens']=lmr.completion_tokens_used
        
        return cls(
            sender=user,
            message=content,
            event=event,
            data=data,
            session_id=session_id,
            **kwargs,
        )

    @classmethod
    def from_block(cls, block_json: dict, **kwargs):
        """Create a Message instance from a JSON dictionary."""
        message_content = block_json.get("data", {}).get("content", "")
        data = block_json.get("data", {})
        attachments = []
        focus = data.get("focus")
        sources = cls.extract_sources(block_json)
        user_name= data['user']['name'] if data.get('user', {}).get('name', 'User') else "User"

        # Only include hub_id and handle based on focus mode1   
        if focus == "my_agents":
            hub_id = data.get("hub_id", None)
            if hub_id is not None:
                data["hub_id"] = hub_id
        elif focus == "selected_agent":
            handle = block_json.get("pilot", data.get("handle", None))
            if handle is not None:
                data["handle"] = [handle]
                recipient = User.add_user(name=handle, _id=handle, role=Role.ASSISTANT)
                kwargs["recipient"] = recipient

        # Process attachments
        files = data.get("files", [])
        for file_dict in files:
            name = file_dict.get("name", "")
            media_url = file_dict.get("media_url", "")
            media_type = file_dict.get("media_type", "")
            # file_path = Path(file_dict.get("url", ""))
            file_path = Path(media_url)

            # Depending on media_type, instantiate the corresponding class
            if media_type == "pdf" or media_type == "txt":
                attachment = FileContentItem(file_path=file_path)
            elif media_type == "image":
                attachment = ImageContentItem(file_path=file_path)
            elif media_type == "object":
                attachment = ObjectContent(obj_content=file_dict)
            elif media_type == "folder":
                attachment = FolderContentItem(path=file_path)
            else:
                # Default to FileContentItem for other types
                attachment = FileContentItem(file_path=file_path)

            attachments.append(attachment)

        # Process history
        history = []
        for message_dict in data.get("history", []):
            message = Message.from_block(message_dict)
            history.append(message)

        # Default event and user
        event = Event.USER_MESSAGE
        user = User.add_user(user_name, Role.USER)

        # Convert focus string to enum
        if focus == "public":
            focus = Focus.PUBLIC
        elif focus == "my_agents":
            focus = Focus.MY_AGENTS
        elif focus == "selected_agent":
            focus = Focus.SELECTED_AGENT
        elif focus == "my_space":
            focus = Focus.MY_SPACE
        else:
            focus = Focus.PUBLIC  # Default focus if not specified

        focus_value = Focus(focus)

        return cls.create(
            message=message_content,
            user=user,
            event=event,
            sources=sources,
            attachments=attachments,
            data=data,
            history=history,
            focus=focus_value,
            **kwargs,
        )
    
    @classmethod
    def extract_sources(cls, block_json):
        sources = []
        data_space = block_json.get('data', {}).get('space', {})
        if isinstance(data_space, dict):
            space_token = data_space.get('space_token')
            if space_token:
                sources.append(space_token)
        if not sources:
            user_space = block_json.get('data', {}).get('user', {}).get('space', {})
            if isinstance(user_space, dict):
                space_token = user_space.get('space_token')
                if space_token:
                    sources.append(space_token)

        return sources


    @classmethod
    def from_memory(cls, memory: dict):
        # Example memory:
        # {'id': '8936f00d-cefe-4af4-bc8f-1ddaa0fac182', 'memory': 'Likes to play cricket on weekends',
        #  'hash': '285d07801ae42054732314853e9eadd7', 'metadata': {'category': 'hobbies'}, 'score': 0.09893511,
        #  'created_at': '2024-10-13T04:04:24.526226-07:00', 'updated_at': None, 'user_id': 'session_123'}]
        # message_content = memory.get("memory", "")
        # data = memory.get("metadata", {})
        # attachments = []
        try:
            return cls(id=memory.get("id", ""), **memory.get("metadata"))
        except Exception as e:
            print(e)
            return cls()

    @classmethod
    def add_user_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="User", role=Role.USER)
        return cls.create(
            message, user, Event.USER_MESSAGE, attachments, data, kwargs=kwargs
        )

    @classmethod
    def add_notification(
        cls,
        message: str,
        user: User = None,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        if not user:
            user = User.add_user(name="System", role=Role.SYSTEM)
        return cls.create(
            message, user, Event.NOTIFICATION, attachments, data, **kwargs
        )

    @classmethod
    def add_stream(
        cls,
        message: str,
        user: User = None,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        if not user:
            user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.STREAM, attachments, data, **kwargs)

    @classmethod
    def add_question_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.QUESTION, attachments, data, **kwargs)

    @classmethod
    def add_planning_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.PLANNING, attachments, data, **kwargs)

    @classmethod
    def add_task_start_message(
        cls,
        message: str,
        user: User = None,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        if not user:
            user = User.add_user(name="System", role=Role.SYSTEM)
        return cls.create(message, user, Event.TASK_START, attachments, data, **kwargs)

    @classmethod
    def add_task_end_message(
        cls,
        message: str,
        user: User = None,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        if not user:
            user = User.add_user(name="System", role=Role.SYSTEM)
        return cls.create(message, user, Event.TASK_END, attachments, data, **kwargs)

    @classmethod
    def add_assistant_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(
            message, user, Event.AGENT_MESSAGE, attachments, data, **kwargs
        )

    @classmethod
    def add_execution_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.EXECUTION, attachments, data, **kwargs)

    @classmethod
    def add_error_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="System", role=Role.SYSTEM)
        return cls.create(
            message, user, Event.NOTIFICATION, attachments, data, **kwargs
        )

    @classmethod
    def add_reflection_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.PLANNING, attachments, data, **kwargs)

    def add_attachment(self, item: Any) -> None:
        if isinstance(item, ContentItem):
            self.attachments.append(item)
        elif isinstance(item, Exception):
            self.attachments.append(
                Content.add_content_item(str(item), ContentType.EXCEPTION)
            )
        elif isinstance(item, str):
            self.attachments.append(Content.add_content_item(item, ContentType.TEXT))
        else:
            self.attachments.append(ObjectContent.add(item))

    def __str__(self) -> str:
        # return "\n\n".join([f"{c}" for i, c in enumerate(self.attachments, 1)])
        summary = "\n\n".join(
            [f"{c.summary}" for i, c in enumerate(self.attachments, 1)]
        )
        return f"[{self.event}] - {self.sender.username}: \n{self.message}\n" + (
            "```\n" f"{summary}\n" "```" if summary else ""
        )

    def to_list(self):
        return [c for c in self.attachments]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self))

    @property
    def summary(self) -> str:
        return self.__str__()

    def generate_kwargs(self) -> dict[str, str]:
        return {
            "message": self.message,
            "data": json.dumps(self.data),
            "attachments": [c.summary for c in self.attachments],
            "event": self.event,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "files": self.attachments,
            # "files":['https://ik.imagekit.io/bethere/unpod/Screenshot_from_2025-01-07_14-41-47.png','https://media.licdn.com/dms/image/v2/D5622AQETBC9DCZJ6eQ/feedshare-shrink_800/feedshare-shrink_800/0/1725229024888?e=2147483647&v=beta&t=wXN0GhWh0fIjd2BPJIttTzy-yY3R5LdOzCNCRF3sFjc'],
            # "images":self.attachments
        }

    def to_memory(self):
        return {
            "memory": str(self),
            "ref_id": self.session_id,
            "metadata": {
                "message": self.message,
                "session_id": self.session_id,
                "data": self.data,
                "attachments": [c.summary for c in self.attachments],
                "event": self.event,
                "sender_id": self.sender.id,
                "sender": self.sender.to_dict(),
                "timestamp": self.timestamp.timestamp(),
            },
        }


class Context:
    session_id: str
    objective: str
    messages: list[Message]

    interaction: bool
    # tasks: List[Task]
    active_message: int

    def __init__(self, session_id, messages: list[Message] = None):
        if not messages:
            messages = []
        self.messages = messages
        self.tasks = []
        self.interaction = False
        self.active_message = -1
        self.session_id = session_id
        self.objective = ""

    def extend(self, context: "Context") -> None:
        if context:
            self.messages.extend(context.messages)

    def __bool__(self) -> bool:
        return len(self.messages) > 0

    def add_message(self, message: Message):
        if len(self.messages) == 0:
            self.objective = message.message
        self.messages.append(message)

    def add_user_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_user_message(message, attachments, data)
        self.add_message(message)

    def add_assistant_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_assistant_message(message, attachments, data)
        self.add_message(message)

    def add_execution_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_execution_message(message, attachments, data)
        self.add_message(message)

    def add_attachment(self, item: Any, message: str = "Empty") -> None:
        if len(self.messages) == 0:
            self.add_user_message(message)
        self.messages[self.active_message].add_attachment(item)

    def add_content(self, content: str) -> "Context":
        item = Content.add_content_item(content, ContentType.TEXT)
        self.add_attachment(item)
        return self

    def close(self, index: int) -> None:
        self.messages.pop(index - 1)

    def clear(self) -> None:
        self.messages.clear()

    def count(self) -> int:
        return len(self.messages)

    def format_numbered(self) -> str:
        return "\n\n".join([f"{i}. {c}" for i, c in enumerate(self.messages, 1)])

    def __str__(self) -> str:
        return "\n\n".join([f"{c}" for i, c in enumerate(self.messages, 1)])

    def dict(self):
        return {
            "content": self.__str__(),
            "session_id": self.session_id,
            "objective": self.objective,
            "interaction": self.interaction,
            "active_message": self.active_message,
        }

    def items(self):
        """Make Context behave like a dictionary for template rendering"""
        return self.dict().items()

    def keys(self):
        """Make Context behave like a dictionary for template rendering"""
        return self.dict().keys()

    def values(self):
        """Make Context behave like a dictionary for template rendering"""
        return self.dict().values()

    def __getitem__(self, key):
        """Make Context behave like a dictionary for template rendering"""
        if key not in self.dict():
            return None
        return self.dict()[key]

    def to_list(self):
        return [c for c in self.messages]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self.format_numbered()))

    def to_memories(self):
        return [c.to_memory() for c in self.messages]

    def summary(self, current_agent_id=None) -> str:
        return "\n\n".join(
            [
                f"{c.summary}"
                for i, c in enumerate(self.get_messages(current_agent_id), 1)
            ]
        )

    def get_messages(self, current_agent_id=None):
        msgs = []
        for message in self.messages:
            if (
                current_agent_id is None
                or message.sender.id == current_agent_id
                or message.sender.role == Role.USER or message.sender.role == Role.FUNCTION
            ):
                msgs.append(message)
        return msgs

    def get_last_user_message(self):
        for message in reversed(self.messages):
            if message.sender.role == Role.USER:
                return message
        return None

    @classmethod
    def factory(cls, session_id, messages: list[Message] = None):
        if messages is None:
            items = []
        return cls(messages)

    @classmethod
    def from_memories(cls, session_id, memories: list[dict] = None):
        if memories is None:
            memories = []
        messages = [Message.from_memory(memory) for memory in memories]
        context = cls(session_id, messages)
        last_message = context.get_last_user_message()
        context.objective = last_message.message if last_message else ""
        context.active_message = len(messages) - 1
        return context

    # def current_task(self) -> Task:
    # @property

    #     if len(self.tasks):
    #         task = self.tasks[-1]
    #         if task.status != TaskStatus.DONE:
    #             return task
