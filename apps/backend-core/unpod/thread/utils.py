import json
import requests
from django.conf import settings
from unpod.common.exception import APIException206
from unpod.common.helpers.service_helper import send_email

from unpod.common.jwt import jwt_encode_handler
from unpod.common.mixin import UsableRequest

# from unpod.common.s3 import generate_presigned_url_s3
from unpod.common.origin import get_source
from unpod.common.s3_url import s3_path_split
from unpod.common.storage_backends import cloudinaryBackend, imagekitBackend
from unpod.roles.services import getRole
from unpod.thread.email_utils import get_post_invite_mail_body


def generateThreadRole(post, user, role_code):
    thread_role = UsableRequest()
    thread_role.post = post
    thread_role.user = user
    thread_role.role = getRole(role_code, "post")
    return thread_role


def getCoverImageData(cover_image):
    cover_image_url = cover_image.get("url")
    public_id = cover_image.get("public_id")
    privacy_type = cover_image.get("privacy_type")
    if public_id:
        cloudObject = cloudinaryBackend.processFetchMediaData(public_id, privacy_type)
        cover_image["url"] = cloudObject.get("url")
        return cover_image
    if cover_image_url and "cloudinary" in cover_image_url:
        return cover_image
    # url = generate_presigned_url_s3(cover_image_url)
    bucket_name, key = s3_path_split(cover_image_url)
    if "media/" in key:
        key = key.replace("media/", "")
    url = imagekitBackend.generateURL(key)
    cover_image["url"] = url
    return cover_image


def extractPostId(post_slug):
    if not post_slug:
        raise APIException206({"message": "Invalid Post Id"})
    try:
        post_id = int(post_slug.split("-")[-1])
    except Exception as ex:
        print("post_slug", post_slug)
        raise APIException206({"message": "Invalid Post Id"})
    return post_id


def generatePostSlug(space, post, post_id=None):
    from django.utils.text import slugify

    from unpod.thread.models import PostRelation

    # post_slug = f"{space.slug}"
    post_slug = ""
    if post.post_rel != PostRelation.main_post.name:
        if post.title and post.title != "":
            post_slug = f"{post_slug}-{post.title}"
        else:
            if post.parent.title and post.parent.title != "":
                post_slug = f"{post_slug}-{post.parent.title}"
            else:
                post_slug = f"{post_slug}-{post.main_post.title}"
    else:
        post_slug = f"{post_slug}-{post.title}"
    if post_id:
        post_slug = f"{post_slug}-{post_id}"
    else:
        post_slug = f"{post_slug}-{post.post_id}"
    # print(post_slug)
    post_slug = slugify(post_slug)
    return post_slug


def fix_content(content):
    try:
        content_json = json.loads(content)
        if not content_json:
            return ""
        if "content" in content_json:
            content = content_json["content"]
    except Exception as ex:
        pass
    return content


def create_related_data(initial_data: dict, keys: list):
    related_data = {}
    for key in keys:
        if initial_data.get(key):
            related_data[key] = initial_data[key]
    return related_data


def sendPostInviteMail(invite):
    subject = "Unpod Thread Join Invitation"
    token_payload = {
        "email": invite.user_email,
        "invite_token": invite.invite_token,
        "invite_type": "post",
    }
    token = jwt_encode_handler(token_payload)
    link = f"{settings.BASE_FRONTEND_URL}/verify-invite?token={token}"
    html_message = get_post_invite_mail_body(
        link, invite.post.title, invite.invite_by.full_name, invite.valid_upto
    )
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [
        invite.user_email,
    ]

    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )


def addTaskToAgent(thread_id, query, content, request, post_type, space):
    if query == "No Title" and content:
        final_query = content
    else:
        final_query = query or ""
    block_type = "question"
    if post_type == "notebook":
        block_type = "notebook"
        final_query = content or query
        content = ""
    payload = {
        "event": "block",
        "data": {
            "block": "html",
            "block_type": block_type,
            "data": {"content": final_query, "context": content or ""},
        },
    }
    headers = {"Authorization": request.headers.get("Authorization")}
    if request.headers.get("AppType"):
        headers["AppType"] = request.headers.get("AppType")
    session_user = request.data.get("session_user")
    knowledge_bases = request.data.get("knowledge_bases", [])
    pilot = request.data.get("pilot")
    files = request.data.get("files", [])
    # focus = request.data.get("focus")
    if pilot:
        payload["pilot"] = pilot
    if files and len(files) > 0:
        payload["data"]["data"]["files"] = files
    payload["data"]["data"]["knowledge_bases"] = knowledge_bases
    payload["data"]["data"]["source"] = get_source(request)
    extra_data = create_related_data(request.data, ["focus", "data", "execution_type"])
    payload["data"]["data"].update(extra_data)
    # print(payload)
    # if focus:
    #     payload["data"]["data"]["focus"] = focus
    space_data = {
        "space_token": space.token,
        "org_token": space.space_organization.token,
        "org_id": space.space_organization.id,
    }
    payload["data"]["space"] = space_data
    query_params = {}
    if session_user:
        query_params = {"session_user": request.data.get("session_user")}
    url = f"{settings.API_SERVICE_URL}/conversation/{thread_id}/add_task/"
    print("addTaskToAgent payload", thread_id, payload, headers)
    res = requests.post(url, json=payload, headers=headers, params=query_params, timeout=30)
    print(res.json())
    return res
