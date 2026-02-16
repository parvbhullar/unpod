from __future__ import absolute_import
from django.core.cache import cache
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
import mux_python
from mux_python.rest import ApiException

import cloudinary
from cloudinary import uploader
from cloudinary import api as cloudinary_api
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from unpod.common.exception import APIException206

from unpod.common.file import getSize

# fmt:off
class PublicMediaStorage(S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


class MuxStorageBackend(object):
    config = {
        "username": getattr(settings, "MUX_TOKEN_ID", ""),
        "password": getattr(settings, "MUX_TOKEN_SECRET", ""),
    }
    if hasattr(settings, 'SSL_CERT_PATH'):
        config.update({"ssl_ca_cert": settings.SSL_CERT_PATH})
    configuration = mux_python.Configuration(**config)
    configuration.verify_ssl = False
    uploads_api = mux_python.DirectUploadsApi(mux_python.ApiClient(configuration))
    assets_api = mux_python.AssetsApi(mux_python.ApiClient(configuration))

    def generateUpload(self):
        create_asset_request = mux_python.CreateAssetRequest(
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC], test=False)
        create_upload_request = mux_python.CreateUploadRequest(
            timeout=3600, new_asset_settings=create_asset_request, cors_origin="*", test=False)
        create_upload_response = self.uploads_api.create_direct_upload(create_upload_request)
        return create_upload_response, True

    def getUploadData(self, upload_id):
        try:
            upload_response = self.uploads_api.get_direct_upload(upload_id)
            upload_response = upload_response.to_dict().get('data')
            upload_response.pop('new_asset_settings', '')
        except ApiException as muxEx:
            # reason = muxEx.body
            return {'message': "Invalid Upload Id"}, False
        return upload_response, True

    def getPlaybackId(self, assets_id):
        create_playback_id_request = mux_python.CreatePlaybackIDRequest(policy=mux_python.PlaybackPolicy.PUBLIC)
        try:
            redis_key = f'playback-{assets_id}'
            playback_id_response = cache.get(redis_key)
            if playback_id_response:
                return playback_id_response
            playback_id_response = self.assets_api.create_asset_playback_id(assets_id, create_playback_id_request)
            playback_id_response = playback_id_response.to_dict().get('data')
            cache.set(redis_key, playback_id_response, 60 * 60 * 24 * 4)
        except ApiException as muxEx:
            return {"message": "Invalid Asset Id"}
        return playback_id_response

    def deletePlaybackId(self, assests_id, playback_id):
        playback_response = self.assets_api.delete_asset_playback_id(assests_id, playback_id)
        return playback_response

    def getAssetData(self, assets_id):
        try:
            asset_res = self.assets_api.get_asset(assets_id)
            asset_res = asset_res.to_dict().get('data')
        except ApiException as muxEx:
            return {'message': "Invalid Assests Id"}, False
        return asset_res, True

    def deleteAllPlaybackId(self, days=2):
        timeout_secs = days * 60 * 60 * 24
        count = 0
        playback_keys = cache.keys('playback-*')
        print(f"Total Keys {len(playback_keys)}")
        for key in playback_keys:
            value = cache.get(key)
            timeout_left = cache.ttl(key)
            if timeout_left < timeout_secs:
                count += 1
                if value:
                    assets_id = key.split('-')[1]
                    playback_id = value.get('id')
                    self.deletePlaybackId(assets_id, playback_id)
                cache.delete(key)
        print(f"Deleted Count {count}")
        return count

    def createAssets(self, object_url, extra={}):
        input_settings = [mux_python.InputSettings(url=object_url)]
        create_asset_request = mux_python.CreateAssetRequest(
            input=input_settings,
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
            test=False,
            **extra
        )
        create_asset_response = self.assets_api.create_asset(create_asset_request)
        return create_asset_response.to_dict().get('data')


muxBackend = MuxStorageBackend()


class CloudinaryStrorageBackend:
    config = cloudinary.config(secure=True)

    CHUNK_SIZE = 6 * 1024 * 1024  # 6MB

    def __init__(self) -> None:
        pass

    def upload_file(self, file, **options):
        print(options)
        if 'chunk_size' in options:
            cloudObject = uploader.upload_large(file, **options)
        else:
            cloudObject = uploader.upload(file, **options)
        return cloudObject

    def processFileUpload(self, file, file_type, file_size=None, upload_folder=None, url=None, access_type=None):
        if file_type not in ['image', 'video']:
            raise APIException206({"message": "Invalid File Type, Only Image & Video support"})
        options = {}
        cloudObject = None
        options.update({'invalidate': True, 'resource_type': file_type})
        if upload_folder:
            options.update({'folder': upload_folder})
        else:
            options.update({"folder": f"assests/{file_type}/"})

        if access_type:
            options.update({"type": access_type})
        if not url:
            if isinstance(file, str):
                print("upload from base64")
                size = getSize(len(file))
                if 60 <= size:
                    options.update({'chunk_size': self.CHUNK_SIZE})

            elif isinstance(file, (io.RawIOBase, io.BufferedIOBase)):
                print("upload from binary file")
                if 60 <= (file_size or 100):
                    options.update({'chunk_size': self.CHUNK_SIZE})

            elif isinstance(file, InMemoryUploadedFile):
                print(("upload video file data/type", file, type(file)))
                size = getSize(file.size)
                if 60 <= size:
                    options.update({'chunk_size': self.CHUNK_SIZE})
            else:
                print("upload from aws url", file)
                options.update({'chunk_size': self.CHUNK_SIZE})
        else:
            options.update({'chunk_size': self.CHUNK_SIZE})
        cloudObject = self.upload_file(file, **options)
        return cloudObject

    def getMediaData(self, public_id, type='upload'):
        cloudObject = cloudinary_api.resource(public_id, type=type)
        return cloudObject

    def processFetchMediaData(self, public_id, type):
        if type not in ['private', 'authenticated']:
            type = 'upload'
        return self.getMediaData(public_id, type)


cloudinaryBackend = CloudinaryStrorageBackend()


class ImageKitStrorageBackend:

    endpoint = getattr(settings, "IMAGE_KIT_ENDPOINT", "")

    def __init__(self) -> None:
        pass

    def generateURL(self, name: str):
        if name is None:
            return None
        if name == '':
            return None
        if 'private' in name:
            name = name.replace('private', '')
        if not name.startswith("/"):
            name = f"/{name}"
        return f"{self.endpoint}{name}"


imagekitBackend = ImageKitStrorageBackend()
