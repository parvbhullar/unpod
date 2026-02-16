import uuid


def generate_uuid():
    return uuid.uuid1().hex


def uuid1_unix_timestamp(uuid_):
    if type(uuid_) == type('A'):
        uuid_ = uuid.UUID(uuid_)
    import datetime as dt
    return (uuid_.time * 1e-7 - (dt.datetime.utcfromtimestamp(0) - dt.datetime(1582, 10, 15)).total_seconds())