import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from prefect import task, flow

from super.core.voice.eval_agent.eval_test_agent import EvalTestAgent, EvalResults
from super_services.voice.models.config import ModelConfig
from super_services.db.services.schemas.task import TaskStatusEnum


@task(
    name="eval_test",
)
async def eval_test(config: Dict[str, Any], test_cases: List[Dict]) -> EvalResults:
    agent = EvalTestAgent(config)
    results = await agent.test_llm_agent(test_cases)
    return results


def _convert_to_bool(value) -> bool:
    """Convert string/empty values to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


@task(
    name="get_collection_pair",
    description="get collection pair from mongo",
)
def get_collection_pair(token):
    try:
        from pymongo import MongoClient
        from super_services.libs.config import settings

        client = MongoClient(settings.MONGO_DSN)
        db = client[settings.MONGO_DB]
        collection = db[f"collection_data_{token}"]
        result = list(collection.find({}, {"_id": 0}))

        # Convert string booleans to actual booleans
        for item in result:
            item["is_tool_call"] = _convert_to_bool(item.get("is_tool_call", False))
            item["is_first_message"] = _convert_to_bool(
                item.get("is_first_message", False)
            )

        client.close()
        print(f"Fetched {len(result)} QA pairs from collection_data_{token}")
        return result

    except Exception as e:
        print(f"Could not get collection pairs: {str(e)}")
        return []


@task(
    name="get_pairs",
)
def get_pairs(kn_bases: List[str]) -> List[Dict[str, Any]]:
    """Generate test case pairs for evaluation."""
    pairs = []
    for kn in kn_bases:
        pair = get_collection_pair(kn)
        pairs.extend(pair)

    return pairs


@task(
    name="save_eval_results",
    description="Save evaluation results to MongoDB",
)
def save_eval_results(
    results_dict: Dict[str, Any],
    agent_id: str,
    metadata: Dict[str, Any] = None,
    eval_id: str = None,
) -> str:
    """
    Save evaluation results to MongoDB.

    Args:
        results_dict: Dictionary with evaluation results
        agent_id: The agent ID that was tested
        metadata: Optional additional metadata

    Returns:
        The eval_id of the saved document
    """
    try:
        from super_services.db.services.models.eval_results import EvalResultModel

        if not eval_id:
            eval_id = str(uuid.uuid4())

        eval_doc = {
            "agent_id": agent_id,
            "total_cases": results_dict.get("total_cases", 0),
            "passed_cases": results_dict.get("passed_cases", 0),
            "failed_cases": results_dict.get("failed_cases", 0),
            "pass_rate": results_dict.get("pass_rate", "0.0%"),
            "test_results": results_dict.get("test_results", []),
            "eval_timestamp": datetime.utcnow(),
            "metadata": metadata or {},
            "status": TaskStatusEnum.completed,
        }

        EvalResultModel.update_one({"eval_id": eval_id}, eval_doc)
        print(f"Saved evaluation results with eval_id: {eval_id}")
        return eval_id

    except Exception as e:
        print(f"Failed to save evaluation results: {str(e)}")
        pass


def create_eval_task(eval_id, agent_id, metadata: dict = {}, results_dict: dict = {}):
    eval_doc = {
        "eval_id": eval_id,
        "agent_id": agent_id,
        "total_cases": results_dict.get("total_cases", 0),
        "passed_cases": results_dict.get("passed_cases", 0),
        "failed_cases": results_dict.get("failed_cases", 0),
        "pass_rate": results_dict.get("pass_rate", "0.0%"),
        "test_results": results_dict.get("test_results", []),
        "eval_timestamp": datetime.utcnow(),
        "metadata": metadata or {},
        "status": TaskStatusEnum.in_progress,
    }
    from super_services.db.services.models.eval_results import EvalResultModel

    EvalResultModel.save_single_to_db(eval_doc)


@flow(
    name="test_agent_evals",
    description="Test agent evals for testing agent configurations",
    log_prints=True,
)
async def test_agent_evals(
    agent_id: str,
    kn_bases: List[str],
) -> Dict[str, Any]:
    """
    Run agent evaluations and return results.

    Args:
        agent_id: The agent ID to test
        kn_bases: List of knowledge base tokens

    Returns:
        Dictionary with evaluation results including eval_id if saved
    """
    test_cases = get_pairs(kn_bases)
    eval_id = f"EV{str(uuid.uuid4())}"

    metadata = {
        "knowledge_bases": kn_bases,
        "test_case_count": len(test_cases),
    }

    create_eval_task(eval_id, agent_id, metadata=metadata, results_dict={})

    print(f"test cases: {len(test_cases)}")

    config = ModelConfig().get_config(agent_id=agent_id)

    results = await eval_test(config, test_cases)

    results_dict = results.to_dict()

    eval_id = save_eval_results(results_dict, agent_id, metadata, eval_id)

    results_dict["eval_id"] = eval_id

    # Print JSON output for easy parsing
    print("\n" + "=" * 60)
    print("JSON RESULTS:")
    print("=" * 60)
    print(json.dumps(results_dict, indent=2, default=str))

    return results_dict


if __name__ == "__main__":
    import asyncio

    kn_bases = ["6OWZ88K5K9Q37LJ6CEUDLNQE"]

    results = asyncio.run(
        test_agent_evals(agent_id="testing-good-qua-xkc0gsvr7ns7", kn_bases=kn_bases)
    )
