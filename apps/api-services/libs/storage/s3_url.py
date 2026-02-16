import re
from urllib.parse import urlparse


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
