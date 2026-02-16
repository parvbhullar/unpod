from abc import ABC

from super.core.handler.planner.schema import TaskSchema, TaskPlan, ClarifyingQuestion
from super.core.handler.planner.strategies import SimplePrompt
from super.core.handler.strategy.base import PromptStrategy
from super.core.handler.strategy.config import PromptStrategyConfiguration
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.resource.llm.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
    MessageRole,
)
from super.core.resource.model_providers import (
    AIModelName,
    LanguageModelMessage,
    LanguageModelFunction,
)
from typing import Dict, Optional, List
import enum
from pydantic import Field

from super.core.utils import json_loads


class PlanningStrategy(PromptStrategy, ABC):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_SYSTEM_PROMPT = """
    *Context*: {context}

    *Functions*: {functions}

    Given the above context and the list of functions, do one of the following:
    1. Divide the task *'{task_objective}'* into smaller tasks by mapping each of the objective's sub-goals to a function from the functions provided.
    2. Use best of your knowledge to choose functions for tasks, if you are able to create tasks but not able to map the functions, map the task with call_human_in_loop.
    3. If you are unable to proceed, ask a Clarifying Question only if any aspect of task *'{task_objective}'* is unclear.
    """

    DEFAULT_USER_PROMPT_TEMPLATE = (
        ""
        # "Current user  is {task_objective}.\n"
        # "You have taken {cycle_count} actions on this task already. "
        # "Here is the actions you have taken and their results:\n"
        # "{action_history}\n\n"
    )

    DEFAULT_PARSER_SCHEMA = TaskPlan.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.handler.planner.strategies.planning_strategy.PlanningStrategy",
        ),
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Dict = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        # print("kwargs",  v)
        model_name = kwargs.pop("model_name", AIModelName.OPENAI_GPT4)
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
        )

        # self._parser_schema = ObjectivePlan.function_schema()

        # pilots = template_kwargs.pop("pilots", [])
        #
        # pilot_enum = enum.Enum("Pilot", {value.get('name'): value.get('name') for value in pilots})

        # class PilotTaskSchema(TaskSchema):
        #     function_name: pilot_enum = Field(..., description="Name of the pilot/function most suited for this task")
        #
        # class PilotObservation(ObjectivePlan):
        #     tasks: List[PilotTaskSchema] = Field(
        #         ..., description="List of tasks to be accomplished by the each pilot"
        #     )
        #
        # self._parser_schema = PilotObservation.function_schema()

        # if model_name == AIModelName.OPENAI_GPT4_VISION and "images" in template_kwargs:
        #     user_message = LanguageModelMessage(
        #         role=MessageRole.USER,
        #     )
        #     # print("VISION prompt", user_message)
        #     user_message = self._generate_content_list(user_message, template_kwargs)
        # else:
        #     user_message = LanguageModelMessage(
        #         role=MessageRole.USER,
        #         content=self._user_prompt_template.format(**template_kwargs)
        #     )

        functions = template_kwargs.pop("functions", [])

        function_enum = enum.Enum(
            "Function", {value.get("name"): value.get("name") for value in functions}
        )

        class PilotTaskSchema(TaskSchema):
            function_name: function_enum = Field(
                ..., description="Name of the function most suited for this task"
            )

        class PilotObjective(TaskPlan):
            tasks: List[PilotTaskSchema] = Field(
                ..., description="List of tasks to be accomplished"
            )

        function = {
            "name": "execute_functions",
            "description": "versatile function wrapper designed to execute multiple functions based on a structured "
            "object passed as its argument. This function simplifies the process of calling multiple "
            "functions with varying parameters by organizing the function calls and their respective "
            "parameters in a single, unified structure.",
            "parameters": {
                "type": "object",
                "properties": {},
                # "required": ["ClarifyingQuestion", "PilotObservation"]
            },
        }

        for schema in [ClarifyingQuestion, TaskPlan]:
            function["parameters"]["properties"].update(
                schema.function_schema(arguments_format=True)
            )

        function = LanguageModelFunction(json_schema=function)
        functions = [function]
        # if self._parser_schema is not None:
        #     parser_function = LanguageModelFunction(
        #         json_schema=self._parser_schema,
        #     )
        #     functions.append(parser_function)

        prompt = LanguageModelPrompt(
            messages=[system_message],
            functions=functions,
            function_call=function,
            # TODO
            tokens_used=0,
        )
        return prompt

    def get_template_kwargs(self, kwargs):
        template_kwargs = {
            "context": "",
            "objective": "",
        }
        # Update default kwargs with any provided kwargs
        template_kwargs.update(kwargs)
        return template_kwargs

    def parse_response_content(
        self,
        response_content: dict,
    ) -> dict:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed response.

        """
        # print(response_content)
        # if "function_call" in response_content:
        #     parsed_response = json_loads(response_content["function_call"]["arguments"])
        # else:
        #     parsed_response = response_content
        # # print(response_content)
        # # parsed_response = json_loads(response_content["content"])
        # # parsed_response = self._parser_schema.from_response(response_content)
        # return parsed_response

        args = json_loads(response_content["function_call"]["arguments"])
        if args.get("ClarifyingQuestion"):
            function_name = "ClarifyingQuestion"
            function_arguments = args["ClarifyingQuestion"]
        else:
            function_name = list(args.keys())[0]
            function_arguments = args[list(args.keys())[0]] if args else {}

        parsed_response = {
            "function_name": function_name,
            "function_arguments": function_arguments,
        }
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response
