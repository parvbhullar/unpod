import hashlib
import re
import unicodedata


def convert_to_int(inp_str: str):
    try:
        val = int(inp_str)
        return val
    except BaseException:
        try:
            val = float(inp_str)
            return val
        except BaseException:
            return inp_str


def convert_to_float(inp_str: str):
    try:
        val = float(inp_str)
        return val
    except BaseException:
        return inp_str


def string_to_int(keyword, len=8):
    hash = hashlib.sha256(keyword.encode()).hexdigest()
    hash = abs(int(hash, 16))
    return hash % (10**len)


def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
