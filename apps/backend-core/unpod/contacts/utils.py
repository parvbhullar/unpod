from django.conf import settings

from unpod.common.helpers.global_helper import get_product_id
from unpod.common.helpers.service_helper import send_email
from unpod.common.utils import get_app_info


def send_demo_email():
    product_id = get_product_id()
    app = get_app_info(product_id)
    APP_URL = app.get("APP_URL")
    APP_NAME = app.get("APP_NAME")

    print(f"Sending demo email for {APP_NAME} at {APP_URL}", app)

    try:
        subject = f"Demo Email - {APP_NAME}"
        html_message = "<p>Dear Sir/Ma'am,</p>"
        html_message += f"<p>This is a demo email from {APP_NAME}.</p>"
        html_message += f"<p>Visit us at <a href='{APP_URL}'>{APP_NAME}</a></p>"
        html_message += "<p>Regards <br>"
        html_message += "Unpod Team</p>"

        from_email = settings.EMAIL_FROM_ADDRESS
        recipient_list = [
            "babulalkumawat83@gmail.com",
        ]

        sent_count, error_message = send_email(
            subject,
            from_email,
            recipient_list,
            mail_body=html_message,
            mail_type="html",
        )

        if error_message:
            return f"Failed to send email: {error_message}"

        return f"Email sent (check console or inbox depending on backend) - {sent_count } emails sent."
    except Exception as e:
        return f"Failed to send email: {str(e)}"
