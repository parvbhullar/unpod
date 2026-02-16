import enum
from typing import List, Any
import logging
import platform
from abc import ABC, abstractmethod

from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.context.schema import Message
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)
from super.core.plugin.base import PluginLocation, PluginStorageFormat
import distro

from super.core.voice.base import BaseVoiceHandler


class SimpleVoiceHandler(BaseVoiceHandler, ABC):
    """A class representing a handler step."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.base.SimpleVoiceHandler",
        ),
        role=RoleConfiguration(
            name="voice_handler",
            role=("A handler to handle voice conversations."),
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        session_id: str = None,
        callback: BaseCallback = None,
        model_config: BaseModelConfig = None,
        configuration: HandlerConfiguration = default_configuration,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        super().__init__(
            session_id=session_id,
            callback=callback,
            configuration=configuration,
            logger=logger
        )
        self._session_id = session_id
        self._callback = callback
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._model_config = model_config


    @abstractmethod
    async def execute(self, objective: str | Message, *args, **kwargs) -> Any:
        """Execute the handler step."""
        ...

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.role.id

    def dump(self) -> dict:
        role_config = self._configuration.role
        dump = {
            "id": role_config.id,
            "name": role_config.name,
            "role": role_config.role,
        }
        return dump


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info
