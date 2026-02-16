import base64
import os
import re
import datetime

import jwt
import pyotp
import requests
from django.conf import settings
from django.template.loader import render_to_string

from unpod.common.helpers.global_helper import get_product_id
from unpod.common.helpers.service_helper import send_email
from unpod.common.utils import get_app_info
from unpod.users.email_utils import get_admin_login_body, get_verify_email_body


def jwt_encode_handler(payload):
    """
    Encode JWT token using PyJWT library (Django 4.2 compatible).
    Replaces the old djangorestframework-jwt encoder.
    """
    # Add expiration time (1 hour for email verification tokens)
    if 'exp' not in payload:
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Use Django's SECRET_KEY for encoding
    secret_key = settings.SECRET_KEY

    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_otp(device_id="4970d474-b22a-11eb-8f1b-d8fc9366b2be"):
    data_random = ("JBSWY3DPEHPK3PXPDHAJU" + device_id).encode("ascii")
    totp = pyotp.TOTP(base64.b32encode(data_random))
    return totp.now()


def verify_number(number):
    if not number or len(str(number)) == 0:
        return False
    number = str(number).lstrip("0")
    if re.match(r"^\d{10}$", number):
        return True
    return False


def verify_otp_format(number):
    if not number or len(str(number)) == 0:
        return False
    number = str(number)
    if re.match(r"^\d{6}$", number):
        return True
    return False


def send_otp(number, otp, is_number, is_email):
    retry = 0
    if is_number:
        while retry < 5:
            try:
                if len(number) > 10:
                    number = number[-10:]
                data_dict = {
                    "flow_id": "633ac3fa5b4b867bba6b3ef2",
                    "sender": "GOFRDM",
                    "mobiles": "91" + number,
                    "otp": str(otp),
                    "key": str("9jlR69M6fa5"),
                }
                headers = {
                    "authkey": settings.MSG91_AUTH_KEY,
                    "content-type": "application/JSON",
                }
                response = requests.post(
                    settings.MSG91_URL, json=data_dict, headers=headers
                )
                print(f"{str(number)}+&otp=+{str(otp)}&type==mobile")
                break
            except Exception as e:
                retry = retry + 1
    elif is_email:
        subject = "Your code for Account Verification"
        message = "Dear Sir/Ma'am, \n\n"
        message += "Thanks for registering with us.\n\n"
        message += "Please find the OTP to verify your unpod account.\n\n"
        message += f"{otp}\n\n\n"
        message += "Regards,\n"
        message += "Unpod Team\n"
        email_from = settings.EMAIL_FROM_ADDRESS
        recipient_list = [
            number,
        ]
        send_email(
            subject,
            email_from,
            recipient_list,
            mail_body=message,
        )
        print(f"{str(number)}+&otp=+{str(otp)}&type==email")


def send_otp_mobile(number, otp):
    sms_data = dict()
    user = {
        "mobile": number,
        "sms_fields": {
            "otp": otp,
            "key": str("9jlR69M6fa5"),
        },
    }
    sms_data["user"] = [user]
    sms_data["channel"] = ["SMS"]
    sms_data["sms"] = settings.SMS_OTP_FLOW_ID


def send_otp_email(email, otp):
    subject = "Your code for Account Verification"
    send_message = "<p>Dear Sir/Ma'am,</p>"
    send_message += "<p>Thanks for registering with us. <br>"
    send_message += "Please find the OTP to verify your unpod.ai account.<br>"
    send_message += f"{otp}<br></p>"
    send_message += "<p>Regards <br>"
    send_message += "Unpod Team</p>"

    email_data = {}
    email_data["email"] = {"subject": subject, "body": send_message, "attachments": {}}
    email_data["channel"] = ["EMAIL"]
    user_data = {
        "from_email": settings.FROM_EMAIL,
        "email": email,
        "cc": [],
        "bcc": [],
        "fields": {},
    }
    email_data["user"] = [user_data]


def send_otp_request(number, otp, is_number, is_email):
    if is_number:
        send_otp_mobile(number, otp)
    elif is_email:
        send_otp_email(number, otp)


def send_otp_link(email, otp):
    """
    Send email verification link using HTML template. (Deprecated)
    Args:
        email (str): Recipient email address.
        otp (str): The OTP code to send.
    Returns:
        None
    """
    product_id = get_product_id()
    app = get_app_info(product_id)
    APP_URL = app.get("APP_URL")
    APP_NAME = app.get("APP_NAME")

    subject = f"{APP_NAME} <> Account Verification"
    token_payload = {"email": email, "token": otp}
    token = jwt_encode_handler(token_payload)

    link = f"{APP_URL}/verify-email?token={token}"
    html_message = get_verify_email_body(link, APP_NAME)
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [
        email,
    ]
    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )


def send_admin_otp(email, otp):
    config_file = os.environ.get('DJANGO_SETTINGS_MODULE')
    setting_env = config_file.split(".")[-1]
    subject = f"Unpod Admin Account Verification - {setting_env.title()}"
    html_message = get_admin_login_body(otp)
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [
        email,
    ]
    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )


def send_verify_email_otp(email, otp, expiry_minutes=30):
    """
    Send email verification OTP using HTML template.

    Args:
        email (str): Recipient email address.
        otp (str): The OTP code to send.
        expiry_minutes (int, optional): OTP validity in minutes. Defaults to 10.

    Returns:
        tuple: (sent_count (int), error_message (str or None))
    """
    product_id = get_product_id()
    app = get_app_info(product_id)
    APP_NAME = app.get("APP_NAME")

    context = {
        "otp": otp,
        "expiry_minutes": expiry_minutes,
        **app,
    }

    html_message = render_to_string("emails/verify_email_otp.html", context)
    subject = f"{APP_NAME} - Email Verification OTP"
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [email]

    return send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )


def send_forgot_password_email(email, token, user_name=None):
    """
    Send forgot password email using HTML template.

    Args:
        email (str): Recipient email address.
        token (str): Password reset token.
        user_name (str, optional): User's name for personalization.

    Returns:
        tuple: (sent_count (int), error_message (str or None))
    """
    product_id = get_product_id()
    app = get_app_info(product_id)
    APP_NAME = app.get("APP_NAME")
    APP_URL = app.get("APP_URL")
    reset_link = f"{APP_URL}/auth/reset-password?token={token}"

    context = {
        "reset_link": reset_link,
        "user_name": user_name,
        **app,
    }

    html_message = render_to_string("emails/forgot_password.html", context)
    subject = f"{APP_NAME} - Password Reset Request"
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [email]

    return send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )
