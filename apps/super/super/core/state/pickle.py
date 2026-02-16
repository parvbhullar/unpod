import logging
import pickle

from super.core.context.schema import Context
from super.core.state.base import BaseState
from super.core.workspace import Workspace


class PickleState(BaseState):
    def __init__(
        self,
        session_id: str,
        workspace: Workspace,
        logger: logging.Logger = logging.getLogger(__name__),
        *args,
        **kwargs,
    ):
        super().__init__(logger, *args, **kwargs)
        self._session_id = session_id
        self._workspace = workspace

    async def save(self, context: Context) -> None:
        state_file_path = self._workspace.get_path(f"{self._session_id}_state.pkl")
        with open(state_file_path, "wb") as file:
            pickle.dump(context, file)

    async def load(self) -> Context:
        state = Context(session_id=self._session_id)
        state_file_path = self._workspace.get_path(f"{self._session_id}_state.pkl")
        if state_file_path.exists():
            with open(state_file_path, "rb") as file:
                state = pickle.load(file)
        return state
