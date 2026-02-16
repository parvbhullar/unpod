from typing import Union
from pydantic import BaseModel


class UserMe(BaseModel):
    user_id: Union[int, str]
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    user_token: str
