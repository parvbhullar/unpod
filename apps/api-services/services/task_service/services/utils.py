import datetime
import os


async def create_run_by_task(input, assignee, objective, task):
    from libs.api.config import get_settings

    settings = get_settings()
    run_data = {
        "space_id": task.get("space_id"),
        "user": task.get("user_info"),
        "collection_ref": task.get("collection_ref"),
        "run_mode": (
            "prod" if getattr(settings, "ENV_NAME", "Prod").lower() == "prod" else "dev"
        ),
        "org_id": task.get("org_id"),
        "thread_id": task.get("thread_id"),
        "assignee": assignee,
        "data": {},
        "tasks": [
            {
                "objective": objective,
                "input_data": input,
                "attachments": [],
                "execution_type": assignee,
            }
        ],
    }
    from services.task_service.models.api_models import APIRequestModel
    from services.task_service.api.api_v1.endpoints.task import create_run

    response = await create_run(APIRequestModel(**run_data))
    return response


def extract_name_from_email(email):
    username = email.split("@")[0]
    name_parts = username.replace(".", " ").replace("_", " ")
    pretty_name = " ".join([part.capitalize() for part in name_parts.split()])
    return pretty_name


def generate_mail_id(subject: str, sender: str):
    import hashlib
    import time

    timestamp = str(int(time.time()))
    base_string = subject + sender + timestamp
    return hashlib.sha1(base_string.encode()).hexdigest()[:16]


def create_dealer_draft_data(token, email_data, attachment_url, message_body, task):
    time_now = datetime.datetime.now(datetime.timezone.utc)
    mail_data = {
        "document_id": "document_id",
        "source": "gmail",
        "metadata": {},
        "subject": f"Re: {email_data['subject']}",
        "from": email_data["to"][0],
        "to": [email_data["from"]],
        "cc": email_data["cc"],
        "date": time_now,
        "date_ts": int(time_now.timestamp()),
        "email_threadId": email_data["email_threadId"],
        "labels": ["DRAFT"],
        "attachments": [{"url": attachment_url}],
        "has_attachments": 1,
        "body": message_body,
        "meta": {
            "title": f"Re: {email_data['subject']}",
            "description": message_body,
            "parent_id": email_data["email_threadId"],
            "user_id": email_data["meta"]["user_id"],
            "hub_id": email_data["meta"]["hub_id"],
            "kn_token": token,
            "task_id": task.get("task_id"),
            "run_id": task.get("run_id"),
        },
    }
    file_name = os.path.basename(attachment_url)
    mail_data["attachments"][0]["filename"] = file_name
    document_id = generate_mail_id(mail_data["subject"], mail_data["from"])
    mail_data["document_id"] = document_id
    mail_data["meta"]["id"] = document_id
    mail_data["meta"]["status"] = "draft"
    mail_data["meta"]["user"] = {
        "id": email_data["from"],
        "name": extract_name_from_email(email_data["from"]),
    }
    return mail_data


async def process_draft_logic(email_data, attachment_url, message_body, task):
    from libs.api.logger import get_logger
    from libs.core.jsondecoder import convertFromMongo
    from services.store_service.views.connector import create_doc_info

    app_logging = get_logger("task_service")

    token = email_data["meta"]["kn_token"]
    draft_data = create_dealer_draft_data(
        token, email_data, attachment_url, message_body, task
    )
    res = await create_doc_info(token, convertFromMongo(draft_data))
    if res.get("success") is False:
        app_logging.error("Failed to create draft: %s", res)
    else:
        app_logging.info(
            "Draft created successfully: %s %s", token, draft_data["document_id"]
        )
    return res
