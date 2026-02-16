import logging
from typing import List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from super.core.handler.base import BaseHandler
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)
from super.core.handler.planner.schema import TaskPlan, TaskSchema, TaskStatus
from super.core.handler.planner.strategies.planning_strategy import PlanningStrategy
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.resource.llm.schema import LanguageModelClassification


class PlanRequest(BaseModel):
    """Request model for planning tasks."""

    objective: str = Field(..., description="The objective to plan tasks for")
    context: Optional[dict] = Field(
        default=None, description="Additional context for planning"
    )
    instructions: Optional[str] = Field(
        default=None, description="Custom instructions for planning"
    )


class PlanResponse(BaseModel):
    """Response model for planned tasks."""

    tasks: List[TaskSchema] = Field(..., description="List of planned tasks")
    reasoning: str = Field(..., description="Reasoning behind the task breakdown")
    needs_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )
    clarifying_question: Optional[str] = Field(
        default=None, description="Question to clarify the objective"
    )


class SimplePlanHandler(BaseHandler):
    """A handler that plans tasks using AI-based planning strategy."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.handler.planner.SimplePlanHandler",
        ),
        role=RoleConfiguration(
            name="plan_handler",
            role="A handler to plan tasks based on given objectives.",
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        prompt_strategy=PlanningStrategy.default_configuration,
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        configuration: HandlerConfiguration = default_configuration,
        logger: logging.Logger = logging.getLogger(__name__),
        session_id: str = None,
        instructions: Optional[str] = None,
    ) -> None:
        """Initialize the SimplePlanHandler.

        Args:
            configuration: Handler configuration
            logger: Logger instance
            session_id: Session identifier
            instructions: Custom planning instructions
        """
        self._logger = logger
        self._configuration = configuration
        self._session_id = session_id
        self._instructions = instructions
        self._strategy = self._initialize_strategy()

    def _initialize_strategy(self) -> PlanningStrategy:
        """Initialize the planning strategy with custom configuration."""
        strategy_config = self._configuration.prompt_strategy.copy()

        if self._instructions:
            # Update system prompt with custom instructions
            strategy_config.system_prompt = (
                f"{self._instructions}\n\n" f"{strategy_config.system_prompt}"
            )

        strategy_config.model_classification = LanguageModelClassification.SMART_MODEL
        return PlanningStrategy(configuration=strategy_config)

    async def execute(self, objective: str, *args, **kwargs) -> Any:
        """Execute the planning process for given objective.

        Args:
            objective: The objective to plan tasks for
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            dict: Planning result containing tasks and metadata
        """
        self._logger.info(f"Planning tasks for objective: {objective}")

        # Create plan request
        request = PlanRequest(
            objective=objective,
            context=kwargs.get("context"),
            instructions=self._instructions,
        )

        try:
            # Generate plan using strategy
            plan_result = await self._strategy(
                request.objective,
                context=request.context,
                session_id=self._session_id,
                **kwargs,
            )

            # Parse response
            response = PlanResponse(
                tasks=[
                    TaskSchema(
                        objective=task.get("objective"),
                        type=task.get("type", "task"),
                        priority=task.get("priority", 1),
                        ready_criteria=task.get("ready_criteria", ["Task is ready"]),
                        acceptance_criteria=task.get(
                            "acceptance_criteria", ["Task is complete"]
                        ),
                        status=TaskStatus.BACKLOG,
                        function_name=task.get("function_name", "default_handler"),
                        motivation=task.get("motivation", "Required for objective"),
                        self_criticism=task.get(
                            "self_criticism", "May need refinement"
                        ),
                        reasoning=task.get(
                            "reasoning", "Based on objective requirements"
                        ),
                    )
                    for task in plan_result.get("task_plan", {}).get("tasks", [])
                ],
                reasoning=plan_result.get("reasoning", "Task breakdown complete"),
                needs_clarification=plan_result.get("needs_clarification", False),
                clarifying_question=plan_result.get("clarifying_question"),
            )

            # Return planning result
            return {
                "task_plan": {
                    "current_status": TaskStatus.IN_PROGRESS,
                    "tasks": response.tasks,
                },
                "reasoning": response.reasoning,
                "needs_clarification": response.needs_clarification,
                "clarifying_question": response.clarifying_question,
            }

        except Exception as e:
            self._logger.error(f"Error during planning: {str(e)}")
            raise

    def __repr__(self):
        return f"{self.__class__.__name__}(session_id={self._session_id})"

    def dump(self) -> dict:
        """Dump handler configuration."""
        role_config = self._configuration.role
        return {
            "id": role_config.id,
            "name": role_config.name,
            "role": role_config.role,
            "instructions": self._instructions,
        }
