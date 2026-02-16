from rest_framework import serializers
from django.contrib.auth.models import AnonymousUser

def checkUserReturnDefault(defaultVal):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            ser = args[0]
            user = AnonymousUser()
            if isinstance(ser, serializers.Serializer):
                user = getattr(ser.context.get('request'), 'user', None) or ser.context.get('user')
                if user is None or not user.is_authenticated:
                    return defaultVal
            return fun(*args, **kwargs)
        return wrapper
    return decorator