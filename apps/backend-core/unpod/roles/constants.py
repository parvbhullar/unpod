import json
import os

from unpod.common.enum import PermissionOperation

ROLES_FILEDS = ["role_name", "role_code", "role_type", "role_metadata"]

TAGS_FILEDS = ["name", "description", "icon", "tag_type", "slug"]

PERMISSION_DICT = {
    "space": [
        {"code": "public", "name": "Public"},
        {"code": "private", "name": "Private"},
        {"code": "shared", "name": "Shared"},
    ],
    "post": [
        {"code": "public", "name": "Public"},
        {"code": "private", "name": "Private"},
        {"code": "shared", "name": "Shared"},
        {"code": "link", "name": "Link"},
    ],
}

PROFILE_ROLES_FILEDS = ["role_name", "role_code", "department"]


tag_file = open(f"{os.path.dirname(__file__)}/tags.json", "r")
TAGS_DATA = json.load(tag_file)
tag_file.close()

GUEST_OPERATION = [
    PermissionOperation.view_detail.name,
    PermissionOperation.view_list.name,
]

VIEWER_OPERATION = [
    PermissionOperation.view_detail.name,
    PermissionOperation.view_list.name,
]

EDITOR_OPERATION = [
    *VIEWER_OPERATION,
    PermissionOperation.add.name,
    PermissionOperation.edit.name,
    PermissionOperation.delete.name,
    PermissionOperation.view_user_list.name,
    PermissionOperation.share_entity.name,
    PermissionOperation.privacy_update.name,
]
OWNER_OPERATION = [
    *EDITOR_OPERATION,
    PermissionOperation.transfer_ownership.name,
    PermissionOperation.archive.name,
]

ROLE_BASED_OPERATION_ORG = {
    "owner": OWNER_OPERATION,
    "editor": EDITOR_OPERATION,
    "viewer": VIEWER_OPERATION,
    "guest": GUEST_OPERATION,
}

ROLE_BASED_OPERATION_SPACE = {
    "owner": OWNER_OPERATION,
    "editor": EDITOR_OPERATION,
    "viewer": VIEWER_OPERATION,
    "guest": GUEST_OPERATION,
}

ROLE_BASED_OPERATION_POST = {
    "owner": [
        *OWNER_OPERATION,
        PermissionOperation.comment.name,
        PermissionOperation.use_superpilot.name,
        PermissionOperation.start_stream.name,
        PermissionOperation.end_stream.name,
    ],
    "editor": [
        *EDITOR_OPERATION,
        PermissionOperation.comment.name,
        PermissionOperation.use_superpilot.name,
        PermissionOperation.start_stream.name,
        PermissionOperation.end_stream.name,
    ],
    "viewer": [*VIEWER_OPERATION, PermissionOperation.comment.name],
    "guest": GUEST_OPERATION,
}

ROLE_BASED_OPERATION = {
    "organization": ROLE_BASED_OPERATION_ORG,
    "space": ROLE_BASED_OPERATION_SPACE,
    "post": ROLE_BASED_OPERATION_POST,
}


ROLE_BASED_INDEX = {"owner": 10, "editor": 9, "viewer": 8, "commentor": 8}

DEFAULT_SPACE_PERMISSION_ROLE = "guest"

DEFAULT_ORGANIZATION_PERMISSION_ROLE = "guest"

DEFAULT_PILOT_PERMISSION_ROLE = "guest"

DEFAULT_POST_PERMISSION_ROLE = "guest"
