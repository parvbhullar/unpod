from datetime import datetime, timedelta
import time
from django.contrib.auth import get_user_model

from unpod.common.enum import PostRepeatType
from unpod.common.mixin import UsableRequest
from unpod.space.utils import checkPostSpaceAccess
from unpod.thread.models import PostCreationCronModel, PostCronResultModel
from unpod.thread.serializers import ThreadCreateSerializer
from unpod.thread.utils import addTaskToAgent
from unpod.common.jwt import jwt_encode_handler, jwt_payload_handler


User = get_user_model()


def createCronPost(
    user_id,
    space_token,
    title,
    content,
    privacy_type="public",
    post_type="ask",
    content_type="text",
    pilot="superpilot",
    extra_data=None,
):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return {
            "success": False,
            "message": "User not found",
        }
    try:
        space = checkPostSpaceAccess(user, token=space_token, check_op=True)
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }
    request = UsableRequest()
    request.user = user
    payload = jwt_payload_handler(user)
    payload["exp"] = datetime.utcnow() + timedelta(days=1)
    token = jwt_encode_handler(payload)
    request.headers = {"Authorization": f"JWT {token}"}
    requst_data = {
        "content": content,
        "privacy_type": privacy_type,
        "post_type": post_type,
        "content_type": content_type,
        "pilot": pilot,
    }
    if extra_data:
        if "knowledge_bases" in extra_data:
            requst_data["knowledge_bases"] = extra_data["knowledge_bases"]
    if title:
        requst_data["title"] = title
    request.data = requst_data
    context = {"request": request, "space": space}
    ser = ThreadCreateSerializer(data=requst_data, context=context)
    if ser.is_valid():
        instance = ser.save()
        if (
            instance.post_type in ["task", "ask", "notebook"]
            and instance.content_type != "voice"
        ):
            addTaskToAgent(
                instance.post_id,
                instance.title,
                instance.content,
                request,
                instance.post_type,
                instance.space,
            )
        return {"success": True, "message": "Post Created", "post_id": instance.post_id}
    return {
        "message": "There is some Validation error",
        "errors": ser.errors,
        "success": False,
    }


def get_next_schedule_timestamp(repeat_type, schedule_timestamp):
    if repeat_type == PostRepeatType.never.name:
        return schedule_timestamp
    if repeat_type == PostRepeatType.daily.name:
        return schedule_timestamp + 86400
    elif repeat_type == PostRepeatType.weekly.name:
        return schedule_timestamp + 604800
    elif repeat_type == PostRepeatType.monthly.name:
        return schedule_timestamp + 2592000
    elif repeat_type == PostRepeatType.yearly.name:
        return schedule_timestamp + 31536000

    return schedule_timestamp


def fetch_create_cron_post():
    print("timestamp", datetime.now().timestamp())
    jobs = PostCreationCronModel.objects.filter(
        repeat_schedule=True,
        retry__lt=3,
        schedule_timestamp__lte=datetime.now().timestamp(),
        schedule_timestamp__gte=datetime.now().timestamp() - 86400,
    )[:50]
    print("Total cron jobs", jobs.count())
    for job in jobs:
        print("Processing the cron job", job.user_id, job.space_token, job.id)
        try:
            res = createCronPost(
                job.user_id,
                job.space_token,
                job.title,
                job.content,
                job.privacy_type,
                job.post_type,
                job.content_type,
                job.pilot,
                job.extra_data,
            )
            if res["success"]:
                post_id = res["post_id"]
                message = res["message"]
                PostCronResultModel.objects.create(
                    post_creation_cron=job,
                    post_created=True,
                    message=message,
                    success=True,
                    post_id=post_id,
                    response=res,
                )
                PostCreationCronModel.objects.filter(id=job.id).update(
                    message=message,
                    success=True,
                    post_created=True,
                    post_id=post_id,
                    response=res,
                    repeat_schedule=False
                    if job.repeat_type == PostRepeatType.never.name
                    else True,
                    schedule_timestamp=get_next_schedule_timestamp(
                        job.repeat_type, job.schedule_timestamp
                    ),
                )
            else:
                retry = job.retry + 1
                PostCronResultModel.objects.create(
                    post_creation_cron=job,
                    post_created=False,
                    message=res["message"],
                    success=False,
                    response=res,
                )
                PostCreationCronModel.objects.filter(id=job.id).update(
                    retry=retry,
                    post_created=False,
                    success=False,
                    message=res["message"],
                    response=res,
                )
        except Exception as e:
            print("Error in cron job", e)
            PostCronResultModel.objects.create(
                post_creation_cron=job,
                post_created=False,
                message=str(e),
                success=False,
                response={},
            )
            PostCreationCronModel.objects.filter(id=job.id).update(
                retry=job.retry + 1,
                post_created=False,
                success=False,
                message=str(e),
                response={},
            )

        time.sleep(0.5)
    return f"Total Thread jobs processed {jobs.count()}"
