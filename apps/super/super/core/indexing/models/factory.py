import logging
from enum import Enum
from typing import List

from super.core.logging.logging import print_log


class ModelType(Enum):
    embedding = "embedding"
    llm = "llm"

class ModelProviderType(Enum):
    openai = "openai"
    anthropic = "anthropic"
    huggingface = "huggingface"


class SentenceTransformerWrapper:
    """
    Wrapper to make SentenceTransformer compatible with LangChain's embeddings interface.
    """
    def __init__(self, model):
        self.client = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        import numpy as np
        embeddings = self.client.encode(texts, convert_to_tensor=False)
        # Handle both numpy arrays and lists
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        import numpy as np
        embedding = self.client.encode([text], convert_to_tensor=False)
        # Handle both numpy arrays and lists
        if isinstance(embedding, np.ndarray):
            return embedding[0].tolist()
        return embedding[0]


class ModelFactory:
    def __init__(
        self,
        logger: logging.Logger = None,
    ):
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    @classmethod
    def factory(
        cls,
        model_name: str,
        model_type: ModelType=ModelType.embedding,
        model_provider_type: ModelProviderType=ModelProviderType.huggingface,
    ):
        if model_type == ModelType.embedding:
            if model_provider_type == ModelProviderType.huggingface:
                # from super.core.indexing.models.hf import (
                #     HFEmbeddingModel,
                # )
                # # Get the singleton SentenceTransformer model
                # sentence_transformer = HFEmbeddingModel().get_model(model_name=model_name)
                try:
                    from langchain.embeddings import HuggingFaceEmbeddings
                except ImportError:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    print_log(
                        "Please install the langchain package to use HuggingFaceEmbeddings: pip install langchain"
                    )

                model_kwargs = {"device": "cpu"}
                encode_kwargs = {"normalize_embeddings": True}
                embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs,
                )
                # Wrap it in our wrapper for LangChain compatibility
                return embeddings
            else:
                from langchain_community.embeddings import OpenAIEmbeddings
                # from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings()
        elif model_type == ModelType.llm:
            from super.core.resource.model_providers.openai import (
                OpenAILLMProvider,
            )

            if model_name.startswith("openai/"):
                return OpenAILLMProvider(model_name=model_name)
            else:
                raise ValueError(f"Unsupported LLM model: {model_name}")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
