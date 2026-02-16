import abc
import typing

from super.core.configuration import SystemConfiguration
from super.core.resource.llm.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)


class PromptStrategy(abc.ABC):
    default_configuration: SystemConfiguration

    @property
    @abc.abstractmethod
    def model_classification(self) -> LanguageModelClassification:
        ...

    @abc.abstractmethod
    def build_prompt(self, *_, **kwargs) -> LanguageModelPrompt:
        ...

    @abc.abstractmethod
    def parse_response_content(self, response_content: dict) -> typing.Any:
        ...
