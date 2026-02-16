import logging
import time

import jwt
import uuid
import datetime
import requests

from django.conf import settings

from unpod.common.s3 import get_s3_presigned_url, get_head_object_s3
from unpod.common.storage_backends import muxBackend
from unpod.common.string import get_random_string

logger = logging.getLogger(__name__)


class HMS:

    base_url = "https://api.100ms.live/v2"
    TIMEOUT = 60

    @staticmethod
    def get_menagement_token():
        app_access_key = settings.HMS['app_access_key']
        app_secret = settings.HMS['app_secret']
        expires = 24 * 3600
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=expires)
        return jwt.encode(payload={
            'access_key': app_access_key,
            'type': 'management',
            'version': 2,
            'jti': str(uuid.uuid4()),
            'iat': now,
            'exp': exp,
            'nbf': now
        }, key=app_secret).decode()

    def create_room(self, channel_name):
        try:
            endpoint = f"{self.base_url}/rooms"
            data = {
                "name": channel_name,
                "recording_info": {
                    "enabled": True,
                    "upload_info": {
                        "type": "s3",
                        "location": settings.HMS_S3_BUCKET,
                        "prefix": "/".join([settings.HMS_AWS_RECORDING_FOLDER, channel_name]),
                        "options": {
                            "region": settings.HMS_S3_REGION,
                        },
                        "credentials": {
                            "key": settings.HMS_AWS_ACCESS_KEY,
                            "secret":  settings.HMS_AWS_SECRET_KEY
                        }
                    }
                }
            }
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Create Room Failed", str(ex))
            return ex, False
        
    def get_room(self, room_id):
        try:
            endpoint = f"{self.base_url}/rooms/{room_id}"
            response = HMS.cloud_get(endpoint)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Disable Room Failed", str(ex))
            return ex, False

    def disable_room(self, room_id):
        try:
            endpoint = f"{self.base_url}/rooms/{room_id}"
            data = {"enabled": False}
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Disable Room Failed", str(ex))
            return ex, False

    def create_room_codes(self, room_id):
        try:
            endpoint = f"{self.base_url}/room-codes/room/{room_id}"
            data = {}
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Create Room Codes Failed", str(ex))
            return ex, False

    def create_room_code_for_role(self, room_id, role):
        try:
            endpoint = f"{self.base_url}/room-codes/room/{room_id}/role/{role}"
            data = {}
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Create Room Codes Failed", str(ex))
            return ex, False

    @staticmethod
    def start_recording(room_id):
        try:
            endpoint = f"{HMS.base_url}/recordings/room/{room_id}/start"
            data = {}
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return None, False
        except Exception as ex:
            print("Start Recording Failed", str(ex))
            return ex, False

    @staticmethod
    def stop_recording(room_id):
        try:
            endpoint = f"{HMS.base_url}/recordings/room/{room_id}/stop"
            data = {}
            response = HMS.cloud_post(endpoint, data)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return response, False
        except Exception as ex:
            print("Stop Recording Failed", str(ex))
            return ex, False

    @staticmethod
    def get_recordings(recording_id):
        try:
            endpoint = f"{HMS.base_url}/recordings/{recording_id}"
            response = HMS.cloud_get(endpoint)
            if response.status_code == 200:
                print(response.json())
                return response.json(), True
            return response.json(), False
        except Exception as ex:
            print("get_recording", str(ex))
            return ex, False


    @staticmethod
    def start_live_recording(recordingObj):
        try:
            response = HMS.start_recording(recordingObj.session.hms_room_id)
            if response:
                recordingObj.recording_reponse = response
                recordingObj.recording_status = True
                recordingObj.save()
                return recordingObj, True
            return None, False
        except Exception as ex:
            print("start_live_recording failed", str(ex))
            return ex, False

    @staticmethod
    def stop_live_recording(recordingObj):
        try:
            response = HMS.stop_recording(recordingObj.session.hms_room_id)
            if response:
                recordingObj.agora_recording_files = response
                recordingObj.recording_status = False
                recordingObj.save()
                return recordingObj, True
            try:
                resp_json = response.json()
            except:
                resp_json = {}
            recordingObj.agora_recording_files = resp_json
            recordingObj.recording_status = False
            recordingObj.save()
            return recordingObj, False
        except Exception as ex:
            logger.info("stop_live_recording failed on response", str(ex))
            print("stop_live_recording failed", str(ex))
            return ex, False

    @staticmethod
    def get_recording_s3_url(recording_id):
        try:
            response, status = HMS.get_recordings(recording_id)
            if status:
                retry = 0
                while response.get('recording_assets') is None and retry < 4:
                    time.sleep(5)
                    response, status = HMS.get_recordings(recording_id)
                    retry += 1
                for asset in response.get('recording_assets', []):
                    if asset['type'] == 'room-composite':
                        return asset['path'], response
                print('room-composite not found')
            return None, None
        except Exception as e:
            print('get_recording_s3_url failed', str(e))
            return None, None

    @staticmethod
    def upload_recording_videos(recordingObj):
        uploadRes = {}
        for s3url in recordingObj.aws_recording_files.keys():
            uploadRes[s3url] = uploadRes.get(s3url, {})
            # current = timezone.now()
            # time_name = f"{current.strftime('%Y%m%d_%H%M%S')}"
            # upload_name = f"{recordingObj.session.channel_name}-{time_name}-Meeting-Recording.mp4"
            upload_url, status = get_s3_presigned_url(settings.HMS_S3_BUCKET, None, s3url)
            fileuploadRes = muxBackend.createAssets(upload_url, extra={'mp4_support': 'standard'})
            print(fileuploadRes, 'fileuploadRes')
            uploadRes[s3url] = fileuploadRes

        for fileName, fileRes in uploadRes.items():
            retry = 0
            while fileRes['status'] != 'ready' and retry < 4:
                time.sleep(2)
                fileRes, status = muxBackend.getAssetData(fileRes['id'])
                print('fileRes\n', fileRes, '\n retry---> ', retry)
                retry += 1
            fileRes = {
                'id': fileRes['id'], 'status': fileRes['status'],
                'mp4_support': fileRes['mp4_support'],
                'playback_ids': fileRes['playback_ids']
            }
            head_res, status = get_head_object_s3(settings.HMS_S3_BUCKET, None, fileName)
            if status:
                head_res.pop('ResponseMetadata', None)
                head_res.pop('LastModified', None)
                fileRes['size'] = head_res['ContentLength']
                fileRes['awsRes'] = head_res
                recordingObj.aws_recording_files[fileName]['muxRes'] = fileRes
        recordingObj.recording_video_status = 'uploaded'
        recordingObj.save()
        return recordingObj

    @staticmethod
    def generate_recording_videos(recordingObj, model, upload=False):
        model.objects.filter(id=recordingObj.id).update(recording_video_status='processing')
        if recordingObj.agora_recording_files:
            recording_id = recordingObj.agora_recording_files[0].get('data', [{}])[0].get('id')
            if recording_id:
                s3_url, response = HMS.get_recording_s3_url(recording_id)
                if s3_url:
                    recordingObj.aws_recording_files[s3_url] = {**response}
        recordingObj.save()
        if upload:
            recordingObj = HMS.upload_recording_videos(recordingObj)
        return recordingObj

    @staticmethod
    def create_live_channel(post, user):
        channel_name = f"{post.post_id}{user.id}{get_random_string('', length=8)}"
        return channel_name

    @staticmethod
    def get_header():
        management_token = HMS.get_menagement_token()
        headers = {
            'Content-type': "application/json",
            'Authorization': f"Bearer {management_token}"
        }
        return headers

    @staticmethod
    def cloud_post(url, data=None, timeout=TIMEOUT):
        headers = HMS.get_header()
        print("cloud_post -> json data : %s" % (data))
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout, verify=False)
            print("url: %s, request body:%s response: %s" % (url, response.request.body, response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")
        except Exception as ex:
            print("cloud_post failed", str(ex), url)
            raise ex

    @staticmethod
    def cloud_get(url, timeout=TIMEOUT):
        headers = HMS.get_header()
        try:
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            print("url: %s,request:%s response: %s" % (url, response.request.body, response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")
