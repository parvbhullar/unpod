import json
from libs.storage.postgres import executeQuery
from libs.core.security import verify_password_django
from libs.core.exceptions import APICommonException


def authenticate(email: str, password: str):
    user = executeQuery("SELECT * FROM users_user WHERE email=%s", (email,))
    if not user:
        return user
    verify = verify_password_django(password, user["password"])
    if not verify:
        raise APICommonException(
            json.dumps({"message": "Invalid credentials", "status_code": 401})
        )
    return user
