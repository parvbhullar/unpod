import json

from django.conf import settings
from django.core.cache import cache

from .otp import generate_otp


def redis_key(number, device_id, prefix):
    key = "otp_verify__"
    key = prefix +'__'+ key
    key += str(number) + "__"
    key += str(device_id) + "__"
    key += str(settings.ENV_NAME)
    return key


def set_cache_helper(key_to_set, key):
    if key_to_set['resend'] > 0:
        otp = key_to_set['otp']
        cache.set(key, json.dumps({'resend': key_to_set['resend']-1, 'otp': key_to_set['otp']}), cache.ttl(key))
        ttl = cache.ttl(key)
        check = True
    else:
        otp = False
        ttl = cache.ttl(key)
        check = False
    return otp, ttl, check


def get_status_phone_email(email, phone_number, device_id, prefix):
    email_otp = None
    phone_otp = None
    email_ttl = 600
    phone_ttl = 600
    email_check = True
    phone_check = True

    phone_key = redis_key(phone_number, device_id, prefix)
    email_key = redis_key(email, device_id, prefix)

    email_key_set = cache.get(email_key)
    phone_key_set = cache.get(phone_key)
    if email_key_set and phone_key_set:
        email_key_set = json.loads(email_key_set)
        phone_key_set = json.loads(phone_key_set)
        email_otp, email_ttl, email_check = set_cache_helper(email_key_set, email_key)
        phone_otp, phone_ttl, phone_check = set_cache_helper(phone_key_set, phone_key)
    elif email_key_set:
        phone_otp = generate_otp(phone_key)
        cache.set(phone_key, json.dumps({'resend': 3, 'otp': phone_otp}), phone_ttl)
        email_key_set = json.loads(email_key_set)
        email_otp, email_ttl, email_check = set_cache_helper(email_key_set, email_key)
    elif phone_key_set:
        email_otp = generate_otp(email_key)
        cache.set(email_key, json.dumps({'resend': 3, 'otp': email_otp}), email_ttl)
        phone_key_set = json.loads(phone_key_set)
        phone_otp, phone_ttl, phone_check = set_cache_helper(phone_key_set, phone_key)
    else:
        email_otp = generate_otp(email_key)
        phone_otp = generate_otp(phone_key)
        cache.set(email_key, json.dumps({'resend': 3, 'otp': email_otp}), email_ttl)
        cache.set(phone_key, json.dumps({'resend': 3, 'otp': phone_otp}), phone_ttl)
    return email_check, phone_check, email_ttl, phone_ttl, email_otp, phone_otp


def get_status(number, device_id, prefix, ttl = 600, resend = True):
    key = redis_key(number, device_id, prefix)
    check_if_set = cache.get(key)
    if check_if_set:
        check_if_set = json.loads(check_if_set)
        if check_if_set['resend'] > 0 and resend:
            cache.set(key, json.dumps(
                {'resend': check_if_set['resend'] - 1, 'otp': check_if_set['otp']}), cache.ttl(key))
            return True, cache.ttl(key), check_if_set['otp']
        else:
            return False, cache.ttl(key), False
    else:
        otp = generate_otp(device_id)
        cache.set(key, json.dumps({'resend': 3, 'otp': otp}), ttl)
        return True, ttl, otp


def set_otp(number, device_id, otp, prefix):
    key = redis_key(number, device_id, prefix)
    check_if_set = cache.get(key)
    if (check_if_set and check_if_set['resend'] > 0) or not check_if_set:
        return cache.ttl(key)
    return 0


def get_otp(number, device_id, prefix):
    key = redis_key(number, device_id, prefix)
    print(key, 'redis_key')
    check_if_set = cache.get(key)
    if check_if_set:
        check_if_set = json.loads(check_if_set)
        return check_if_set['otp']
    else:
        return None


def delete_key(number, device_id, prefix):
    key = redis_key(number, device_id, prefix)
    cache.delete(key)


def redis_set(key, data, ttl):
    if isinstance(data, dict):
        data = json.dumps(data)
    cache.set(key, data, timeout=ttl)

def redis_get(key):
    return cache.get(key)

def redis_delete(key):
    cache.delete(key)