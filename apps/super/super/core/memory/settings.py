from enum import Enum


class MemoryProviders(Enum):
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"
    VESPA = "vespa"
    NEO4J = "neo4j"
    REDIS = "redis"


class MemoryConfig:
    def __init__(
        self, provider: str, collection_name: str, host: str, port: int, **kwargs
    ):
        self.provider = provider
        self.collection_name = collection_name
        self.host = host
        self.port = port

        # Embedder settings
        self.embedder_provider = kwargs.get("embedder_provider", None)
        self.embedder_config = kwargs.get("embedder_config", None)

        # LLM settings
        self.llm_provider = kwargs.get("llm_provider", None)
        self.llm_config = kwargs.get("llm_config", None)

        # Custom prompt
        self.custom_prompt = kwargs.get("custom_prompt", None)
        self.version = kwargs.get("version", None)

        # Graph Store
        self.username = kwargs.get("username", None)
        self.password = kwargs.get("password", None)

    def get_config(self) -> dict:
        """Returns the configuration as a dictionary."""
        store_type = "vector_store"
        if self.provider != MemoryProviders.NEO4J.value:
            store_type = "graph_store"
        if self.provider == MemoryProviders.REDIS.value:
            store_type = "kv_store"

        if store_type == "vector_store":
            config = {
                store_type: {
                    "provider": self.provider,
                    "config": {
                        "collection_name": self.collection_name,
                        "host": self.host,
                        "port": self.port,
                    },
                }
            }
        else:
            config = {
                store_type: {
                    "provider": self.provider,
                    "config": {
                        "url": self.host,
                        "username": self.username,
                        "password": self.password,
                    },
                }
            }
        if self.embedder_provider:
            config["embedder"] = {
                "provider": self.embedder_provider,
                "config": self.embedder_config,
            }
        if self.llm_provider:
            config["llm"] = {"provider": self.llm_provider, "config": self.llm_config}
        if self.custom_prompt:
            config["custom_prompt"] = self.custom_prompt
        if self.version:
            config["version"] = self.version
        return config

    @property
    def url(self) -> str:
        """Returns the URL of the memory store."""
        url = f"{self.host}"
        if self.port:
            url = f"{url}:{self.port}"
        if self.username and self.password:
            url = f"{self.provider}://{self.username}:{self.password}@{url}"
        else:
            url = f"{self.provider}://{url}"
        return url

    @property
    def mem_provider(self) -> str:
        return self.provider

    def __repr__(self):
        """Representation of the configuration."""
        return (
            f"MemoryConfig(provider={self.provider}, "
            f"collection_name={self.collection_name}, "
            f"host={self.host}, port={self.port})"
            f"embedder_provider={self.embedder_provider}, "
            f"embedder_config={self.embedder_config}"
        )

    @classmethod
    def factory(
        cls,
        collection_name: str,
        provider: str = MemoryProviders.QDRANT.value,
        host: str = "localhost",
        port: int = 6333,
        **kwargs,
    ) -> "MemoryConfig":
        """Factory method to create a MemoryConfig object from a dictionary."""
        ## LLM settings
        # "llm": {
        #     "provider": "openai",
        #     "config": {
        #         "model": "gpt-4o",
        #         "temperature": 0.2,
        #         "max_tokens": 1500,
        #     }
        # },
        # "custom_prompt": custom_prompt,
        # "version": "v1.1"

        # Graph Store config
        # "graph_store": {
        #     "provider": "neo4j",
        #     "config": {
        #         "url": "neo4j+s://xxx",
        #         "username": "neo4j",
        #         "password": "xxx"
        #     }
        # },
        # "version": "v1.1"
        return cls(
            provider=provider,
            collection_name=collection_name,
            host=host,
            port=port,
            **kwargs,
        )


if __name__ == "__main__":
    # Example usage:
    memory_config = MemoryConfig.factory(collection_name="test")
    # Retrieve configuration as a dictionary
    config_dict = memory_config.get_config()
    print(config_dict)
