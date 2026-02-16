"""
Seed script to insert default LLM provider config into MongoDB.

Usage:
    LLM_PROVIDER=openai LLM_MODEL=gpt-4 LLM_API_KEY=sk-xxx python scripts/seed_llm_provider.py
    LLM_PROVIDER=anthropic LLM_MODEL=claude-3-sonnet-20240229 LLM_API_KEY=sk-ant-xxx python scripts/seed_llm_provider.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.api.config import get_settings
from services.search_service.models.llm_provider import LLMProviderModel


def seed():
    settings = get_settings()
    print(f"Connected to MongoDB: {settings.MONGO_DB}")

    provider = os.environ.get("LLM_PROVIDER")
    model_name = os.environ.get("LLM_MODEL")
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")

    if not provider or not model_name:
        print("ERROR: LLM_PROVIDER and LLM_MODEL are required.")
        print(
            "Usage: LLM_PROVIDER=openai LLM_MODEL=gpt-4 LLM_API_KEY=sk-xxx python scripts/seed_llm_provider.py"
        )
        sys.exit(1)

    # Check if a default provider already exists
    existing = LLMProviderModel.find_many(is_default=True)
    if existing:
        print(f"Updating existing default provider (id={existing[0].id})")
        from mongomantic.core.database import MongomanticClient
        from bson import ObjectId

        db = MongomanticClient.db
        db["llm_providers"].update_one(
            {"_id": ObjectId(str(existing[0].id))},
            {
                "$set": {
                    "provider": provider,
                    "model_name": model_name,
                    "api_key": api_key,
                    "api_base": api_base,
                    "is_default": True,
                }
            },
        )
        print(f"Updated: provider={provider}, model={model_name}")
    else:
        data = {
            "provider": provider,
            "model_name": model_name,
            "api_key": api_key,
            "api_base": api_base,
            "is_default": True,
            "custom_config": {},
        }
        LLMProviderModel.save_single_to_db(data)
        print(f"Created: provider={provider}, model={model_name}, is_default=True")

    print("Done.")


if __name__ == "__main__":
    seed()
