import requests
from django.conf import settings

from unpod.common.datetime import get_datetime_now
from unpod.core_components.models import GlobalSystemConfig


def complete_message(message, **kwargs):
    """
    Complete a message by replacing placeholders with provided values.

    """
    if not kwargs:
        return message
    try:
        return message.format(**kwargs)
    except Exception as e:
        print(str(e))
        return message


def get_global_configs(key):
    config = GlobalSystemConfig.objects.filter(key=key).first()

    if config:
        return config.value
    else:
        return {}


def set_global_configs(key, value):
    GlobalSystemConfig.objects.update_or_create(key=key, defaults={"value": value})


def get_email_global_data():
    return {
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "CURRENT_YEAR": get_datetime_now().year,
    }


def get_app_info(product_id):
    frontend_info = get_global_configs("frontend_info")
    application = frontend_info.get(
        product_id,
        {
            "name": settings.APP_NAME,
            "url": settings.BASE_FRONTEND_URL,
        },
    )
    application_name = application.get("name", settings.APP_NAME)
    application_url = application.get("url", settings.BASE_FRONTEND_URL)

    return {
        "APP_NAME": application_name,
        "APP_URL": application_url,
        **get_email_global_data(),
    }


def safe_json(res):
    try:
        return res.json()
    except Exception:
        return {}


def api_request(url, request_type, retry=3, verify=True, headers={}, payload={}, timeout=30):
    """
    Make HTTP requests with proper timeout handling to prevent 504 Gateway Timeouts.

    Args:
        url: The URL to request
        request_type: HTTP method (get, post, put, delete, patch, options)
        retry: Number of retries on failure (default: 3)
        verify: SSL verification (default: True)
        headers: Request headers (default: {})
        payload: Request body as JSON (default: {})
        timeout: Request timeout in seconds (default: 30)

    Returns:
        dict: JSON response or error dict
    """
    for i in range(retry):
        try:
            if request_type.lower() == "get":
                res = requests.get(url, headers=headers, json=payload, verify=verify, timeout=timeout)
                return safe_json(res)

            elif request_type.lower() == "post":
                res = requests.post(url, headers=headers, json=payload, verify=verify, timeout=timeout)
                return safe_json(res)

            elif request_type.lower() == "put":
                res = requests.put(url, headers=headers, json=payload, verify=verify, timeout=timeout)
                return safe_json(res)

            elif request_type.lower() == "delete":
                res = requests.delete(url, headers=headers, json=payload, verify=verify, timeout=timeout)
                return safe_json(res)

            elif request_type.lower() == "patch":
                res = requests.patch(url, headers=headers, json=payload, verify=verify, timeout=timeout)
                return safe_json(res)

            elif request_type.lower() == "options":
                res = requests.options(
                    url, headers=headers, json=payload, verify=verify, timeout=timeout
                )
                return safe_json(res)

        except requests.exceptions.Timeout:
            print(f"Attempt {i + 1}: Request timeout for {url}")
        except requests.exceptions.ConnectionError as e:
            print(f"Attempt {i + 1}: Connection error for {url}: {e}")
        except Exception as e:
            print(f"Attempt {i + 1}: error hitting api retrying {e}")

    return {"success": False, "message": "error while hitting the api"}
