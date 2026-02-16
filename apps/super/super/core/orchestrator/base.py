from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import Any, Union, Optional

from super.core.handler import EchoHandler, BaseHandler
from super.core.memory.settings import MemoryProviders
from super.core.state.kv import KVState
from super.core.state.vector import VectorState


class HandlerType(Enum):
    HANDLER = "handler"
    PLANNER = "planner"
    COMMUNICATOR = "communicator"


class BaseOrc(ABC):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__), **kwargs):
        self.logger = logger
        self.handlers = {}
        self.transformers = {}
        self.total_cost = {}
        self.handler_relations = {}

    def add_handler(self, handler, transformer=None, name=None):
        """Adds a handler and an optional transformer to the chain."""
        handler_name = name or handler.name() or handler.__class__.__name__
        if handler_name in [n for n, h in self.handlers.get(HandlerType.HANDLER, [])]:
            raise ValueError(
                f"Handler names must be unique, but '{handler_name}' is already registered."
            )
        self._add(handler, transformer, HandlerType.HANDLER, handler_name)

    def _add(self, handler, transformer, handler_type, name=None):
        if handler_type not in self.handlers:
            self.handlers[handler_type] = [(name, handler)]
            self.transformers[handler_type] = [transformer or None]
        else:
            self.handlers[handler_type].append((name, handler))
            self.transformers[handler_type].append(transformer or None)

    def add_planner(self, planner, transformer=None, name=None):
        """Adds a planner and an optional transformer to the chain."""
        planner_name = name or planner.name or planner.__class__.__name__
        if planner_name in [n for n, p in self.handlers.get(HandlerType.PLANNER, [])]:
            raise ValueError(
                f"Planner names must be unique, but '{planner_name}' is already registered."
            )
        self._add(planner, transformer, HandlerType.PLANNER, planner_name)

    def current_planner(self, planner: BaseHandler = None) -> BaseHandler:
        if HandlerType.PLANNER not in self.handlers:
            return planner
        return self.handlers[HandlerType.PLANNER][-1][1]

    def current_handler(self, handler_name) -> BaseHandler:
        if HandlerType.HANDLER not in self.handlers:
            return EchoHandler(logger=self.logger)
        # TODO optimise this search
        for i, (name, handler) in enumerate(self.handlers[HandlerType.HANDLER]):
            if name == handler_name:
                return handler
        return None

    def get_handler_by_name(self, name: str) -> Optional[BaseHandler]:
        """Get a handler by its name."""
        for n, handler in self.handlers.get(HandlerType.HANDLER, []):
            if n == name:
                return handler
        return None

    def default_transformer(self, data, response, context):
        response = response.get("content", data)
        return response, context

    def add_handler_relation(
        self,
        handler1: Union[str, BaseHandler],
        handler2: Union[str, BaseHandler],
        relation_name: str = "default",
    ) -> "BaseOrc":
        """Add a relation between two handlers to define their interaction pattern."""
        h1_name = handler1 if isinstance(handler1, str) else handler1.__class__.__name__
        h2_name = handler2 if isinstance(handler2, str) else handler2.__class__.__name__

        if relation_name not in self.handler_relations:
            self.handler_relations[relation_name] = []

        self.handler_relations[relation_name].append((h1_name, h2_name))
        return self

    @abstractmethod
    async def execute(self, data, context, **kwargs):
        pass

    @abstractmethod
    async def _send_callback(self, message: Any):
        pass

    def remove_handler(self, handler_index):
        """
        Removes a handler from the chain.
        """
        self.handlers[HandlerType.HANDLER].pop(handler_index)
        self.transformers[HandlerType.HANDLER].pop(handler_index)

    def update_cost(cls, response):
        if hasattr(response, "total_cost"):
            total_cost = response.total_cost
            completion_tokens_used = response.completion_tokens_used
            prompt_tokens_used = response.prompt_tokens_used
            cls.total_cost["total_cost"] = (
                cls.total_cost.get("total_cost", 0) + total_cost
            )
            cls.total_cost["completion_tokens_used"] = (
                cls.total_cost.get("completion_tokens_used", 0) + completion_tokens_used
            )
            cls.total_cost["prompt_tokens_used"] = (
                cls.total_cost.get("prompt_tokens_used", 0) + prompt_tokens_used
            )

    def dump_handlers(self):
        handlers_dict = []
        if HandlerType.HANDLER in self.handlers:
            for name, handler in self.handlers[HandlerType.HANDLER]:
                handlers_dict.append(handler.dump())
        return handlers_dict
