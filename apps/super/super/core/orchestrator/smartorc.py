import logging
import re
from typing import Union, List, Any

from super.core.orchestrator.base import BaseOrc, HandlerType
from super.core.context.schema import Message, Context
from super.core.handler import BaseHandler, EchoHandler
from super.core.utils import JsonSerializableRegistry


class SmartOrc(BaseOrc, JsonSerializableRegistry):
    serializable_attributes = ["handlers", "transformers", "total_cost"]

    def __init__(
        self,
        context: Context = None,
        logger: logging.Logger = logging.getLogger(__name__),
        callback=None,
        session_id: str = None,
        **kwargs,
    ):
        BaseOrc.__init__(self, logger=logger, **kwargs)
        JsonSerializableRegistry.__init__(self)
        self._context = context or Context(session_id=session_id or "default")
        self.callback = callback
        self._validators = {}
        self.default_transformer = None

    def add_handler(self, handler, transformer=None, name=None):
        if name is None:
            name = re.sub(r"(?<!^)(?=[A-Z])", "_", handler.__class__.__name__).lower()
        else:
            name = name.lower().replace(" ", "_")
        super().add_handler(handler, transformer, name=name)

    async def add_validator(self, handler_type: HandlerType, validator) -> None:
        if handler_type not in self._validators:
            self._validators[handler_type] = []
        self._validators[handler_type].append(validator)

    async def validate_input(
        self, data: Union[str, Message], handler_type: HandlerType
    ) -> tuple[bool, str]:
        if handler_type not in self._validators:
            return True, ""

        if isinstance(data, str):
            data = Message.add_user_message(data)

        for validator in self._validators[handler_type]:
            try:
                is_valid, message = await validator(data)
                if not is_valid:
                    self.logger.warning(f"Validation failed: {message}")
                    return False, message
            except Exception as e:
                error_msg = f"Validator error: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg

        return True, ""

    async def execute(
        self, objective: Union[str, Message], **kwargs
    ) -> tuple[dict, Context]:
        if isinstance(objective, str):
            objective = Message.add_user_message(objective, kwargs)

        try:
            is_valid, error_message = await self.validate_input(
                objective, HandlerType.HANDLER
            )
            if not is_valid:
                return {
                    "status": "error",
                    "message": error_message,
                    "cost": self.total_cost,
                }, self._context

            self._context.add_message(objective)

            if self.current_planner():
                planner_valid, error = await self.validate_input(
                    objective, HandlerType.PLANNER
                )
                if planner_valid:
                    try:
                        await self.current_planner().execute(self._context, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Planner execution failed: {str(e)}")
                        return {
                            "status": "error",
                            "message": f"Planner execution failed: {str(e)}",
                            "cost": self.total_cost,
                        }, self._context

            handler = None
            transformer = None
            handler_name = "unknown"

            if (
                HandlerType.HANDLER in self.handlers
                and self.handlers[HandlerType.HANDLER]
            ):
                first_handler = self.handlers[HandlerType.HANDLER][0]
                handler_name = first_handler[0]
                handler = first_handler[1]
                transformer = self.transformers[HandlerType.HANDLER][0]
            else:
                handler = EchoHandler(logger=self.logger)
                self.add_handler(handler, name="echo_handler")
                handler_name = "echo_handler"
                handler, transformer = self.current_handler(handler_name)

            try:
                response = await handler.execute(objective.message, **kwargs)
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Handler execution failed: {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "handler": handler_name,
                    "cost": self.total_cost,
                }, self._context

            if transformer is not None and hasattr(transformer, "transform"):
                try:
                    response = await transformer.transform(response)
                except Exception as e:
                    error_msg = f"Transformer failed: {str(e)}"
                    self.logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": error_msg,
                        "handler": handler_name,
                        "cost": self.total_cost,
                    }, self._context

            structured_response = {
                "status": "success",
                "response": response,
                "handler": handler_name,
                "cost": self.total_cost,
                "handler_type": handler_name,
            }

            if self.callback:
                await self.callback(structured_response, self._context)

            return structured_response, self._context

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Orchestrator execution failed: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "handler": "unknown",
                "cost": self.total_cost,
            }, self._context

    async def _send_callback(self, message: Any):
        if self.callback:
            await self.callback(message)
