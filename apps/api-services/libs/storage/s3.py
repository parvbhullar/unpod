import boto3
from io import BytesIO
import os
from botocore.client import Config
from libs.storage.s3_url import s3_path_split
from libs.api.config import get_settings

media_location = f"{os.getcwd()}/media/"


def get_s3_client():
    settings = get_settings()
    if getattr(settings, "s3_client", None):
        return settings.s3_client
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )
    settings.s3_client = s3_client
    return s3_client


def read_file(bucket_name, filename, s3_url=None):
    if s3_url:
        bucket_name, filename = s3_path_split(s3_url)
    s3_client = get_s3_client()
    f = BytesIO()
    s3_client.download_fileobj(bucket_name, filename, f)
    return f.getvalue()


def read_file_header(bucket_name, filename, s3_url=None):
    if s3_url:
        bucket_name, filename = s3_path_split(s3_url)
    s3_client = get_s3_client()
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key=filename)
    return s3_response_object


def presigned_url(bucket_name, filename):
    s3_client = get_s3_client()
    url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket_name, "Key": filename},
        ExpiresIn=3600,
    )
    return url


def upload_s3(bucket, data, file_name, save_local=False):
    s3_client = get_s3_client()
    file_url = f"https://{bucket}.s3.ap-south-1.amazonaws.com/" + file_name
    try:
        if save_local:
            if not os.path.exists(media_location):
                os.mkdir(media_location)
            file_location = media_location + file_name
            with open(file_location, "w") as fileObj:
                fileObj.write(data)
                fileObj.close()
            return file_name, True
        s3_res = s3_client.put_object(Bucket=bucket, Body=data, Key=file_name)
        return file_url, True
    except Exception as ex:
        return "error in file upload to s3" + str(ex), False


def download_file(bucket_name, filename, output_location):
    s3_client = get_s3_client()
    os.makedirs(os.path.dirname(output_location), exist_ok=True)
    s3_client.download_file(bucket_name, filename, output_location)
    return output_location


def upload_file_to_s3(bucket, file_location, output_location):
    s3_client = get_s3_client()
    s3_client.upload_file(file_location, bucket, output_location)
    return f"https://{bucket}.s3.ap-south-1.amazonaws.com/{output_location}"


def upload_fileobj_to_s3(bucket, fileobj, output_location):
    s3_client = get_s3_client()
    s3_client.upload_fileobj(fileobj, bucket, output_location)
    return f"https://{bucket}.s3.ap-south-1.amazonaws.com/{output_location}"
