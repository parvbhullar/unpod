import logging
from typing import Dict, List, Union, Optional
from datetime import datetime, timedelta
from contextlib import nullcontext

from super.core.callback.base import BaseCallback
from super.core.context.schema import Message
from super.core.context.unit_of_work import Task
from super.core.handler import BaseHandler
from super.core.handler.planner.schema import TaskPlan, TaskSchema, TaskStatus
from super.core.handler.strategy.base import PromptStrategy
from super.core.orchestrator import BaseOrc
from super.core.state.base import BaseState, State
from super.core.state.vector import VectorState
from super.core.handler.planner import DefaultPlanner



class SimpleOrc(BaseOrc):
    """
    SimpleOrc provides a structured way to orchestrate handlers that interact with each other
    and process tasks in a sequential manner.
    """

    def __init__(
        self,
        session_id: str,
        instructions: Union[str, List[str], PromptStrategy] = None,
        callback: BaseCallback = None,
        state: BaseState = None,
        logger: logging.Logger = logging.getLogger(__name__),
        **kwargs,
    ):
        """
        Initialize a SimpleOrc instance.

        Args:
            session_id (str): Unique identifier for this orchestration session
            instructions (Union[str, List[str], PromptStrategy]): Instructions or strategy for planning
            callback (BaseCallback): Callback for sending messages/updates
            state (BaseState): State management instance
            logger (Logger): Logger instance
        """
        if callback is None:
            from tests.mocks.callback import MockCallback

            self._callback = MockCallback()
        else:
            self._callback = callback

        super().__init__(logger, **kwargs)
        self._session_id = session_id
        self.state = state or State()
        self._context = None
        self._instructions = instructions

        # Initialize task manager
        from super.core.orchestrator.tasks.manager import TaskManager

        self.task_manager = TaskManager()

        # Handler management
        self.handlers: Dict[str, BaseHandler] = {}

        # Load planner based on instructions
        self._planner = self._load_planner(instructions)

    def _load_planner(self, instructions) -> DefaultPlanner:
        """Load planner based on instructions."""
        if isinstance(instructions, PromptStrategy):
            return DefaultPlanner(strategy=instructions, logger=self.logger)
        elif instructions:
            return DefaultPlanner(instructions=instructions, logger=self.logger)
        return DefaultPlanner(logger=self.logger)

    async def _send_callback(self, message: Message):
        """Send a message through the callback if one is configured."""
        if self._callback and message:
            print(f"Sending message: {message.message}")
            await self._callback.send(message)
            self.logger.info(f"Callback sent: {message.message}")

    async def observe(self, objective: Union[str, Message], context=None, **kwargs):
        """
        Observe and plan tasks for the given objective.

        Args:
            objective: The objective to analyze
            context: The current context
            **kwargs: Additional arguments

        Returns:
            Message: Response containing analysis and planned tasks
        """
        # Initialize context if needed
        if not context:
            context = await self.state.load() or State().load()

        # Convert string objective to Message
        if isinstance(objective, str):
            objective = Message.add_user_message(objective)

        self.logger.info(f"[OBSERVER] Planning for objective: {objective.message}")

        # Generate task plan using planner
        planning_result = await self._planner.execute(
            objective.message, context=context, session_id=self._session_id, **kwargs
        )

        # Create tasks from plan
        if "task_plan" in planning_result:
            for task_dict in planning_result["task_plan"].get("tasks", []):
                task = Task.create(
                    objective=task_dict["objective"],
                    function_name=task_dict.get("function_name"),
                    status=TaskStatus.BACKLOG,
                )
                self.task_manager.add_task(task)

        # Create response message
        response = Message.add_assistant_message(
            f"Planning complete. Created {len(self.task_manager.get_tasks_by_status(TaskStatus.BACKLOG))} tasks."
        )

        # Update context
        context.add_message(objective)
        context.add_message(response)
        await self.state.save(context)

        return response

    async def execute_next_task(self) -> Optional[Message]:
        """Execute the next ready task using appropriate handler."""
        ready_tasks = self.task_manager.get_ready_tasks()
        if not ready_tasks:
            return None

        task = ready_tasks[0]
        handler = self.handlers.get(task.function_name)

        if not handler:
            self.logger.warning(f"No handler found for task: {task.objective}")
            return None

        try:
            # Update task status
            self.task_manager.update_status(task.id, TaskStatus.IN_PROGRESS)

            # Execute task with handler
            result = await handler.execute(task.objective)

            # Store result in state
            if isinstance(self.state, VectorState):
                await self.state.add(
                    {
                        "text": str(result),
                        "type": "task_result",
                        "task_id": task.id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ref_id=self._session_id,
                )

            # Update task status
            self.task_manager.update_status(task.id, TaskStatus.COMPLETED)

            return Message.add_assistant_message(f"Completed task: {task.objective}")

        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            self.task_manager.update_status(task.id, TaskStatus.FAILED)
            return Message.add_error_message(f"Failed to execute task: {str(e)}")

    async def handle_clarification(
        self, response: Message, ability_args: dict, **kwargs
    ) -> bool:
        """
        Handle clarifying questions as part of the feedback loop.

        Args:
            response: The AI response message containing the clarification
            ability_args: Arguments containing the clarifying question
            **kwargs: Additional arguments

        Returns:
            bool: True if execution should hold for user response, False otherwise
        """
        # 1. User/System layer - Create question message
        question = ability_args.get("clarifying_question")
        if not question:
            return False

        question_message = Message.add_question_message(message=question)

        # 2. Observers/Logging layer
        self.logger.info(
            f"[OBSERVER] Clarification needed for session {self._session_id}"
        )
        self.logger.info(f"[OBSERVER] Question: {question}")

        # 3. Flow Manager layer - Add clarification event
        flow = get_flow()
        if flow:
            clarification_event = Event(
                event="clarification_request", thread_id=self._session_id
            )
            flow.add_events([clarification_event])
            self.logger.info(
                f"[OBSERVER] Added clarification event to flow: {clarification_event}"
            )

        # 4. Memory Layer - Store clarification request
        if isinstance(self.state, VectorState):
            await self.state.add(
                {
                    "text": question,
                    "type": "clarification_request",
                    "timestamp": datetime.now().isoformat(),
                    "response_id": response.id if hasattr(response, "id") else None,
                },
                ref_id=self._session_id,
            )

        # Load or initialize context if needed
        if not self._context:
            self._context = await self.state.load()
            if not self._context:
                from super.core.context.schema import Context

                self._context = Context(session_id=self._session_id)

        # Add to context
        self._context.add_message(question_message)
        await self.state.save(self._context)

        # Send through callback if available
        await self._send_callback(question_message)

        # Return True to indicate execution should hold for user response
        return True

    async def execute(self, objective: Union[str, Message], **kwargs):
        """
        Execute the orchestration for given objective.

        Args:
            objective: The objective to achieve, either as string or Message
            **kwargs: Additional arguments
        """
        if not self._context:
            self._context = await self.state.load()

        self.logger.info(
            f"Processing message for session {self._session_id}, Message: {objective}"
        )
        await self._send_callback(Message.add_notification("Processing message..."))

        if isinstance(objective, str):
            objective = Message.add_user_message(objective)
        self._context.add_message(objective)
        self._context.interaction = False
        kwargs.pop("context", None)
        # Observe and plan
        while True:
            observation_response = await self.observe(
                objective, self._context, **kwargs
            )
            # Parse observation response into TaskPlan structure
            message_parts = observation_response.message.split("\n")
            ability_args = {"current_status": TaskStatus.IN_PROGRESS, "tasks": []}

            # Extract tasks from reasoning and next steps
            current_task = None
            for line in message_parts:
                if line.startswith("Reasoning:"):
                    reasoning = line.replace("Reasoning:", "").strip()
                    current_task = {
                        "objective": reasoning,
                        "type": "plan",
                        "priority": 1,
                        "ready_criteria": ["Reasoning complete"],
                        "acceptance_criteria": ["Valid reasoning provided"],
                        "status": TaskStatus.IN_PROGRESS,
                        "function_name": "planner",
                        "motivation": "Initial analysis",
                        "self_criticism": "May need refinement",
                        "reasoning": reasoning,
                    }
                    ability_args["tasks"].append(current_task)
                elif line.startswith("Next steps:"):
                    steps = line.replace("Next steps:", "").strip().split(",")
                    for i, step in enumerate(steps):
                        task = {
                            "objective": step.strip(),
                            "type": "task",
                            "priority": i + 1,
                            "ready_criteria": ["Previous step complete"],
                            "acceptance_criteria": ["Step validated"],
                            "status": TaskStatus.BACKLOG,
                            "function_name": "executor",
                            "motivation": "Required step",
                            "self_criticism": "May need clarification",
                            "reasoning": "Sequential execution required",
                        }
                        ability_args["tasks"].append(task)
                elif "Clarifying question:" in line:
                    ability_args["clarifying_question"] = line.replace(
                        "Clarifying question:", ""
                    ).strip()

            if ability_args.get("clarifying_question"):
                hold = await self.handle_clarification(
                    observation_response, ability_args, **kwargs
                )
                if hold:
                    self._context.interaction = True
                    return
            else:
                await self._process_observation(
                    objective, observation_response, ability_args, **kwargs
                )
                break
        return self._context

    async def _process_observation(
        self, objective, observation_response, ability_args, **kwargs
    ):
        """Process the observation and create execution plan."""
        try:
            # Convert dict tasks to TaskSchema objects
            task_schemas = []
            for task_dict in ability_args.get("tasks", []):
                task_schemas.append(TaskSchema(**task_dict))
            ability_args["tasks"] = task_schemas

            observation = TaskPlan(**ability_args)
            if not observation:
                raise Exception("Either observation or observer is not defined")

            await self._callback.send(observation, **kwargs)

            planning_message = Message.add_planning_message(
                f'Task Breakdown of "{objective.message}":\n'
                + "\n".join(
                    [
                        f"'{task.objective}' will be done by {task.function_name} handler"
                        for task in observation.tasks
                    ]
                )
            )
            self._context.add_message(planning_message)
        except Exception as e:
            self.logger.error(f"Error processing observation: {str(e)}")
            raise

        if not self.task:
            self.task = Task.create(objective=objective.message)
            self._context.tasks.append(self.task)

        self.task.add_plan(observation.tasks)

    def advance_time(self, delta: timedelta):
        """Advance the current datetime by the specified delta."""
        self.current_datetime += delta

    async def run_steps(
        self, steps: int, timedelta_per_step: Optional[timedelta] = None
    ):
        """Run the orchestration for a specified number of steps."""
        for _ in range(steps):
            await self.execute(self._current_task)
            if timedelta_per_step:
                self.advance_time(timedelta_per_step)

    async def skip_steps(
        self, steps: int, timedelta_per_step: Optional[timedelta] = None
    ):
        """Skip a specified number of steps without executing tasks."""
        if timedelta_per_step:
            self.advance_time(steps * timedelta_per_step)

    @staticmethod
    def add_orchestrator(orchestrator: "SimpleOrc"):
        """Register an orchestrator instance."""
        if orchestrator._session_id in SimpleOrc.all_orchestrators:
            raise ValueError(
                f"Session ID must be unique, but '{orchestrator._session_id}' already exists."
            )
        SimpleOrc.all_orchestrators[orchestrator._session_id] = orchestrator

    @staticmethod
    def get_orchestrator_by_session(session_id: str) -> Optional["SimpleOrc"]:
        """Get an orchestrator by its session ID."""
        return SimpleOrc.all_orchestrators.get(session_id)

    @staticmethod
    def clear_orchestrators():
        """Clear all registered orchestrators."""
        SimpleOrc.all_orchestrators = {}
