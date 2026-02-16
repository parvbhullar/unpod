import os
import boto3
from django.conf import settings
from botocore.client import Config
from unpod.common.s3_url import s3_path_split

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_REGION_NAME = settings.AWS_S3_REGION_NAME

DEFAULT_BUCKET = "unpod"

media_location = f"{os.getcwd()}/unpod/media/"


def delete_file(file_name):
    try:
        os.remove(file_name)
    except:
        try:
            file_path = f"{os.getcwd()}/{file_name}"
            os.remove(file_path)
        except:
            pass
    return True


def get_s3_client():
    if getattr(settings, "s3_client", None):
        return settings.s3_client
    s3_client = boto3.client(
        "s3",
        region_name=AWS_S3_REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )
    settings.s3_client = s3_client
    return s3_client


def upload_s3(bucket, data, file_name, save_local=False, **kwargs):
    s3_client = get_s3_client()
    file_url = f"https://{bucket}.s3.amazonaws.com/" + file_name
    try:
        if save_local:
            if not os.path.exists(media_location):
                os.mkdir(media_location)
            file_location = media_location + file_name
            with open(file_location, "w") as fileObj:
                fileObj.write(data)
                fileObj.close()
            return file_name, True
        s3_res = s3_client.put_object(Bucket=bucket, Body=data, Key=file_name, **kwargs)
        return file_url, True
    except Exception as ex:
        return "error in file upload to s3" + str(ex), False


def upload_zip(zip_name, zip_location, bucket):
    try:
        s3_client = get_s3_client()
        file_url = f"https://{bucket}.s3.amazonaws.com/" + zip_name
        s3_client.upload_file(zip_location, bucket, zip_name)
        return file_url, True
    except Exception as ex:
        print(ex)
        return "error in file upload_zip to s3" + str(ex), False


def read_s3(bucket_name, key, s3_url=None, from_local=False):
    try:
        if from_local:
            file_location = media_location + key
            return open(file_location).read(), True
        s3_client = get_s3_client()
        if s3_url:
            bucket_name, key = s3_path_split(s3_url)
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=key)
        body = s3_object["Body"]
        return body.read(), True
    except Exception as ex:
        print("error in file read from s3" + str(ex))
        return "error in file read from s3" + str(ex), False


def get_s3_presigned_url(bucket_name, key, s3_url=None):
    try:
        s3_client = get_s3_client()
        if s3_url:
            bucket_name, key = s3_path_split(s3_url)
        s3_params = {"Bucket": bucket_name, "Key": key}
        s3_expire = settings.AWS_EXPIRE_TIME
        s3_url = s3_client.generate_presigned_url(
            "get_object", Params=s3_params, ExpiresIn=s3_expire
        )
        return s3_url, True
    except Exception as ex:
        return "error in file read from s3" + str(ex), False


def generate_presigned_url_s3(s3_url):
    if not s3_url:
        return None
    s3_client = get_s3_client()
    bucket_name, key = s3_path_split(s3_url)
    s3_params = {"Bucket": bucket_name, "Key": key}
    s3_expire = settings.AWS_EXPIRE_TIME
    s3_url = s3_client.generate_presigned_url(
        "get_object", Params=s3_params, ExpiresIn=s3_expire
    )
    return s3_url


def delete_s3(bucket_name, key, s3_url=None):
    try:
        s3_client = get_s3_client()
        if s3_url:
            bucket_name, key = s3_path_split(s3_url)
        s3_res = s3_client.delete_object(Bucket=bucket_name, Key=key)
        return "S3 Object Deleted", True
    except Exception as ex:
        return "error in file delete s3" + str(ex), False


def get_head_object_s3(bucket_name, key, s3_url=None):
    try:
        s3_client = get_s3_client()
        if s3_url:
            bucket_name, key = s3_path_split(s3_url)
        s3_res = s3_client.head_object(Bucket=bucket_name, Key=key)
        return s3_res, True
    except Exception as ex:
        return "error in file fetch head s3" + str(ex), False


def generate_presigned_url_post(file_key, bucket_name=DEFAULT_BUCKET):
    s3_client = get_s3_client()
    s3_params = {"Bucket": bucket_name, "Key": file_key}
    s3_expire = 300
    s3_res = s3_client.generate_presigned_post(**s3_params, ExpiresIn=s3_expire)
    return s3_res
