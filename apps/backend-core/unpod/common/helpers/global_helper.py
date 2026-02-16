from django.conf import settings

from unpod.common.middleware import get_current_request


def get_request_header(name, default=None):
    request = get_current_request()
    if not request:
        return default
    return request.headers.get(name, default)


def get_product_id():
    return get_request_header("Product-Id", settings.DEFAULT_PRODUCT_ID)


def get_current_user():
    request = get_current_request()
    if not request:
        return None
    return getattr(request, "user", None)


def format_validation_errors(errors):
    formatted_errors = []
    for field, error_list in errors.items():
        for error in error_list:
            # formatted_errors.append({"field": field, "message": str(error)})
            formatted_errors.append(f"{field}: {str(error)}")

    return formatted_errors[0] if len(formatted_errors) > 0 else formatted_errors
