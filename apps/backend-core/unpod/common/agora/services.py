import os
import time
import logging
import requests

from django.conf import settings
from requests.auth import HTTPBasicAuth

from unpod.common.agora.RtcTokenBuilder007 import RtcTokenBuilder, Role_Publisher, Role_Subscriber
from unpod.common.s3 import delete_s3, get_head_object_s3, get_s3_presigned_url, read_s3
from unpod.common.string import get_random_string, split_join_comma_seprated
from unpod.common.storage_backends import muxBackend
from django.utils import timezone

logger = logging.getLogger(__name__)


class AgoraUtil(object):
    TIMEOUT = 60

    @staticmethod
    def create_live_channel(post, user):
        channel_name = f"{post.post_id}{user.id}{get_random_string('', length=8)}"
        return channel_name

    @staticmethod
    def generate_agora_token(user, channelName, role=Role_Publisher):
        appID = settings.AGORA_APP_ID
        appCertificate = settings.AGORA_AUTH_CERTIFICATE
        userAccount = user.id
        expireTimeInSeconds = 3600 * 6
        currentTimestamp = int(time.time())
        privilegeExpiredTs = currentTimestamp + expireTimeInSeconds
        token = RtcTokenBuilder.build_token_with_uid(
            appID, appCertificate, channelName, userAccount, role, privilegeExpiredTs)
        return token

    @staticmethod
    def generate_recording_token(channelName, role=Role_Publisher):
        appID = settings.AGORA_APP_ID
        appCertificate = settings.AGORA_AUTH_CERTIFICATE
        userAccount = ''
        expireTimeInSeconds = 3600 * 6
        currentTimestamp = int(time.time())
        privilegeExpiredTs = currentTimestamp + expireTimeInSeconds
        token = RtcTokenBuilder.build_token_with_uid(
            appID, appCertificate, channelName, '', Role_Publisher, privilegeExpiredTs)
        return token

    @staticmethod
    def get_url():
        url = "https://api.agora.io/v1/apps/%s/cloud_recording/" % settings.AGORA_APP_ID
        return url

    @staticmethod
    def get_header():
        headers = {'Content-type': "application/json"}
        return headers

    @staticmethod
    def get_auth():
        username = settings.AGORA_AUTH['username']
        password = settings.AGORA_AUTH['password']
        auth = HTTPBasicAuth(username, password)
        return auth

    @staticmethod
    def get_acquire_body(c_name, uid):
        acquire_body = {
            "uid": uid,
            "cname": c_name,
            "clientRequest": {
                "resourceExpiredHour": 24,
                "scene": 0
            }
        }
        return acquire_body

    @staticmethod
    def get_layout_config(c_name, uid, count, mixedVideoLayout):
        # Set up two regions for two users
        layout = {}
        if mixedVideoLayout == 0:
            layout = {
                "mixedVideoLayout": mixedVideoLayout}
        if mixedVideoLayout == 3 and count == 2:
            layoutConfig = [{"x_axis": 0.0, "y_axis": 0.0, "width": 1.0, "height": 0.5, "alpha": 0.9, "render_mode": 0},
                            {"x_axis": 0.0, "y_axis": 0.5, "width": 1.0, "height": 0.5, "alpha": 0.9, "render_mode": 0}]
            layout = {
                "mixedVideoLayout": mixedVideoLayout,
                "layoutConfig": layoutConfig
            }
        if mixedVideoLayout == 3 and count == 3:
            layoutConfig = [
                {
                    # "uid": uid,
                    "x_axis": 0.0,
                    "y_axis": 0.0,
                    "width": 1.0,
                    "height": 1.0,
                    "alpha": 1.0,
                    "render_mode": 0
                },
                {
                    "x_axis": 0.0,
                    "y_axis": 0.5,
                    "width": 0.5,
                    "height": 0.5,
                    "alpha": 1.0,
                    "render_mode": 0
                },
                {
                    "x_axis": 0.5,
                    "y_axis": 0.5,
                    "width": 0.5,
                    "height": 0.5,
                    "alpha": 1.0,
                    "render_mode": 0
                }
            ]
            layout = {
                "mixedVideoLayout": mixedVideoLayout,
                "backgroudColor": "#FF0000",
                "layoutConfig": layoutConfig
            }

        return layout

    @staticmethod
    def get_start_body(c_name, uid, token):
        AGORA_STORAGE_CONFIG = {
            "secretKey": settings.AGORA_AWS_SECRET_KEY,
            "region": settings.AGORA_AWS_REGION,
            "accessKey": settings.AGORA_AWS_ACCESS_KEY,
            "bucket": settings.AGORA_AWS_BUCKET,
            "vendor": settings.AGORA_AWS_VENDOR,
            "fileNamePrefix": [settings.AGORA_AWS_RECORDING_FOLDER, c_name]
        }
        CONFIG = AGORA_STORAGE_CONFIG
        # AGORA_STORAGE_CONFIG = AGORA_STORAGE_CONFIG.update({ 'fileNamePrefix' : ["recording", c_name]})
        print("------AGORA_STORAGE_CONFIG-----", "AGORA_STORAGE_CONFIG : ", AGORA_STORAGE_CONFIG, "CONFIG :", CONFIG)
        print("------start_body-----", "CONFIG : ", CONFIG, "other :", c_name, uid)
        start_body = {
            "uid": uid,
            "cname": c_name,
            "clientRequest": {
                "token": token,
                "storageConfig": CONFIG,
                "recordingConfig": {
                    "channelType": 0,
                    "streamTypes": 2,
                    "audioProfile": 1,
                    "videoStreamType": 0,
                    "maxIdleTime": 120,
                    "transcodingConfig": {
                        "width": 520,
                        "height": 850,
                        "fps": 30,
                        "bitrate": 600,
                        "mixedVideoLayout": 0
                    }
                },
                "recordingFileConfig": {
                    "avFileType": ["hls", "mp4"]
                }
            }
        }
        print("----end get_start_body-----", start_body)
        return start_body

    @staticmethod
    def get_update_body(c_name, uid, layout):
        update_body = {
            "uid": uid,
            "cname": c_name,
            "clientRequest": layout
        }
        return update_body

    @staticmethod
    def get_stop_body(c_name, uid):
        stop_body = {
            "uid": uid,
            "cname": c_name,
            "clientRequest": {
                "resourceExpiredHour": 24
            }
        }
        return stop_body

    @staticmethod
    def cloud_post(url, data=None, timeout=TIMEOUT):
        headers = AgoraUtil.get_header()
        auth = AgoraUtil.get_auth()
        print("cloud_post -> json data : %s" % (data))
        # print("cloud_post -> json data : %s url: %s, auth:%s headers: %s" % (data, url, auth, headers))
        try:
            response = requests.post(url, json=data, headers=headers, auth=auth, timeout=timeout, verify=False)
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
        headers = AgoraUtil.get_header()
        auth = AgoraUtil.get_auth()
        try:
            response = requests.get(url, headers=headers, auth=auth, timeout=timeout, verify=False)
            print("url: %s,request:%s response: %s" % (url, response.request.body, response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")

    @staticmethod
    def start_record(c_name, uid):
        try:
            uid = str(uid)
            c_name = str(c_name)
            print("uid", uid, "c_name", c_name)
            token = AgoraUtil.generate_recording_token(c_name)
            acquire_url = AgoraUtil.get_url() + "acquire"
            print("-----go to Acquire----------")
            r_acquire = AgoraUtil.cloud_post(acquire_url, AgoraUtil.get_acquire_body(c_name, uid))
            if r_acquire.status_code == 200:
                print("Acquire success! Code: %s Info: %s" % (r_acquire.status_code, r_acquire.json()))
                resourceId = r_acquire.json()["resourceId"]
            else:
                print("Acquire error! Code: %s Info: %s" % (r_acquire.status_code, r_acquire.json()))
                return False
            print("-------go to Start Recording---------")
            start_url = AgoraUtil.get_url() + "resourceid/%s/mode/mix/start" % resourceId
            r_start = AgoraUtil.cloud_post(start_url, AgoraUtil.get_start_body(c_name, uid, token))
            if r_start.status_code == 200:
                sid = r_start.json()["sid"]
                print("Start Recording! Code:%s Info:%s" % (r_start.status_code, r_start.json()))
            else:
                print("Start error! Code:%s Info:%s" % (r_start.status_code, r_start.json()))
                return False

            return {"resource_id": resourceId, 'sid': sid}
        except Exception as ex:
            print("start_record failed", str(ex))
            raise ex

    @staticmethod
    def get_started_recording(resourceId, sid):
        query_url = AgoraUtil.get_url() + "resourceid/%s/sid/%s/mode/mix/query" % (resourceId, sid)
        r_query = AgoraUtil.cloud_get(query_url)
        if r_query.status_code == 200:
            print("The recording status: %s" % r_query.json())
        else:
            print("Query failed. Code %s, info: %s" % (r_query.status_code, r_query.json()))
        return r_query.json()

    @staticmethod
    def update_layout_after_started_recording(c_name, uid, resourceId, sid, count):
        uid = str(uid)
        c_name = str(c_name)
        update_url = AgoraUtil.get_url() + "resourceid/%s/sid/%s/mode/mix/updateLayout" % (resourceId, sid)
        mixedVideoLayout = 0
        if count and count > 0:
            # count = len(collaborators)
            if count == 1:
                layout = AgoraUtil.get_layout_config(c_name, uid, count, mixedVideoLayout)
            if count == 2:
                mixedVideoLayout = 3
                layout = AgoraUtil.get_layout_config(c_name, uid, count, mixedVideoLayout)
            if count == 3:
                mixedVideoLayout = 3
                layout = AgoraUtil.get_layout_config(c_name, uid, count, mixedVideoLayout)
            if count >= 4:
                layout = AgoraUtil.get_layout_config(c_name, uid, count, mixedVideoLayout)
        else:
            layout = AgoraUtil.get_layout_config(c_name, uid, count, mixedVideoLayout)

        r_update = AgoraUtil.cloud_post(update_url, AgoraUtil.get_update_body(c_name, uid, layout))
        if r_update.status_code == 200:
            print("Update layout success.")
        else:
            print("Update layout failed. Code: %s Info: %s" % r_update.status_code, r_update.json())

        return r_update.json()

    @staticmethod
    def stop_recording(c_name, uid, resourceId, sid):
        uid = str(uid)
        c_name = str(c_name)
        stop_url = AgoraUtil.get_url() + "resourceid/%s/sid/%s/mode/mix/stop" % (resourceId, sid)
        r_stop = AgoraUtil.cloud_post(stop_url, AgoraUtil.get_stop_body(c_name, uid))
        if r_stop.status_code == 200:
            print("Stop cloud recording success. FileList : %s, uploading status: %s"
                  % (r_stop.json()["serverResponse"]["fileList"], r_stop.json()["serverResponse"]["uploadingStatus"]))
        else:
            print(f"Stop failed! Code: {r_stop.status_code}", r_stop.json())

        return r_stop

    @staticmethod
    def start_live_recording(recordingObj):
        try:
            response = AgoraUtil.start_record(recordingObj.session.channel_name, recordingObj.id)
            if response and 'sid' in response:
                recordingObj.agora_resource_id = response['resource_id']
                recordingObj.agora_sid = response['sid']
                recordingObj.agora_sids = split_join_comma_seprated(recordingObj.agora_sids, recordingObj.agora_sid)
                recordingObj.save()
                return recordingObj, True
        except Exception as ex:
            print("start_live_recording failed", str(ex))
            return ex, False

    @staticmethod
    def check_live_recording(recordingObj):
        try:
            response = AgoraUtil.get_started_recording(recordingObj.agora_resource_id, recordingObj.agora_sid)
            if response and 'serverResponse' in response:
                recordingObj.recording_status = True
                recordingObj.save()
                return recordingObj, True
            return response, False
        except Exception as ex:
            print("check_live_recording failed", str(ex))
            recordingObj.recording_reponse = response
            recordingObj.save()
            return recordingObj, False

    @staticmethod
    def stop_live_recording(recordingObj):
        try:
            response = None
            logger.info("stopping started")
            response = AgoraUtil.stop_recording(recordingObj.session.channel_name, recordingObj.id,
                                                recordingObj.agora_resource_id, recordingObj.agora_sid)
            if response.status_code == 200:
                resp_json = response.json()
                recordingObj.recording_reponse = resp_json
                recordingObj.recording_status = False
                if 'serverResponse' in resp_json:
                    if resp_json["serverResponse"]["fileList"]:
                        fileList = resp_json["serverResponse"]["fileList"]
                        recordingObj.agora_recording_files = fileList
                        recordingObj.save()
                        return recordingObj, True
            try:
                resp_json = response.json()
            except:
                resp_json = {}
            recordingObj.recording_reponse = resp_json
            recordingObj.recording_status = False
            recordingObj.save()
            return recordingObj, False
        except Exception as ex:
            logger.info("stop_live_recording failed on response", str(ex))
            print("stop_live_recording failed", str(ex))
            return ex, False

    @staticmethod
    def update_layout_live_recording(activityObj, count):
        try:
            response = AgoraUtil.update_layout_after_started_recording(
                activityObj.channel_name, activityObj.id, activityObj.agora_resource_id, activityObj.agora_sid, count)
            return response
        except Exception as ex:
            print("update_layout_live_recording failed", str(ex))
            return ex

    @staticmethod
    def get_live_recording(activityObj):
        try:
            response = AgoraUtil.get_started_recording(activityObj.agora_resource_id, activityObj.agora_sid)
            return response
        except Exception as ex:
            print("update_layout_live_recording failed", str(ex))
            return ex

    @staticmethod
    def delete_recording_video(recording_file):
        folder_name = os.path.dirname(recording_file['fileName'])
        all_files = AgoraUtil.get_related_files(recording_file['fileName'])
        for file in all_files:
            file_key = folder_name + '/' + file
            delete_s3(settings.AGORA_AWS_BUCKET, file_key)
        delete_s3(settings.AGORA_AWS_BUCKET, recording_file['fileName'])

    @staticmethod
    def download_recording_video(channel_name, file_name):
        pass

    @staticmethod
    def upload_recording_videos(recordingObj):
        uploadRes = {}
        for fileName, file in recordingObj.aws_recording_files.items():
            uploadRes[fileName] = uploadRes.get(fileName, {})
            # current = timezone.now()
            # time_name = f"{current.strftime('%Y%m%d_%H%M%S')}"
            # upload_name = f"{recordingObj.session.channel_name}-{time_name}-Meeting-Recording.mp4"
            upload_url, status = get_s3_presigned_url(settings.AGORA_AWS_BUCKET, fileName)
            fileuploadRes = muxBackend.createAssets(upload_url, extra={'mp4_support': 'standard'})
            print(fileuploadRes, 'fileuploadRes')
            uploadRes[fileName] = fileuploadRes

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
            head_res, status = get_head_object_s3(settings.AGORA_AWS_BUCKET, fileName)
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
        file_to_delete = []
        for file in recordingObj.agora_recording_files:
            if file['fileName'].endswith(".mp4"):
                recordingObj.aws_recording_files[file['fileName']] = {**recordingObj.aws_recording_files.get(file['fileName'], {}), **file}
            elif file['fileName'].endswith(".m3u8"):
                file_to_delete.append(file)
        for file in file_to_delete:
            AgoraUtil.delete_recording_video(file)
        recordingObj.recording_video_status = 'removed'
        recordingObj.save()
        if upload:
            recordingObj = AgoraUtil.upload_recording_videos(recordingObj)
        return recordingObj

    @staticmethod
    def get_related_files(target_url, ext='.ts'):
        """
        Get all the files from the target_url
        :param target_url: string
        :return: list
        """
        target_url_data, status = read_s3(settings.AGORA_AWS_BUCKET, target_url)
        all_src_file = target_url_data.decode().split('\n') if status else []
        stream_files = []
        for file in all_src_file:
            if file.endswith(ext):
                stream_files.append(file)
        return stream_files
