import markdown
from django.conf import settings
from django.utils.text import Truncator

from unpod.common.helpers.service_helper import send_email
from unpod.core_components.event_mail import prepare_post_mail
from unpod.users.utils import get_name


BASE_FRONTEND_URL = settings.BASE_FRONTEND_URL

if not BASE_FRONTEND_URL.endswith("/"):
    BASE_FRONTEND_URL = BASE_FRONTEND_URL + "/"

EVENT_CONST = {
    "send_post_email": {
        "event_description": "Send Post Email",
        "event_type": "post_created",
        "event_execution": "send",
    }
}


def prepare_event_base(event_name):
    return EVENT_CONST.get(event_name, {})


def prepase_event_config(event_name, obj):
    if event_name == "send_post_email":
        return {
            "user": obj.user.id,
            "space_token": obj.space.token,
            "post_pk": obj.id,
            "post_id": obj.post_id,
            "post_type": obj.post_type,
        }
    return {}


def process_send_post_email(event):
    from unpod.thread.models import ThreadPost

    event_config = event.event_config
    post_pk = event_config.get("post_pk")
    post_instance = (
        ThreadPost.objects.filter(pk=post_pk)
        .prefetch_related("threadpostpermission_post", "space__spacememberroles_space")
        .select_related("user", "space")
        .first()
    )
    if not post_instance:
        return True, "Post not found"

    title = post_instance.title
    description = post_instance.description
    content = post_instance.content or description
    link = f"{BASE_FRONTEND_URL}thread/{post_instance.slug}/"
    post_user = post_instance.user
    space_name = post_instance.space.name
    post_user_email = None
    post_user_name = None
    if post_user and post_user.email:
        post_user_email = post_user.email
        post_user_name = get_name(post_user.first_name, post_user.last_name)
    if post_instance.post_type in ["task", "ask", "notebook"]:
        if post_instance.block and len(post_instance.block) == 0:
            return "wait", "Post in progress"
        # send email logic
        else:
            block = post_instance.block
            content = block.get("data", {}).get("content") or content or description
    elif post_instance.post_type in ["post", "article"]:
        pass
    else:
        return True, "Post type not supported"

    content = markdown.markdown(content)
    content = Truncator(content).words(300, truncate="...")
    subject = f"New Post: {title}"
    if post_user_name:
        subject = f"{post_user_name} posted new insight"
    user_list = post_instance.space.spacememberroles_space.all().values(
        "user__email", "user__first_name", "user__last_name"
    )
    email_from = settings.EMAIL_FROM_ADDRESS
    for email in user_list:
        if email["user__email"] == post_user_email:
            continue
        recipient_list = [
            email["user__email"],
        ]
        user_name = get_name(
            email.get("user__first_name", ""), email.get("user__last_name", "")
        )
        mail_body = prepare_post_mail(
            user_name, post_user_name, space_name, title, description, content, link
        )

        send_email(
            subject,
            email_from,
            recipient_list,
            mail_body=mail_body,
            mail_type="html",
        )

    return True, f"Email sent successfully, Total Emails - {len(user_list)-1}"
