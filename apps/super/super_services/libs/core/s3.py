import boto3
from io import BytesIO
import os
from botocore.client import Config

from super_services.libs.config import settings
import re
from urllib.parse import urlparse

media_location = f"{os.getcwd()}/media/"


def get_s3_client():
    if getattr(settings, "s3_client", None):
        return settings.s3_client
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    settings.s3_client = s3_client
    return s3_client


def read_file(bucket_name, filename):
    s3_client = get_s3_client()
    f = BytesIO()
    s3_client.download_fileobj(bucket_name, filename, f)
    return f.getvalue()


def read_file_header(bucket_name, filename):
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



def style(url):
    o = urlparse(url)
    if o.scheme == "s3":
        return "s3"
    if re.search(r"^s3[.-](\w{2}-\w{4,9}-\d\.)?amazonaws\.com", o.netloc):
        return "bucket-in-path"
    if re.search(r"\.s3[.-](\w{2}-\w{4,9}-\d\.)?amazonaws\.com", o.netloc):
        return "bucket-in-netloc"
    raise ValueError(f"Unknown url style: {url}")


def parse_s3_credential_url(url):
    o = urlparse(url)
    cred_name, bucket = o.netloc.split("@")
    key = o.path if o.path[0] != "/" else o.path[1:]
    return {"bucket": bucket, "key": key, "credential_name": cred_name}


def parse_s3_url(url):
    o = urlparse(url)
    bucket = o.netloc
    key = o.path if o.path[0] != "/" else o.path[1:]
    return bucket, key


def parse_bucket_in_path_url(url):
    path = urlparse(url).path
    bucket = path.split("/")[1]
    key = "/".join(path.split("/")[2:])
    return bucket, key


def parse_bucket_in_netloc_url(url):
    o = urlparse(url)
    bucket = o.netloc.split(".")[0]
    key = o.path if o.path[0] != "/" else o.path[1:]
    return bucket, key


def s3_path_split(url):
    url_style = style(url)
    if url_style == "s3-credential":
        return parse_s3_credential_url(url)
    if url_style == "s3":
        return parse_s3_url(url)
    if url_style == "bucket-in-path":
        return parse_bucket_in_path_url(url)
    if url_style == "bucket-in-netloc":
        return parse_bucket_in_netloc_url(url)
