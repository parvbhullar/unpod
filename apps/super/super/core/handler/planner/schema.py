import enum
from typing import List, Union, Optional
from pydantic import BaseModel, Field
from super.core.resource.llm.schema import SchemaModel


class TaskStatus(str, enum.Enum):
    BACKLOG: str = "backlog"
    READY: str = "ready"
    IN_PROGRESS: str = "in_progress"
    DONE: str = "done"


class TaskSchema(SchemaModel):
    """
    Class representing the data structure for task for pilot objective, whether it is complete or not.
    """

    objective: str = Field(
        ..., description="An verbose description of what exactly the task is."
    )
    type: str = Field(
        # default=TaskType.RESEARCH,
        description="A categorization for the task from [research, write, edit, code, design, test, plan]."
    )
    priority: int = Field(
        ...,
        description="A number between 1 and 10 indicating the priority of the task "
        "relative to other generated tasks.",
    )
    ready_criteria: List[str] = Field(
        ...,
        description="A list of measurable and testable criteria that must "
        "be met for the "
        "task to be considered complete.",
    )
    acceptance_criteria: List[str] = Field(
        ...,
        description="A list of measurable and testable criteria that "
        "must be met before the task can be started.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG,
        description="The current status of the task from [backlog, in_progress, complete, on_hold].",
    )
    function_name: str = Field(
        ..., description="Name of the handler/function most suited for this task"
    )
    motivation: str = Field(
        ...,
        description="Your justification for choosing this pilot instead of a different one.",
    )
    self_criticism: str = Field(
        ...,
        description="Thoughtful self-criticism that explains why this pilot may not be "
        "the best choice.",
    )
    reasoning: str = Field(
        ...,
        description="Your reasoning for choosing this pilot taking into account the "
        "`motivation` and weighing the `self_criticism`.",
    )

    # def get_task(self) -> Task:
    #     return Task.factory(
    #         self.objective, self.type, self.priority, self.ready_criteria, self.acceptance_criteria, status=self.status,
    #         function_name=self.function_name
    #     )


class TaskPlan(SchemaModel):
    """
    Class representing the data structure for observation for agent objective, whether it is complete or not.
    If not complete, then the pilot name, motivation, self_criticism and reasoning for choosing the pilot.
    """

    current_status: TaskStatus = Field(
        ..., description="Status of the objective asked by the user "
    )
    tasks: List[TaskSchema] = Field(
        ..., description="List of tasks to be accomplished to achieve the objective."
    )
    clarifying_question: Optional[str] = Field(
        ...,
        description="Relevant question to be asked to user if ask is not clear from the user.",
    )

    # def get_tasks(self) -> List[Task]:
    #     lst = []
    #     for task in self.tasks:
    #         lst.append(task.get_task())
    #     return lst


class ClarifyingQuestion(SchemaModel):
    """
    Function to ask clarifying question to the user about objective if required
    Ask the user relevant question only if all the conditions are met. conditions are:
    1. the information is not already available.
    2. you are blocked to proceed without user assistance
    """

    clarifying_question: str = Field(
        ...,
        description="Relevant question to be asked to user in user friendly language",
    )
    motivation: str = Field(
        ..., description="Your justification for asking this question."
    )
    self_criticism: str = Field(
        ...,
        description="Thoughtful self-criticism that explains why this question might not be required",
    )
    reasoning: str = Field(
        ...,
        description="Your reasoning for asking this question. taking into account the `motivation` "
        "and weighing the `self_criticism`.",
    )
    ambiguity: List[str] = Field(
        ..., description="your thoughtful reflection on the ambiguity of the task"
    )
