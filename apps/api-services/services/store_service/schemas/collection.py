import enum
import os
import mimetypes
import tempfile
from typing import Any, Dict, Optional, Union, List, Literal
from pydantic import BaseModel, Field, PrivateAttr, model_validator

from services.store_service.core.file import compute_sha1_from_file
from libs.api.logger import get_logger
from libs.storage.s3 import read_file

app_logging = get_logger("store_service")


class CollectionTypes(str, enum.Enum):
    video = "video"
    audio = "audio"
    doc = "doc"
    image = "image"
    text = "text"
    collection = "collection"
    table = "table"
    document = "document"
    webpage = "webpage"
    email = "email"
    contact = "contact"
    evals = "evals"


class CollectionModelConfig(BaseModel):
    name: str
    desc: str
    collection_type: CollectionTypes
    org_id: Union[int, str]
    token: str


class FieldSchema(BaseModel):
    title: str
    type: str
    description: str
    required: bool = Field(default=False)
    default: Any = Field("")
    index: bool = Field(default=False)
    primary: bool = Field(default=False)


class CollectionModelSchema(BaseModel):
    collection_id: Union[int, str]
    org_id: Union[int, str]
    token: str
    fields: Dict = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    schemas: Optional[Dict] = Field(default_factory=dict)


class CollectionStoreConfig(CollectionModelConfig):
    fields: Dict[str, FieldSchema] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    schemas: Optional[Dict] = Field(default_factory=dict)


class CollectionStoreConfigUpdate(BaseModel):
    name: Optional[str] = None
    desc: Optional[str] = None
    collection_type: Optional[CollectionTypes] = None
    fields: Optional[Dict[str, FieldSchema]] = None
    keywords: Optional[List[str]] = None
    schemas: Optional[Dict] = Field(default_factory=dict)


class CollectionFileLogSchema(BaseModel):
    name: str
    size: int
    file_sha1: str
    collection_id: Union[int, str]


class CollectionFile(BaseModel):
    url: str
    name: Optional[str] = None
    size: Optional[int] = Field(default=None, ge=0)
    media_type: Optional[str] = None
    file_sha1: Optional[str] = None

    _content: Optional[bytes] = PrivateAttr(default_factory=bytes)
    _metadata: Optional[Dict] = PrivateAttr(default_factory=dict)

    config: Optional[Dict] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def validate(self, data):
        if not data.get("url"):
            raise ValueError("URL is required")
        if not data.get("name"):
            data["name"] = os.path.basename(data.get("url"))
        return data

    def load(cls, **kwargs):
        if cls._content and cls._content is not None:
            return cls._content
        cls._metadata["headers"] = {}
        url = str(cls.url)
        if "s3" in url:
            data = read_file(None, None, url)
            cls._content = data
            if cls.size is None:
                cls.size = len(data)
            return data
        if "file://" in url:
            url = url.replace("file://", "")
        if os.path.exists(url):
            with open(url, "rb") as f:
                data = f.read()
                cls._content = data
                if cls.size is None:
                    cls.size = len(data)
            return data
        return None

    def get_content(cls, **kwargs):
        return cls.load(**kwargs)

    def get_content_type(cls, **kwargs):
        file_extension = os.path.splitext(cls.name)[1]
        return mimetypes.types_map.get(file_extension)

    def check_file(self, collection_id=None):
        """
        Check if file exists
        """
        self.compute_file_sha1()
        if collection_id:  # if collection id is provided
            return self.file_already_exists({"collection_id": collection_id})
        return self.file_already_exists()

    def compute_file_sha1(self):
        """
        Compute the sha1 of the file using a temporary file
        """
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=self.name,
        ) as tmp_file:
            tmp_file.write(self._content)
            tmp_file.flush()
            self.file_sha1 = compute_sha1_from_file(tmp_file.name)

        os.remove(tmp_file.name)

    def file_already_exists(self, query: Dict = {}):
        from services.store_service.models.collection import CollectionFileLogModel

        """
        Check if file already exists in vectors table
        """
        if not self.file_sha1:
            self.compute_file_sha1()
        query = {**query, "file_sha1": self.file_sha1}
        app_logging.debug("query", query)
        check = CollectionFileLogModel.find_one(**query)
        return True if check else False

    def save_file_log(self, collection_id):
        from services.store_service.models.collection import CollectionFileLogModel

        data = {
            "name": self.name,
            "size": self.size,
            "file_sha1": self.file_sha1,
            "collection_id": collection_id,
        }
        CollectionFileLogModel.save_single_to_db(data)


class BulkDataUpdate(BaseModel):
    labels: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str] = None


class BulkUpdateItem(BaseModel):
    document_id: str
    action: Literal["edit", "index"]
    data: BulkDataUpdate = Field(default_factory=BulkDataUpdate)
    suggested_actions: Optional[List[str]] = None
