import os
import mimetypes
from unpod.common.enum import MediaType, SizeUnit
from django.conf import settings


def getFileExtension(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension


def getFileType(file_name, mime=False):
    mime_type = mimetypes.MimeTypes().guess_type(file_name)[0]
    if mime_type is None:
        file_name, file_extension = os.path.splitext(file_name)
        mime_type = mimetypes.types_map.get(file_extension)
    if mime:
        return mime_type
    if mime_type is None:
        return MediaType.file.name
    if 'image' in mime_type:
        return MediaType.image.name
    elif 'video' in mime_type:
        return MediaType.video.name
    elif 'audio' in mime_type:
        return MediaType.audio.name
    elif 'json' in mime_type:
        return MediaType.json.name
    elif 'pdf' in mime_type:
        return MediaType.pdf.name
    elif 'excel' in mime_type:
        return MediaType.excel.name
    elif 'Word' in mime_type:
        return MediaType.Word.name
    elif 'markdown' in mime_type:
        return MediaType.markdown.name
    elif 'text' in mime_type:
        return MediaType.text.name
    elif 'powerpoint' in mime_type:
        return MediaType.powerpoint.name
    else:
        return MediaType.file.name


def getS3FileURL(file_name, upload_to):
    return f"{settings.AWS_S3_CUSTOM_DOMAIN}/{settings.AWS_PRIVATE_MEDIA_LOCATION}/{upload_to}/{file_name}"


def getS3FileURLFromURL(s3_url):
    return s3_url.split("?")[0]


def convertSizeUnit(size_in_bytes, unit):
    """ Convert the size from bytes to other units like KB, MB or GB"""
    if unit == SizeUnit.KB:
        return size_in_bytes / 1024
    elif unit == SizeUnit.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == SizeUnit.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def getSize(size, size_unit=SizeUnit.MB):
    return convertSizeUnit(size, size_unit)


def get_file_size(file_name, size_unit=SizeUnit.MB):
    """ Get file in size in given unit like KB, MB or GB"""
    size = os.path.getsize(file_name)
    return convertSizeUnit(size, size_unit)
