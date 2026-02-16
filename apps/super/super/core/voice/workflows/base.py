from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseWorkflow(ABC):
    """
    Base abstract class for workflow implementations.

    This class provides a common interface for all workflow types,
    ensuring consistent initialization and execution patterns.
    """

    def __init__(self,agent:str, model_config: Optional[Dict[str, Any]] = None, user_state: Any = None, transcript: Any = None,token:str =None):
        """
        Initialize the workflow with configuration and state.

        Args:
            model_config: Configuration dictionary for the workflow
            user_state: Current state of the user/session
        """
        self.model_config = model_config if model_config else (
            user_state.model_config if user_state and hasattr(user_state, 'model_config') else {}
        )
        self.token = token if token else (self.model_config.get('space_token') if self.model_config else None)
        self.transcript = user_state.transcript if user_state and hasattr(user_state, 'transcript') else transcript
        self.user_state = user_state
        self.agent = agent

    @abstractmethod
    async def execute(self) -> Any:
        """
        Execute the workflow.

        This method should be implemented by subclasses to define
        the main workflow execution logic.

        Returns:
            Any: The result of the workflow execution
        """
        pass

