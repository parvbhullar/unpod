import os
import httpx

from super_services.libs.core.httpx import fetch_with_manual_retry


async def validate_phone_number(phone_number):
    """
    Validate phone number and return in normal format without +, with country code

    Args:
        phone_number (str): The phone number to validate.

    Returns:
        str: The phone number in normal format without +, with country code.
    """
    phone_number = phone_number.strip()
    phone_number = phone_number.replace(" ", "")
    if phone_number.startswith("+"):
        return phone_number[1:]
    elif phone_number.startswith("91"):
        return phone_number
    else:
        return f"91{phone_number}"


async def send_sms_msg91(phone_number, temp_id, **kwargs):
    """
    Send SMS using Msg91 API.

    Args:
        phone_number (str): The recipient's phone number.
        temp_id (str): The template ID for the SMS message.
        **kwargs: Additional keyword arguments to be passed to the API.

    Returns:
        dict: The response from the API.
    """
    url = "https://api.msg91.com/api/v5/flow/"
    headers = {
        "authkey": os.getenv("MSG91_AUTH_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "flow_id": temp_id,
        "sender": os.getenv("MSG91_HEADER", "GFBIZT"),
        "mobiles": await validate_phone_number(phone_number),
        **kwargs,
    }
    client = httpx.AsyncClient()
    res = await fetch_with_manual_retry(
        client, "POST", url, headers=headers, json=payload
    )
    print(res.text, res.status_code)
    return res
