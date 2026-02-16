class NotFound(Exception):
    pass


class APIException(Exception):
    pass


class API206Exception(Exception):
    pass


class APICommonException(Exception):
    pass


class ImproperlyConfigured(Exception):
    """
    Application is somehow improperly configured
    """

    pass


class InsufficientFundException(Exception):
    pass
