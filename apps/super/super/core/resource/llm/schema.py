import enum
import json
from functools import wraps
from sre_parse import ANY
from typing import List, Union, Callable, Any, Optional
from pydantic import field_validator, ConfigDict, BaseModel, Field, SecretStr
from pydantic.v1 import validate_arguments


class MessageRole(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class MessageContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE_URL = "image_url"
    PDF = "pdf"


class MessageImage(BaseModel):
    url: str
    alt_text: str


class MessageFile(BaseModel):
    url: str
    alt_text: str


class MessageContent(BaseModel):
    type: MessageContentType = MessageContentType.TEXT
    text: Optional[str] = None

    def add_text(self, text: str):
        self.text = text

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        final_data = {}
        for key in d.keys():
            if d[key] is not None and d[key]:
                final_data[key] = d[key]
        if final_data.get("type") in [MessageContentType.IMAGE_URL]:
            del final_data["text"]
        return final_data


class MessageImages(BaseModel):
    type: MessageContentType = MessageContentType.IMAGE_URL
    image_url: Optional[Any] = None

    def add_image(self, url: str, alt_text: str = ""):
        self.image_url = MessageImage(url=url, alt_text=alt_text)


class MessageFile(BaseModel):
    type: MessageContentType = MessageContentType.PDF
    pdf_data: Optional[str] = None

    # def add_image(self, url: str, alt_text: str = ""):
    #     self.image_url = MessageImage(url=url, alt_text=alt_text)

    def add_file(self, content: str):
        self.pdf_data = content

    # def dict(self, *args, **kwargs):
    #     d = super().dict(*args, **kwargs)
    #     final_data = {}
    #     for key in d.keys():
    #         if d[key] is not None and d[key]:
    #             final_data[key] = d[key]
    #     if final_data.get("type") in [MessageContentType.IMAGE_URL]:
    #         del final_data["text"]
    #     return final_data


class LanguageModelMessage(BaseModel):
    role: MessageRole
    content: Union[str, List[MessageContent], Any] = None

    # content_list: List[MessageContent] = Field(default_factory=list)

    def add_text(self, text: str):
        # Ensure that content is a list before appending
        if self.content is None or isinstance(self.content, str):
            self.content = []  # Reset content to be a list
        # Append a new MessageContent instance
        # print("Adding TEXT", text)
        self.content.append(MessageContent(type=MessageContentType.TEXT, text=text))

    def add_image(self, url: str, alt_text: str):
        # Ensure that content is a list before appending
        if self.content is None or isinstance(self.content, str):
            self.content = []  # Reset content to be a list

        # print("Adding url", url)
        message = MessageImages()
        message.add_image(url, alt_text)
        self.content.append(message)

    def add_file(self, content: str):
        # Ensure that content is a list before appending
        if self.content is None or isinstance(self.content, str):
            self.content = []  # Reset content to be a list

        # print("Adding url", url)
        message = MessageFile()
        message.add_file(content)
        self.content.append(message)

    def to_dict(self):
        return self.dict()

    def __str__(self):
        if self.content is None:
            return "No Content \n" + self.role.value
        if isinstance(self.content, str):
            return (self.content or "") + "\n" + self.role.value
        content = "\n".join([str(c.type) for c in self.content])
        return content + "\n" + self.role.value


class LanguageModelFunction(BaseModel):
    json_schema: dict

    def to_dict(self):
        return self.json_schema

    def __str__(self):
        return json.dumps(self.json_schema, indent=2)


class LanguageModelClassification(str, enum.Enum):
    """The LanguageModelClassification is a functional description of the model.

    This is used to determine what kind of model to use for a given prompt.
    Sometimes we prefer a faster or cheaper model to accomplish a task when
    possible.

    """

    FAST_MODEL: str = "fast_model"
    SMART_MODEL: str = "smart_model"


class LanguageModelPrompt(BaseModel):
    messages: List[LanguageModelMessage]
    functions: List[LanguageModelFunction] = Field(default_factory=list)
    function_call: Union[LanguageModelFunction, None] = None

    def get_messages(self):
        return [m.to_dict() for m in self.messages]

    def get_functions(self):
        return [f.to_dict() for f in self.functions]

    def get_function_call(self):
        if self.function_call is None:
            return None
        return self.function_call.json_schema or "auto"

    def get_system_prompt(self):
        return "\n".join(
            [m.content for m in self.messages if m.role == MessageRole.SYSTEM]
        )

    def get_user_prompt(self):
        return "\n".join(
            [m.content for m in self.messages if m.role == MessageRole.USER]
        )

    def __str__(self):
        return "\n\n".join([f"{m.role.value}: {m.content}" for m in self.messages])
        # + "\n\nFunctions:" + "\n\n".join([f"{f.json_schema}" for f in self.functions])

    def get_context(self):
        return self.__str__()


## Function Calls ##
####################
def _remove_a_key(d, remove_key) -> None:
    """Remove a key from a dictionary recursively"""
    if isinstance(d, dict):
        for key in list(d.keys()):
            if key == remove_key:
                del d[key]
            else:
                _remove_a_key(d[key], remove_key)


class schema_function:
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.validate_func = validate_arguments(func)
        parameters = self.validate_func.model.schema()
        parameters["properties"] = {
            k: v
            for k, v in parameters["properties"].items()
            if k not in ("v__duplicate_kwargs", "args", "kwargs")
        }
        parameters["required"] = sorted(
            parameters["properties"]
        )  # bug workaround see lc
        _remove_a_key(parameters, "title")
        _remove_a_key(parameters, "additionalProperties")
        self.openai_schema = {
            "name": self.func.__name__,
            "description": self.func.__doc__,
            "parameters": parameters,
        }
        self.model = self.validate_func.model

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        @wraps(self.func)
        def wrapper(*args, **kwargs):
            return self.validate_func(*args, **kwargs)

        return wrapper(*args, **kwargs)

    def from_response(self, completion, throw_error=True):
        """Execute the function from the response of an openai chat completion"""
        message = completion.choices[0].message
        if throw_error:
            assert "function_call" in message, "No function call detected"
            assert (
                message["function_call"]["name"] == self.openai_schema["name"]
            ), "Function name does not match"

        function_call = message["function_call"]
        arguments = json.loads(function_call["arguments"])
        return self.validate_func(**arguments)


class SchemaModel(BaseModel):
    @classmethod
    def _resolve_ref(cls, ref, definitions):
        # Extract the key from the reference string and return the corresponding definition
        ref_key = ref.split("/")[-1]
        return definitions.get(ref_key)

    @classmethod
    def function_schema(cls, arguments_format=False) -> dict:
        schema = cls.schema()
        definitions = schema.get("definitions", {})

        # Process the properties to replace $ref with actual definitions
        properties = schema.get("properties", {})
        cls.set_properties(definitions, properties)

        # Prepare the final parameters excluding certain keys
        parameters = {
            k: v for k, v in schema.items() if k not in ("title", "description")
        }
        parameters["properties"] = properties
        parameters["required"] = sorted(parameters.get("properties", {}))
        # parameters["definitions"] = definitions
        _remove_a_key(parameters, "title")
        if arguments_format:
            name = schema["title"]
            # parameters.pop("required", None)
            # parameters.pop("definitions", None)
            multiple_args = cls.multiple_args()
            if multiple_args:
                return parameters
            return {
                cls.name(): parameters,
                # "description": schema["description"],
            }
        return {
            "name": schema["title"],
            "description": schema["description"],
            "parameters": parameters,
        }

    @classmethod
    def set_properties(cls, definitions, properties):
        for prop, details in properties.items():
            if (
                "allOf" in details
                and len(details["allOf"]) == 1
                and "$ref" in details["allOf"][0]
            ):
                ref = details["allOf"][0]["$ref"]
                resolved_ref = cls._resolve_ref(ref, definitions)
                if resolved_ref:
                    properties[prop] = resolved_ref
                    if resolved_ref.get("type") == "object":
                        cls.set_properties(
                            definitions, resolved_ref.get("properties", {})
                        )
            if "type" in details:
                if (
                    details["type"] == "array"
                    and "items" in details
                    and "$ref" in details["items"]
                ):
                    ref = details["items"]["$ref"]
                    resolved_ref = cls._resolve_ref(ref, definitions)
                    if resolved_ref:
                        properties[prop]["items"] = resolved_ref
                        if resolved_ref.get("type") == "object":
                            cls.set_properties(
                                definitions, resolved_ref.get("properties", {})
                            )
        return properties

    @classmethod
    def name(cls) -> str:
        schema = cls.schema()
        return schema["title"]

    @classmethod
    def multiple_args(cls) -> bool:
        return False

    @classmethod
    def from_response(cls, completion, throw_error=True):
        message = completion.choices[0].message

        if throw_error:
            assert "function_call" in message, "No function call detected"
            assert (
                message["function_call"]["name"] == cls.function_schema()["name"]
            ), "Function name does not match"

        function_call = message["function_call"]
        arguments = json.loads(function_call["arguments"])
        return cls(**arguments)
