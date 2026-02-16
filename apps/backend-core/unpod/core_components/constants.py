import json
import os

PROFILEROLES = [
    {
        "role_name": "Developer",
        "role_code": "developer",
        "parent_role": "Engineer",
        "department": "Engineering",
    },
    {
        "role_name": "Designer",
        "role_code": "designer",
        "parent_role": "Engineer",
        "department": "Engineering",
    },
    {
        "role_name": "Investor",
        "role_code": "investor",
        "parent_role": "Investor",
        "department": "Investor",
    },
    {
        "role_name": "Engineer",
        "role_code": "engineer",
        "parent_role": "Engineer",
        "department": "Engineering",
    },
]


def updatePrfileRoles(role_data):
    from django.utils.text import slugify

    roles = role_data["roles"]
    for role in roles:
        PROFILEROLES.append(
            {
                "role_name": role["Role"],
                "role_code": slugify(role["Role"]),
                "parent_role": role["ParentRole"],
                "department": role["Department"],
            }
        )


role_file = open(f"{os.path.dirname(__file__)}/roles.json", "r")
role_data = json.load(role_file)
updatePrfileRoles(role_data)
role_file.close()


EVALS_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "title": "Question"},
        "answer": {"type": "string", "title": "Answer"},
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "title": "Keywords",
            "default": [],
        },
        "status": {"type": "string", "title": "Status", "default": "active"},
        "batch_id": {
            "type": {"type": "string", "title": "Batch Id"},
            "default": None,
            "title": "Batch Id",
        },
    },
    "required": ["question", "answer"],
}
