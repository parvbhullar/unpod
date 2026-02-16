import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict

import rsa
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import jwt
import argon2

_password_hasher = argon2.PasswordHasher()


ALGORITHM = "HS256"


def get_authorization_scheme_param(
    authorization_header_value: Optional[str],
) -> Tuple[str, str]:
    if not authorization_header_value:
        return "", ""
    scheme, _, param = authorization_header_value.partition(" ")
    return scheme, param


def get_random_secret_key(length=50) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"

    secret_key = "".join(secrets.choice(chars) for i in range(length))
    return secret_key


def get_random_auth_key(length=24) -> str:
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSUVWXYZ0123456789"
    secret_key = "".join(secrets.choice(chars) for i in range(length))
    return secret_key


def get_random_key(length=24, prefix=None, uppercase=False) -> str:
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSUVWXYZ0123456789"
    if prefix:
        secret_key = prefix + "".join(
            secrets.choice(chars) for _ in range(length - len(prefix))
        )
    else:
        secret_key = "".join(secrets.choice(chars) for _ in range(length))
    if uppercase:
        return secret_key.upper()
    return secret_key


def create_access_token(
    subject: dict, expires_delta: timedelta = None, settings=None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Dictionary with token claims
        expires_delta: Optional expiration timedelta (defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        settings: Settings object with DJANGO_SECRET_KEY and ACCESS_TOKEN_EXPIRE_MINUTES attributes (optional, will load if not provided)

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If settings cannot be loaded
    """
    if settings is None:
        # Auto-load settings if not provided
        from libs.api.config import get_settings

        settings = get_settings()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, **subject, "iat": datetime.now(timezone.utc)}
    encoded_jwt = jwt.encode(to_encode, settings.DJANGO_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str, settings=None) -> Dict:
    """
    Decode a JWT token.

    Args:
        token: JWT token string to decode
        settings: Settings object with DJANGO_SECRET_KEY attribute (optional, will load if not provided)

    Returns:
        Decoded token data as dictionary

    Raises:
        ValueError: If settings cannot be loaded
        Exception: If token is invalid
    """
    if settings is None:
        # Auto-load settings if not provided
        from libs.api.config import get_settings

        settings = get_settings()

    try:
        decoded_data = jwt.decode(
            token, settings.DJANGO_SECRET_KEY, algorithms=[ALGORITHM]
        )
    except Exception:
        raise Exception("Invalid JWT Token")
    return decoded_data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (argon2.exceptions.VerificationError, argon2.exceptions.InvalidHashError):
        return False


def verify_password_django(plain_password: str, hashed_password: str) -> bool:
    """Verify Django-style password (argon2 format).

    Args:
        plain_password: Plain text password to verify
        hashed_password: Django hashed password in format: algorithm$salt$hash

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Django format: algorithm$salt$hash
        if "$" not in hashed_password:
            # Not a valid Django password format
            return False

        algorithm, rest = hashed_password.split("$", 1)

        # Verify using argon2
        return argon2.PasswordHasher().verify("$" + rest, plain_password)
    except argon2.exceptions.VerificationError:
        return False
    except (ValueError, AttributeError) as e:
        # Invalid password format
        return False


def get_password_hash(password: str) -> str:
    return _password_hasher.hash(password)


def genrate_hash(hash_string, algorithm="sha256"):
    if isinstance(hash_string, bytes):
        hash_string = hash_string.decode()
    hash = hashlib.new(algorithm, hash_string.encode()).hexdigest()
    return hash


def decrypt(ciphertext, key):
    try:
        return rsa.decrypt(ciphertext, key).decode("ascii")
    except BaseException:
        return False


def pad_data_pkcs5(plain_data):
    """
    func to pad cleartext to be multiples of 8-byte blocks.
    """
    block_size = AES.block_size
    return plain_data + (block_size - len(plain_data) % block_size) * chr(
        block_size - len(plain_data) % block_size
    )


def unpad_data(data):
    return data[: -ord(data[len(data) - 1 :])]


def encrypt_data(data, key, type=None):
    """Encrypt data using AES-CBC. Output format: base64(iv + ciphertext)."""
    if type is not None:
        raw_key = key
    else:
        raw_key = key.encode("utf8")

    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(raw_key, AES.MODE_CBC, iv)
    padded = pad_data_pkcs5(data)
    encrypted_data = base64.b64encode(iv + cipher.encrypt(padded.encode("utf8")))
    return encrypted_data


def decrypt_data(data, key, type=None):
    """Decrypt data. Supports both AES-CBC (iv-prefixed) and legacy AES-ECB."""
    if isinstance(key, (bytes, bytearray)):
        try:
            raw_key = key.decode().encode("utf8")
        except Exception:
            raw_key = key
    else:
        raw_key = key

    raw = base64.b64decode(data)

    # CBC: first 16 bytes are the IV
    if len(raw) > AES.block_size:
        iv = raw[: AES.block_size]
        ciphertext = raw[AES.block_size :]
        try:
            cipher = AES.new(raw_key, AES.MODE_CBC, iv)
            plain = cipher.decrypt(ciphertext)
            result = unpad_data(plain)
            if type == "byte":
                return result
            return result.decode("utf8")
        except (ValueError, UnicodeDecodeError):
            pass

    # Fallback: legacy ECB decryption for old data
    cipher = AES.new(raw_key, AES.MODE_ECB)
    cipher_txt = cipher.decrypt(raw)
    if type == "byte":
        return unpad_data(cipher_txt)
    else:
        return unpad_data(cipher_txt).decode("utf8")


def generate_key(password):
    salt = get_random_bytes(32)
    key = PBKDF2(password, salt, dkLen=32)
    return key, salt


def to_hash256(secret_key):
    hash = hashlib.sha256(secret_key.encode("utf-8")).hexdigest()
    return hash


def str_to_base64(s):
    return base64.b64encode(s.encode("utf-8"))


def base64_to_str(b):
    return base64.b64decode(b).decode("utf-8")


def fetch_ek(app_key, sek):
    ek = decrypt_data(sek, base64.b64decode(app_key), type="byte")
    return ek


def generate_app_key():
    app_key_data = get_random_key(32)
    flat_app_key = base64.b64encode(app_key_data.encode("utf8")).decode()
    return flat_app_key
