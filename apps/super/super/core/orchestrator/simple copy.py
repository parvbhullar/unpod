import logging
from typing import Union

from super.core.block.execution.simple import SimpleExecutor
from super.core.callback.base import BaseCallback
from super.core.context.schema import Message, Context
from super.core.context.unit_of_work import Task
from super.core.handler.config import RoleConfiguration
from super.core.handler.planner.schema import TaskStatus, TaskPlan
from super.core.handler.planner.strategies.planning_strategy import PlanningStrategy
from super.core.handler.simple import SimpleHandler
from super.core.orchestrator.base import BaseOrc
from super.core.resource.model_providers import AIModelName
from super.core.resource.model_providers.schema import LanguageModelResponse
from super.core.state.base import BaseState, State


class SimpleOrc(BaseOrc):
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

    async def _send_callback(self, message: Message):
        if self._callback:
            self._callback.send(message)

    # TODO add files and data and additional kwargs
    async def execute(self, objective: Union[str, Message], **kwargs):
        if not self._context:
            self._context = await self.state.load()

        print(
            f"Processing message for session {self._session_id}, Message: {objective}"
        )
        await self._send_callback(Message.add_notification("Processing message..."))

        if isinstance(objective, str):
            objective = Message.add_user_message(objective)
        self._context.add_message(objective)
        self._context.interaction = False

        # TODO: user message bhejega to uss time pe new task banne se kese roke?
        # if not self.task:
        #     task = self._context.current_task
        #     if not task:
        #         self.task = Task.factory(objective.message)
        #         self._context.tasks.append(self.task)
        #     else:
        #         self.task = task
        #
        # if not self.task.plan:
        #     if self.task.status == TaskStatus.BACKLOG:
        #         task_start_message = Message.add_task_start_message(f"Starting Task: '{objective.message}'")
        #         self._context.add_message(task_start_message)
        #     self.task.status = TaskStatus.IN_PROGRESS
        while True:
            # await self._callback.send(**kwargs)
            observation_response = await self.observe(
                objective, self._context, **kwargs
            )
            print(observation_response)
            ability_args = observation_response.content.get("function_arguments", {})
            if ability_args.get("clarifying_question"):
                hold = await self.handle_clarification(
                    observation_response, ability_args, **kwargs
                )
                if hold:
                    self._context.interaction = True
                    return
            else:
                observation = TaskPlan(**ability_args)
                if not observation:
                    raise Exception(
                        "Either observation or observer is not defined, please set observer in the chain."
                    )
                print("kwargs in chain", kwargs)
                await self._callback.send(observation, **kwargs)
                planning_message = Message.add_planning_message(
                    f'Pilot level Task Breakdown of "{objective.message}":\n'
                    + "\n".join(
                        [
                            f"'{task.objective}' will be done by {task.function_name} pilot"
                            for task in observation.tasks
                        ]
                    )
                )
                self._context.add_message(planning_message)
                self.task.add_plan(observation.get_tasks())
                break
        #
        # while self.task.active_task_idx < len(self.task.plan):
        #     await self.execute_next(objective, **kwargs)
        #     if self._context.interaction:
        #         break
        # if self.task.active_task_idx == len(self.task.plan):
        #     print('resetting state', self._session_id)
        #     self._context.current_task.status = TaskStatus.DONE
        #     task_end_message = Message.add_task_end_message(f"Task Completed: '{objective.message}'")
        #     self._context.add_message(task_end_message)
        #     await self._callback.send(**kwargs)
        #     print("chain completed")

    async def execute_next(self, objective, **kwargs):
        self._current_task = self.task.current_sub_task
        if self._current_task.status != TaskStatus.DONE:
            handler, transformer = self.current_handler(
                self._current_task.function_name
            )
            if handler is None:
                # TODO : Add a check to see if the task needs to be created as multiple tasks
                # return f"Handler named '{task_in_hand.function_name}' is not defined", context
                # TODO: Remove posibilty of null handler, or handle the situation...(dont start execution without confirming the flow from anther plan observer) - (planner, plan observer internal talks)
                self.logger.error(
                    f"Handler named '{self._current_task.function_name}' is not defined"
                )
                # TODO: need to be fixed, just increasing the task index to not to stuck in the same task
                self.task.active_task_idx += 1
            else:
                # TODO: there should be Pilot Task where we store the pilot Action?
                await self.execute_handler(
                    handler, transformer, user_input=objective, **kwargs
                )
                if not self._context.interaction:
                    self._current_task.status = TaskStatus.DONE
                    self.task.active_task_idx += 1
        else:
            self._response = "Task is already completed"
            self.task.active_task_idx += 1

    async def execute_handler(self, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(self._current_task, **kwargs)
            else:
                response = await handler.execute(self._current_task, **kwargs)

            # self._pilot_state = await self._state.serialize(handler) or {}
            if not self._context.interaction:
                # if isinstance(response, LanguageModelResponse):
                #     self._context.add_attachment(response.get_content())
                # elif isinstance(response, Context):
                #     self._context.extend(response)
                # elif isinstance(response, AbilityAction):
                #     pass
                if transformer:
                    self._response, self._context = transformer(
                        data=self._current_task,
                        response=response,
                        context=self._context,
                    )

        except Exception as e:
            import traceback

            self.logger.error(
                f"Error in handler {handler.name()}: {e} {traceback.print_exc()}"
            )

    async def handle_clarification(self, response, ability_args, **kwargs) -> bool:
        question_message = Message.add_question_message(
            message=ability_args.get("clarifying_question")
        )
        self._context.add_message(question_message)
        user_input, hold = await self._callback.send(
            question_message,
            task=self.task,
            response=response,
            context=self._context,
            **kwargs,
        )
        if user_input:
            self._context.add_message(user_input)
        return hold

    async def observe(self, objective, context, **kwargs) -> LanguageModelResponse:
        observer = self.current_planner(self.default_planner())
        if observer:
            try:
                return await observer.execute(
                    objective,
                    task_objective=objective.message,
                    context=context,
                    functions=self.dump_handlers(),
                    **kwargs,
                )
            except Exception as e:
                import traceback

                self.logger.error(
                    f"Error in observer {observer.name()}: {e} {traceback.print_exc()}"
                )
                return None
        return None

    def default_planner(self):
        return SimpleHandler.create(
            PlanningStrategy.default_configuration,
            smart_model_name=AIModelName.OPENAI_GPT4_O,
            fast_model_name=AIModelName.OPENAI_GPT4_O_MINI,
            role_config=RoleConfiguration(
                name="observer_pilot",
                role=(
                    "An AI Agent observing the conversation and selecting the next handler to execute the respective task"
                ),
                cycle_count=0,
                max_task_cycle_count=3,
                creation_time="",
            ),
        )

    # async def execute(self, objective: Union[str, Message], **kwargs):
    #     """
    #     Main method to start execution with a given objective.
    #     """
    #     if isinstance(objective, str):
    #         objective = Message.add_user_message(objective, kwargs)
    #     self._context.add_message(objective)
    #
    #     self._context.interaction = False
    #
    #     if self.current_planner():
    #         self.current_planner().execute(self._context, **kwargs)
    #     else:
    #         self.logger.warning("No planner found in the orchestrator.")
    #
    #     handler, transformer = self.current_handler("echo_handler")
    #
    #     response = await handler.execute(objective.message, **kwargs)
    #
    #     return response, self._context
    #
    # async def load_dependencies(self, **kwargs):
    #     """
    #     Load dependencies for the orchestrator.
    #     """
    #
    #     executor = SimpleExecutor.default_configuration
    #     res = await executor.execute(**{"document_type": "BOE",
    #                                     "file_url": "https://unpodbackend.s3.amazonaws.com/media/private/Charger-Bill.pdf"})
    #
    #     pass
