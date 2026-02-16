"""
JWT handlers for Django 4.2+ using PyJWT and SimpleJWT.
Replaces old djangorestframework-jwt package.
"""
import datetime
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

try:
    from rest_framework_simplejwt.tokens import RefreshToken
    SIMPLE_JWT_AVAILABLE = True
except ImportError:
    SIMPLE_JWT_AVAILABLE = False


def jwt_payload_handler(user):
    """
    Create JWT payload for a user.
    Compatible with old djangorestframework-jwt format.
    """
    User = get_user_model()
    username = user.get_username()

    payload = {
        'user_id': user.pk,
        'username': username,
        'email': getattr(user, 'email', ''),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=180),  # 180 day expiration
    }

    return payload


def jwt_encode_handler(payload):
    """
    Encode JWT token using PyJWT library (Django 4.2 compatible).
    """
    # Use Django's SECRET_KEY for encoding
    secret_key = settings.SECRET_KEY
    return jwt.encode(payload, secret_key, algorithm='HS256')


def jwt_decode_handler(token):
    """
    Decode JWT token using PyJWT library (Django 4.2 compatible).
    """
    secret_key = settings.SECRET_KEY
    try:
        return jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise
    except jwt.DecodeError:
        raise
    except jwt.InvalidTokenError:
        raise
