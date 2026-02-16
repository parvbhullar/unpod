"""Stub types for agent generation and search."""

from abc import ABC
from typing import List, Any

from pydantic import Field

from super.core.handler.planner.strategies import SimplePrompt
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.handler.strategy.config import PromptStrategyConfiguration
from super.core.resource.llm.schema import SchemaModel, LanguageModelClassification


class KnowledgeBase(SchemaModel):
    name: str = Field(
        None,
        description="Name of the knowledge base.",
    )
    datasource: str = Field(
        None,
        description="Type and description of the data sources.",
    )


class AIPersona(SchemaModel):
    persona_name: str = Field(None, description="The name of the AI persona.")
    handle: str = Field(None, description="Unique identifier for the AI persona.")
    about: str = Field(None, description="Description of the AI persona.")
    tags: List[str] = Field(None, description="Tags associated with the AI persona.")
    persona: str = Field(None, description="The persona text.")
    questions: List[str] = Field(None, description="Key questions for the persona.")
    knowledge_bases: List[KnowledgeBase] = Field(
        None, description="Knowledge bases this persona relies on."
    )
    llm_model: str = Field(None, description="The language model for this persona.")


class PersonaGenPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT_MULTI_AGENT = """
    Generate 6 distinct AI Agent personas based on the user's query.
    """
    DEFAULT_SYSTEM_PROMPT = """
    Given a task description or existing prompt, produce a detailed system prompt.
    """
    DEFAULT_USER_PROMPT_TEMPLATE = """
        Query, Task, Goal, or Current Prompt:{message}
    """
    DEFAULT_PARSER_SCHEMA = AIPersona.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=(
                "super.app.agent_types.PersonaGenPrompt"
            ),
        ),
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Any = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification


class AIAgent:
    """Model representing an AI agent."""

    persona_name: str
    about: str
    tags: list[str] | None
    handle: str
    persona: str
    questions: list[str] | None
    score: float | None
    embeddings: list[float] | None

    def __init__(self, data):
        self.persona_name = data.get("persona_name")
        self.tags = data.get("tags", [])
        self.handle = data.get("handle")
        self.about = data.get("about")
        self.persona = data.get("persona")
        self.knowledge_bases = data.get("knowledge_bases", [])
        self.questions = data.get("questions", [])
        self.score = data.get("score", 0)
        self.embeddings = data.get("embeddings", None)

    def __str__(self):
        return (
            f"AIAgent('{self.persona_name}', handle='{self.handle}',"
            f" tags={self.persona_name}, score={self.score})"
        )

    def display_info(self):
        print(f"Name: {self.persona_name}")
        print(f"Handle: {self.handle}")
        print("Tags:", ", ".join(self.tags))
        print("About:", self.about)
        print("Persona:", self.persona)
        print("Knowledge Bases:", ", ".join(self.knowledge_bases))

    def to_dict(self):
        return {
            "persona_name": self.persona_name,
            "tags": self.tags,
            "handle": self.handle,
            "about": self.about,
            "persona": self.persona,
            "knowledge_bases": self.knowledge_bases,
            "questions": self.questions,
            "score": self.score,
            "embeddings": self.embeddings,
        }
