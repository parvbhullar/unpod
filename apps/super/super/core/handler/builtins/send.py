import enum
from typing import List, Any
import logging
import platform
from abc import ABC

from super.core.callback.base import BaseCallback
# from controlflow.cli.main import callback
from super.core.context.schema import Message
from super.core.handler.base import BaseHandler
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)
from super.core.plugin.base import PluginLocation, PluginStorageFormat
import distro


class SendToUserHandler(BaseHandler, ABC):
    """A class representing a handler step."""

    default_role_config = RoleConfiguration(
        id="respond_to_user",
        name="respond_to_user",
        role="An handler which respond to the user from response.",
        cycle_count=0,
        max_task_cycle_count=3,
    )

    def __init__(
        self,
        role_config: RoleConfiguration = default_role_config,
        callback: BaseCallback = None,
        logger: logging.Logger = logging.getLogger(__name__),
        session_id: str = None,
    ) -> None:
        self._role = role_config
        self._session_id = session_id
        self._logger = logger
        self._callback = callback

    async def execute(self, objective: str | Message, *args, **kwargs) -> Any:
        self._logger.info(f"Echoing {self.name()} with objective: {objective}")
        callback = self._callback or kwargs.get("callback", None)
        if callback:
            callback.send(objective)
        else:
            self._logger.info(
                "No callback found to send the message. Ignoring the message."
            )

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def name(self) -> str:
        """The name of the ability."""
        return self._role.name

    def dump(self) -> dict:
        role_config = self._role
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
