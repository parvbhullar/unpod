import os
import hashlib
import mimetypes
from fastapi import UploadFile
from libs.api.logger import get_logger

app_logging = get_logger("store_service")


def getFileExtension(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension


def getMimeType(file_name):
    mime_type = mimetypes.MimeTypes().guess_type(file_name)[0]
    if mime_type is None:
        file_name, file_extension = os.path.splitext(file_name)
        mime_type = mimetypes.types_map.get(file_extension)
    return mime_type


def compute_sha1_from_file(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
        return compute_sha1_from_content(content)


def compute_sha1_from_content(content):
    return hashlib.sha1(content).hexdigest()


def fileToUploadFile(filename, fileObj=None, **kwargs):
    if fileObj is None:
        fileObj = open(filename, "rb")
        fileObj = fileObj.read()
    if not kwargs.get("size"):
        kwargs["size"] = len(fileObj)
    return UploadFile(filename=filename, file=fileObj, **kwargs)


def toFile(file: UploadFile):
    from services.store_service.core.parsers.file import File

    app_logging.debug("toFile", file.filename)
    return File(
        file=file,
        file_name=file.filename,
        file_size=file.size,
        file_extension=getFileExtension(file.filename),
        content=file.file,
    )
