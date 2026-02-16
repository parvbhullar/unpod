DEFAULT_SPACE_ROLES = [
    {"role_code": "owner", "role_name": "Owner"},
    {"role_code": "editor", "role_name": "Editor"},
    {"role_code": "viewer", "role_name": "Viewer"},
]

SPACE_LIST_ALL = [
    "name",
    "token",
    "slug",
    "privacy_type",
    "created_by",
    "space_type",
    "content_type",
    "description",
]


SPACE_LIST_FIELDS = [*SPACE_LIST_ALL, "description"]

SPACE_ALL_TOKEN = "SPACE1234W48WASLGHQV0ALL"

SPACE_HOME_TOKEN = "SPACEHOMEW48WASLGHQV0789"

DEFAULT_SPACES = ["general"]

# DEFAULT_SPACES =  ['events', 'blogs', 'videos', 'podcasts', 'general']

CONTACT_SPACE_DEFAULT_SCHEMA = {
    "type": "object",
    "required": ["name", "about", "email", "address", "occupation", "contact_number"],
    "properties": {
        "name": {
            "type": "text",
            "title": "Name",
            "description": "Contact Name",
            "defaultValue": "",
        },
        "about": {
            "type": "textarea",
            "title": "About",
            "description": "",
            "defaultValue": "",
        },
        "email": {
            "type": "email",
            "title": "email",
            "description": "",
            "defaultValue": "",
        },
        "address": {
            "type": "text",
            "title": "Address",
            "description": "",
            "defaultValue": "",
        },
        "occupation": {
            "type": "text",
            "title": "Occupation",
            "description": "",
            "defaultValue": "",
        },
        "company_name": {
            "type": "text",
            "title": "Company Name",
            "description": "",
            "defaultValue": "",
        },
        "contact_number": {
            "type": "phone",
            "title": "Contact Number",
            "description": "",
            "defaultValue": "",
        },
        "alternate_number": {
            "type": "number",
            "title": "Alternate Contact Number",
            "description": "Alter number",
            "defaultValue": "",
        },
    },
}
