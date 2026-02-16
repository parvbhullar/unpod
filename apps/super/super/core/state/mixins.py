import abc


class StateMixin(abc.ABC):
    @abc.abstractmethod
    async def to_state(self) -> dict:
        ...

    @abc.abstractmethod
    async def from_state(self, state: dict) -> None:
        ...


class DictStateMixin(abc.ABC):
    @abc.abstractmethod
    async def to_dict_state(self) -> dict:
        ...

    @abc.abstractmethod
    async def from_dict_state(self, state: dict) -> None:
        ...


class PickleStateMixin(abc.ABC):
    @abc.abstractmethod
    async def to_pickle_state(self) -> dict:
        ...

    @abc.abstractmethod
    async def from_pickle_state(self, state: dict) -> None:
        ...
