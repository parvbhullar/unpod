import secrets
import string
from super_services.libs.core.sonyflake import app_sonyflake

def get_random_string(prefix, length=10):
    ALL_CHARS = string.ascii_lowercase+string.ascii_uppercase+string.digits
    code = ''.join(secrets.choice(ALL_CHARS) for _ in range(length))
    if prefix:
        return prefix+code
    return code


def generateRandomKey(prefix=None, unique=False, length=6):
    token = get_random_string(prefix, length=length)
    if unique:
        token=token+str(app_sonyflake.next_id())
    return token