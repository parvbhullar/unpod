import abc
import os
from dataclasses import dataclass
from typing import Dict, Any

import inflection

from super.core.utils import read_yaml, import_module


@dataclass
class HandlerEntry:
    name: str
    alias: str
    module: type
    intro: str

    @staticmethod
    def from_yaml_file(file_path: str):
        data = read_yaml(file_path)
        name = os.path.basename(file_path).split(".")[
            0
        ]  # set role name as YAML file name without extension
        module_path, class_name = data["module"].rsplit(".", 1)
        module = import_module(module_path)
        cls = getattr(module, class_name)
        return HandlerEntry(
            name=name,
            alias=data["alias"],
            module=cls,
            intro=data["intro"],
        )


class BaseHandler(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs):
    #     ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The name of the ability."""
        return inflection.underscore(self.__name__)

    @property
    @abc.abstractmethod
    def dump(self) -> Dict[str, Any]:
        ...
