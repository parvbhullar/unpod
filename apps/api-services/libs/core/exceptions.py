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


def build_exception_response(exc, default_status_code):
    import json
    from starlette.responses import JSONResponse

    error_res = dict()
    if len(exc.args):
        res = exc.args[0]
    else:
        res = json.loads(str(exc))
    if isinstance(res, str):
        res = json.loads(res)
    status_code = res.pop("status_code", default_status_code)
    error_res["message"] = res.pop("message", "Error")
    error_res.update(res)
    error_res["success"] = False
    return JSONResponse(error_res, status_code=status_code)
