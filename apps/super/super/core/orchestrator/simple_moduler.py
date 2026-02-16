from dataclasses import dataclass
from typing import Union, Optional, Tuple, Any
import logging
from abc import ABC, abstractmethod

from super.core.block.execution.simple import SimpleExecutor
from super.core.callback.base import BaseCallback
from super.core.context.schema import Message, Context
from super.core.context.unit_of_work import Task, UnitOfWork
from super.core.handler.planner.schema import TaskStatus
from super.core.orchestrator.base import BaseOrc
from super.core.resource.model_providers.schema import LanguageModelResponse
from super.core.state.base import BaseState, State


@dataclass
class ExecutionContext:
    """Holds the execution context for a task"""

    objective: Union[str, Message, Task]
    context: Context
    task: Optional[Task] = None
    interaction_required: bool = False


class ObjectiveHandler(ABC):
    """Base class for handling different types of objectives"""

    @abstractmethod
    async def handle(self, context: ExecutionContext) -> ExecutionContext:
        pass


class StringObjectiveHandler(ObjectiveHandler):
    async def handle(self, context: ExecutionContext) -> ExecutionContext:
        context.objective = Message.add_user_message(context.objective)
        return context


class MessageObjectiveHandler(ObjectiveHandler):
    async def handle(self, context: ExecutionContext) -> ExecutionContext:
        context.context.add_message(context.objective)
        return context


class TaskObjectiveHandler(ObjectiveHandler):
    async def handle(self, context: ExecutionContext) -> ExecutionContext:
        context.task = context.objective
        return context


class TaskManager:
    """Manages task creation and retrieval"""

    @staticmethod
    async def get_or_create_task(context: ExecutionContext) -> Task:
        if not context.task:
            current_task = context.context.current_task
            if not current_task:
                if isinstance(context.objective, Message):
                    message = context.objective.message
                else:
                    message = str(context.objective)
                task = Task.factory(message)
                context.context.tasks.append(task)
            else:
                task = current_task
            return task
        return context.task


class TaskPlanner:
    """Handles task planning and observation"""

    def __init__(self, callback: BaseCallback):
        self.callback = callback

    async def plan_task(self, context: ExecutionContext, **kwargs) -> ExecutionContext:
        if not context.task.plan:
            if context.task.status == TaskStatus.BACKLOG:
                self._add_task_start_message(context)
            context.task.status = TaskStatus.IN_PROGRESS
            observation = await self._get_observation(context, **kwargs)
            if observation:
                context.task.add_plan(observation.get_tasks())
        return context

    def _add_task_start_message(self, context: ExecutionContext):
        message = Message.add_task_start_message(
            f"Starting Task: '{context.task.objective}'"
        )
        context.context.add_message(message)

    async def _get_observation(
        self, context: ExecutionContext, **kwargs
    ) -> Optional[Any]:
        await self.callback.on_observation_start(**kwargs)
        observation_response = await self._observe(context, **kwargs)
        ability_args = observation_response.content.get("function_arguments", {})

        if ability_args.get("clarifying_question"):
            if await self._handle_clarification(
                context, observation_response, ability_args, **kwargs
            ):
                context.interaction_required = True
                return None

        observation = self._create_observation(ability_args)
        await self._process_observation(context, observation, **kwargs)
        return observation

    @staticmethod
    async def _observe(context: ExecutionContext, **kwargs) -> LanguageModelResponse:
        # Implementation of observe method
        pass

    @staticmethod
    async def _handle_clarification(
        context: ExecutionContext, response: Any, args: dict, **kwargs
    ) -> bool:
        # Implementation of clarification handling
        pass

    @staticmethod
    def _create_observation(ability_args: dict) -> Any:
        return Observation(**ability_args)

    async def _process_observation(
        self, context: ExecutionContext, observation: Any, **kwargs
    ):
        await self.callback.on_observation(observation, **kwargs)
        self._add_planning_message(context, observation)

    @staticmethod
    def _add_planning_message(context: ExecutionContext, observation: Any):
        message = Message.add_planning_message(
            f'Pilot level Task Breakdown of "{context.task.objective}":\n'
            + "\n".join(
                [
                    f"'{t.objective}' will be done by {t.function_name} pilot"
                    for t in observation.tasks
                ]
            )
        )
        context.context.add_message(message)


class TaskExecutor:
    """Handles task execution"""

    def __init__(self, callback: BaseCallback):
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    async def execute_task(
        self, context: ExecutionContext, **kwargs
    ) -> ExecutionContext:
        while context.task.active_task_idx < len(context.task.plan):
            await self._execute_step(context, **kwargs)
            if context.interaction_required:
                break

        if self._is_task_complete(context):
            await self._complete_task(context, **kwargs)

        return context

    async def _execute_step(self, context: ExecutionContext, **kwargs):
        current_task = context.task.current_sub_task
        if current_task.status != TaskStatus.DONE:
            handler, transformer = self._get_handler(current_task.function_name)
            if handler:
                await self._execute_handler(context, handler, transformer, **kwargs)
            else:
                self.logger.error(
                    f"Handler named '{current_task.function_name}' is not defined"
                )
                context.task.active_task_idx += 1

    def _get_handler(self, function_name: str) -> Tuple[Any, Any]:
        # Implementation of handler retrieval
        pass

    async def _execute_handler(
        self, context: ExecutionContext, handler: Any, transformer: Any, **kwargs
    ):
        try:
            if hasattr(handler, "execute"):
                response = await handler.execute(**kwargs)
            else:
                response = await handler(**kwargs)

            if transformer:
                response = await transformer.transform(response)

            if not context.interaction_required:
                context.task.current_sub_task.status = TaskStatus.DONE
                context.task.active_task_idx += 1

        except Exception as e:
            self.logger.error(f"Error executing handler: {str(e)}")
            raise

    @staticmethod
    def _is_task_complete(context: ExecutionContext) -> bool:
        return context.task.active_task_idx == len(context.task.plan)

    async def _complete_task(self, context: ExecutionContext, **kwargs):
        context.context.current_task.status = TaskStatus.DONE
        message = Message.add_task_end_message(
            f"Task Completed: '{context.task.objective}'"
        )
        context.context.add_message(message)
        await self.callback.on_chain_complete(**kwargs)


class SimpleOrc(BaseOrc):
    """Main orchestrator class implementing the flowchart logic"""

    def __init__(
        self,
        session_id: str,
        callback: BaseCallback = None,
        state: BaseState = None,
        logger: logging.Logger = logging.getLogger(__name__),
        **kwargs,
    ):
        super().__init__(logger, **kwargs)
        self._session_id = session_id
        self._callback = callback
        self.state = state or State()
        self._context = None

        # Initialize components
        self.task_manager = TaskManager()
        self.task_planner = TaskPlanner(callback)
        self.task_executor = TaskExecutor(callback)

        # Initialize objective handlers
        self.objective_handlers = {
            str: StringObjectiveHandler(),
            Message: MessageObjectiveHandler(),
            Task: TaskObjectiveHandler(),
        }

    async def execute(self, objective: Union[str, Message, Task], **kwargs):
        """Main execution flow following the flowchart"""
        try:
            # Create execution context
            context = ExecutionContext(objective=objective, context=self._context)

            # Handle objective based on type
            handler = self.objective_handlers.get(type(objective))
            if handler:
                context = await handler.handle(context)

            # Get or create task
            context.task = await self.task_manager.get_or_create_task(context)

            # Plan task if needed
            context = await self.task_planner.plan_task(context, **kwargs)
            if context.interaction_required:
                return

            # Execute task
            context = await self.task_executor.execute_task(context, **kwargs)

        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}")
            raise
