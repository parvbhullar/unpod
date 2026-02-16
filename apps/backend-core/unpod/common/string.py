import random
import re
import string
import secrets
import hashlib
from faker import Factory
from django.core.cache import cache
from django.utils.html import strip_tags

fake = Factory.create()


def checkValue(value):
    if value and value != "":
        return True
    if value != None:
        return True
    return False


def generate_code(N=16):
    token = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(N)
    )
    return token


def get_random_string(prefix, length=10):
    ALL_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(ALL_CHARS) for _ in range(length))
    if prefix:
        return prefix + code
    return code


def generate_color_hex():
    return fake.hex_color().upper()


def split_join_comma_seprated(files, value):
    print("files type", type(files), "value type", type(value))
    if files:
        files = files.split(",")
        print("split files", files)
        if value:
            files.append(value)
            print("append files", files)
        files_str = ",".join(files)
        print("files_str", files_str)
        return files_str
    return value


def split_full_name(full_name):
    n = full_name.find(" ")
    if n < 0:
        return full_name, ""
    return full_name[:n].strip(), full_name[n:].strip()


def string_to_int(keyword, len=8):
    hash = hashlib.sha256(keyword.encode()).hexdigest()
    hash = abs(int(hash, 16))
    return hash % (10**len)


def mask_email(email: str):
    index = email.find("@")
    email_prefix = email[:index]
    email_suffix = email[index:]
    mask_prefix_email = string_to_int(email_prefix, len=len(email_prefix))
    redis_key = "mask_email_prefix_{}".format(mask_prefix_email)
    cache.set(redis_key, email_prefix, timeout=60 * 60 * 24)
    mask_prefix_email = str(mask_prefix_email)[::-1]
    return "{}{}{}".format(email_prefix[:2], mask_prefix_email, email_suffix)


def unmask_email(email: str):
    index = email.find("@")
    email_prefix = email[:index]
    email_suffix = email[index:]
    mask_prefix_email = email_prefix[2:]
    mask_prefix_email = str(mask_prefix_email)[::-1]
    redis_key = "mask_email_prefix_{}".format(mask_prefix_email)
    mask_prefix_email = cache.get(redis_key)
    if mask_prefix_email:
        return "{}{}".format(mask_prefix_email, email_suffix)
    return None


def textify(html):
    if not html:
        return ""
    # Remove html tags and continuous whitespaces
    text_only = re.sub("[ \t]+", " ", strip_tags(html))
    # Strip single spaces in the beginning of each line
    return text_only.replace("\n ", "\n").strip()


def machine_to_label(name: str) -> str:
    return name.replace("_", " ").title()
