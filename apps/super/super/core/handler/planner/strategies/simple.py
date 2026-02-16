from super.core.context.schema import ContentItem, ContentType
from super.core.handler.strategy.base import PromptStrategy
from super.core.handler.strategy.config import PromptStrategyConfiguration
from super.core.resource.llm.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
    SchemaModel,
    MessageRole,
)
from super.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
)
from pydantic import Field
from typing import List, Dict
from super.core.resource.model_providers import AIModelName
from super.core.utils import json_loads
from super.core.utils.prompts.chat_prompts import REQUIRE_CITATION_STATEMENT
from super.core.utils.prompts.constants import GENERAL_SEP_PAT


class BaseContent(SchemaModel):
    """
    Class representing a question and its answer as a list of facts each one should have a soruce.
    each sentence contains a body and a list of sources."""

    content: str = Field(
        ..., description="Full body of response content from the llm model"
    )
    highlights: List[str] = Field(
        ...,
        description="Body of the answer, each fact should be its separate object with a body and a list of sources",
    )


class SimplePrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = (
        "Your job is to respond to user queries by providing accurate, well-structured answers. "
        "When using provided documents as sources, cite them using [n] format where n is the document number. "
        "Each citation should be relevant and properly integrated into your response. "
        "Your response should include both the main content and a structured list of citations used."
    )

    DEFAULT_USER_PROMPT_TEMPLATE = (
        "Your current task is '{task_objective}'.\n"
        "Here is the relevant context and information:\n"
        "{additional_info}\n\n"
        "User input: {user_input}\n\n"
        "Please provide a response that:\n"
        "1. Directly addresses the task/question\n"
        "2. Uses proper citations [n] when referencing information from provided documents\n"
        "3. Maintains a clear and coherent structure\n"
    )

    DEFAULT_PARSER_SCHEMA = BaseContent.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
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

    def format_csv(self, data):
        local_path = data  # Extract the local file path
        if ".csv" in local_path:
            local_path = local_path.replace("file:", "")

        import pandas as pd

        # Load your CSV file
        data = pd.read_csv(local_path)

        # Convert DataFrame to JSON if necessary
        json_data = data.to_json(orient="records")
        return json_data

    def process_file(self, path):
        from markitdown import MarkItDown
        from openai import OpenAI

        client = OpenAI()
        md = MarkItDown(llm_client=client, llm_model="gpt-4o")
        result = md.convert(path)
        return result.text_content

    def load_base64_file(self, file):
        """
        Convert a file (local or URL) to a Base64 string.

        Parameters:
        file (str): The file path or URL.

        Returns:
        str: Base64 encoded string of the file's content.
        """
        import base64
        import requests
        from urllib.parse import urlparse
        import csv

        try:
            if file.startswith("http") or file.startswith("https"):
                file = file.replace(
                    "\\", "/"
                )  # Replace backslashes with forward slashes
                if file.startswith("https:/") and not file.startswith("https://"):
                    file = file.replace("https:/", "https://")
                elif file.startswith("http:/") and not file.startswith("http://"):
                    file = file.replace("http:/", "http://")

            if file.startswith("https") or file.startswith("http"):
                response = requests.get(file)
                response.raise_for_status()  # Raise an error for bad responses
                file_content = response.content
            elif file.startswith("file:"):
                local_path = urlparse(file).path  # Extract the local file path
                file_content = open(local_path, "rb").read()
            else:
                raise ValueError(
                    "Unsupported file format. Use 'http' or 'file:' prefixes."
                )
            base64_content = base64.b64encode(file_content).decode("utf-8")
            return base64_content

        except requests.exceptions.RequestException as e:
            # Handle HTTP errors
            print(f"Error fetching the URL: {e}")
            return None

        except FileNotFoundError:
            print("Local file not found.")
            return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        # print("kwargs",  v)
        model_name = kwargs.pop("model_name", AIModelName.OPENAI_GPT4)
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
        )

        docs_message = self._generate_docs_message(kwargs.get("docs", []))
        system_prompt = self._system_prompt_message.format(**template_kwargs)

        if docs_message:
            system_prompt = (
                system_prompt + GENERAL_SEP_PAT + REQUIRE_CITATION_STATEMENT,
            )

        messages = []
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt[0],
        )

        messages.append(system_message)

        if docs_message:
            messages.append(docs_message)

        if "images" in template_kwargs or "files" in template_kwargs:
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
            )
            user_message = self._generate_content_list(user_message, template_kwargs)
        else:
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
                content=self._user_prompt_template.format(**template_kwargs),
            )

        messages.append(user_message)

        functions = []
        if self._parser_schema is not None:
            parser_function = LanguageModelFunction(
                json_schema=self._parser_schema,
            )
            functions.append(parser_function)

        prompt = LanguageModelPrompt(
            messages=messages,
            functions=functions,
            function_call=None if not functions else functions[0],
            tokens_used=0,
        )

        return prompt

    def get_template_kwargs(self, kwargs):
        template_kwargs = {
            "task_objective": "",
            "cycle_count": 0,
            "action_history": "",
            "additional_info": "",
            "user_input": "",
            "acceptance_criteria": "",
        }
        # Update default kwargs with any provided kwargs
        template_kwargs.update(kwargs)
        return template_kwargs

    def _generate_docs_message(self, docs):
        if not docs:
            return None

        info = "Here are the relevant documents for reference:\n\n"
        for n, doc in enumerate(docs, 1):
            info += f"[{n}] {doc.content}\n"
            if hasattr(doc, "metadata") and doc.metadata:
                info += f"Source: {doc.url or doc.metadata.get('source', 'Unknown')}\n"
            info += "\n"

        return LanguageModelMessage(
            role=MessageRole.USER,
            content=info,
        )

    def _generate_content_list(self, message: LanguageModelMessage, template_kwargs):
        from super.core.context.schema import ContentType

        message.add_text(self._user_prompt_template.format(**template_kwargs))

        image_list = template_kwargs.pop("images", [])
        for image in image_list:
            if image.type == ContentType.IMAGE:
                message.add_image(url=str(image.content), alt_text="")

        file_list = template_kwargs.pop("files", [])

        # for file in file_list:
        #     #TODO load base content from file
        #     if isinstance(file, str) and (file.startswith("http") or file.startswith("file:")):
        #         content = self.load_base64_file(file)
        #     elif isinstance(file, ContentItem):
        #         if file.type==ContentType.IMAGE:
        #             message.add_image(url=str(file.content), alt_text="")
        #         if '.pdf' in str(file.content) and file.type==ContentType.FILE:
        #             message.add_file(f"data:application/pdf;base64,{self.load_base64_file(str(file.content))}")
        #         if '.csv' in str(file.content) and file.type==ContentType.FILE:
        #             message.add_text(self.format_csv(file.content))
        #     else:
        #         content = file
        # message.add_text(str(content))

        for file in file_list:
            if isinstance(file, ContentItem):
                if ".csv" in str(file.content) and file.type == ContentType.FILE:
                    message.add_text(self.format_csv(file.content))
                elif file.type == ContentType.TEXT:
                    message.add_text(file.content)
                else:
                    message.add_text(self.process_file(file.content))
            else:
                message.add_text(str(file))

        return message

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
        # print("Raw Model Response", response_content)
        if "function_call" in response_content and response_content["function_call"]:
            parsed_response = json_loads(
                response_content.get("function_call", {}).get("arguments", {})
            )
        else:
            parsed_response = response_content

        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

    def get_config(self) -> PromptStrategyConfiguration:
        return PromptStrategyConfiguration(
            model_classification=self._model_classification,
            system_prompt=self._system_prompt_message,
            user_prompt_template=self._user_prompt_template,
            parser_schema=self._parser_schema,
        )

    @classmethod
    def factory(
        cls,
        system_prompt=None,
        user_prompt_template=None,
        parser=None,
        model_classification=None,
    ) -> "SimplePrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config["model_classification"] = model_classification
        if system_prompt:
            config["system_prompt"] = system_prompt
        if user_prompt_template:
            config["user_prompt_template"] = user_prompt_template
        if parser:
            config["parser_schema"] = parser
        config.pop("location", None)
        return cls(**config)
