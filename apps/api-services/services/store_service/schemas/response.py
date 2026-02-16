from typing import List, TypeVar, Optional, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DynamicResponseBase(BaseModel):
    message: str


class DynamicResponseModel(DynamicResponseBase, Generic[T]):
    data: T


class DynamicResponseModelWithPagination(DynamicResponseBase, Generic[T]):
    count: Optional[int] = None
    data: List[T]
