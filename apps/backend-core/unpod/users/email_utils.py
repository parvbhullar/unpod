from django.conf import settings
from django.utils import timezone


def get_password_reset_body(user_full_name, link):
    message = f"<p>Dear {user_full_name if user_full_name != '' else 'Sir/Maam'},</p>"
    message += f"<p>A request has been received to change the password for your Unpod account</p>"
    message += f"<p><a href='{link}'>Click here </a> to reset the password.</p>"
    message += f"<p>This reset link is only valid for 30 minutes.</p>"
    message += f"<p>Please copy below link if above link not opening </p>"
    message += f"<p> <strong> {link} </strong> </p>"
    message += "<p>If you are receiving this mail in spam and unable to reset the password, please move this email from the Spam folder.</p>"
    # message += f"<br/>"
    message += "<p>Regards<br>"
    message += "<p>Unpod Team</p>"
    return message


def get_verify_email_body(link, app_name):
    message = f"<p>Dear Sir/Maam,</p>"
    message += f"<p>Below the link to verify your {app_name} account</p>"
    message += f"<p><a href='{link}'>Click here </a> to verfiy your email</p>"
    message += f"<p>This link is only valid for 30 minutes.</p>"
    message += f"<p>Please copy below link if above link not opening </p>"
    message += f"<p> <strong> {link} </strong> </p>"
    message += "<p>If you are receiving this mail in spam and unable to click on link, please move this email from the Spam folder.</p>"
    # message += f"<br/>"
    message += "<p>Regards<br>"
    message += f"<p>{app_name} Team</p>"
    return message


def get_admin_login_body(otp):
    message = f"<p>Dear Sir/Maam,</p>"
    message += f"<p>Please Find the Login OTP For Admin Login</p>"
    message += f"<p> <strong> {otp} </strong> </p>"
    message += f"<p>This OTP is only valid for 10 minutes.</p>"
    message += "<p>Regards<br>"
    message += "<p>Unpod Team</p>"
    return message


def get_register_as_user(user, password):
    message = f"Hi {user.first_name if user.first_name != '' else 'Sir/Maam'}, \n\n"
    message += (
        f"Welcome to {settings.COMPANY_NAME} – we're excited to have you on board! \n"
    )
    message += (
        f"Your account has been successfully created. Here are your login details: \n\n"
    )
    message += f"Username: {user.username}\n"
    message += f"Password: {password}\n\n"
    message += f"You can log in using the following link: "
    message += f"{settings.BASE_FRONTEND_URL}/auth/signin \n\n"
    message += f"For your security, we recommend changing your password after your first login. \n"
    message += f"If you need help, feel free to contact our support team at {settings.SUPPORT_EMAIL}. \n"
    message += f"Thanks,\n"
    message += f"The {settings.COMPANY_NAME} Team\n"
    message += (
        f"© {timezone.now().year} {settings.COMPANY_NAME}. All rights reserved.\n\n"
    )
    return message


def get_new_user_register(user):
    plain_text = f"Hello Admin,\n\n"
    plain_text += (
        f"A new user has successfully registered on {settings.COMPANY_NAME}.\n\n"
    )
    plain_text += f"Here are the account details:\n"
    plain_text += f"Name: {user.get_full_name()}\n"
    plain_text += f"Email: {user.email}\n"
    plain_text += f"Phone: {user.phone_number or 'Not provided'}\n"
    plain_text += (
        f"Account created at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    plain_text += f"You can view and manage this user from the Admin:\n"
    plain_text += (
        f"{settings.BASE_URL}/{settings.ADMIN_URL}/users/user/{user.id}/change/\n\n"
    )
    plain_text += (
        f"If this registration looks suspicious, please review it immediately.\n\n"
    )
    plain_text += f"Thanks,\n"
    plain_text += f"The {settings.COMPANY_NAME} System\n"
    plain_text += (
        f"© {timezone.now().year} {settings.COMPANY_NAME}. All rights reserved.\n"
    )
    return plain_text
