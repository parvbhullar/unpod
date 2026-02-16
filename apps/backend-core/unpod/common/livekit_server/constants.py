import os

env_file_name = os.environ.get("DJANGO_SETTINGS_MODULE").split(".")[-1]

ENV_RENAME = {"production": "prod"}

ENGLISH_AGENT_NAME = (
    f"unpod-{ENV_RENAME.get(env_file_name, env_file_name)}-general-agent-v3"
)

CENTRAL_AGENT_NAME = (
    f"superkik-{ENV_RENAME.get(env_file_name, env_file_name)}-assistant-agent-v1"
)
