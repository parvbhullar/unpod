import os
import tempfile
from typing import Any, List, Optional

from fastapi import UploadFile
from pydantic import BaseModel

from libs.api.logger import get_logger

app_logging = get_logger("store_service")


class File(BaseModel):
    file: Optional[UploadFile] = None
    file_name: Optional[str] = ""
    file_size: Optional[int] = None
    file_extension: Optional[str] = ""
    content: Optional[Any] = None
    chunk_size: int = 500
    chunk_overlap: int = 0
    documents: List = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.file:
            self.file_name = self.file.filename
            self.file_size = self.file.size
            self.file_extension = os.path.splitext(self.file.filename)[-1].lower()

    def file_is_empty(self):
        return self.file.size < 1

    def compute_documents(self, loader_class):
        app_logging.log(f"Computing documents from file {self.file_name}")

        documents = []
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f"temp__{self.file.filename}",
        ) as tmp_file:
            tmp_file.write(self.content)
            tmp_file.flush()
            loader = loader_class(tmp_file.name)
            documents = loader.load()
            documents["metadata"].update(
                {"file_name": self.file_name, "file_size": self.file_size}
            )

        os.remove(tmp_file.name)
        self.documents = documents
