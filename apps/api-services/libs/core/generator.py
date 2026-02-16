import secrets
import string
from libs.core.sonyflake import app_sonyflake


def get_random_string(prefix, length=10):
    ALL_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(ALL_CHARS) for _ in range(length))
    if prefix:
        return prefix + code
    return code


def generateRandomKey(prefix=None, unique=False, length=6, sonyflake=None):
    """
    Generate a random key with optional prefix and unique ID.

    Args:
        prefix: Optional prefix for the key
        unique: If True, append a unique ID from sonyflake
        length: Length of the random string part
        sonyflake: SonyFlake instance (uses app_sonyflake if not provided)

    Returns:
        Generated random key string
    """
    token = get_random_string(prefix, length=length)
    if unique:
        if sonyflake is None:
            sonyflake = app_sonyflake
        token = token + str(sonyflake.next_id())
    return token
