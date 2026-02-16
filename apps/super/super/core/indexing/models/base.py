import abc
from typing import Any


class BaseModel:
    @abc.abstractmethod
    def get_model(self, model_name: str) -> Any:
        raise NotImplementedError