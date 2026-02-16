DEFAULT_THREAD_ROLES = [
    {"role_code": "owner", "role_name": "Owner"},
    {"role_code": "editor", "role_name": "Editor"},
    {"role_code": "viewer", "role_name": "Viewer"},
    {"role_code": "commentor", "role_name": "Commentor"},
]


DEFAULT_POST_ROLES = [
    {"role_code": "owner", "role_name": "Owner"},
    {"role_code": "editor", "role_name": "Editor"},
    {"role_code": "viewer", "role_name": "Viewer"},
    {"role_code": "commentor", "role_name": "Commentor"},
]


THREAD_LIST_FIELDS = [
    "title",
    "description",
    "privacy_type",
    "slug",
    "user",
    "post_id",
    "tags",
    "created",
    "seq_number",
    "post_rel",
    "space",
    "post_count",
    "reply_count",
    "reaction_count",
    "view_count",
    "media_data",
    "is_live",
    "post_type",
    "content_type",
    "post_status",
    "block",
    "ref_doc_id",
]


THREAD_POST_LIST_FIELDS = [*THREAD_LIST_FIELDS, "content"]

THREAD_DETAIL_FIELDS = [*THREAD_LIST_FIELDS, "content", "users", "related_data"]

THREAD_POST_REPLY_FIELDS = [
    "title",
    "description",
    "content",
    "slug",
    "user",
    "created",
    "seq_number",
    "post_rel",
    "space",
    "reply_count",
    "reaction_count",
    "view_count",
    "privacy_type",
]
