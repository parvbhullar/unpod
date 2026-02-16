SOURCE_DICT = {"https://qa2.unpod.tv": "qa2"}


def get_source(request):
    return "qa2"
    origin = request.headers.get("Origin")
    return SOURCE_DICT.get(origin, "main")
