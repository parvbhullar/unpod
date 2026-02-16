"""
Prefect Flow for Eval Generation
Async flow that generates QA evaluation pairs for an agent.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from prefect import flow, task, get_run_logger
from prefect.runtime import flow_run

from super_services.evals.eval_generator import EvalGenerator


logger = logging.getLogger(__name__)


@dataclass
class EvalGenerationJob:
    """Job parameters for eval generation flow."""
    agent_id: str
    force_regenerate: bool = False


def generate_eval_flow_name() -> str:
    """Generate dynamic flow run name."""
    parameters = flow_run.parameters
    job = parameters.get("job", {})
    if hasattr(job, "__dict__"):
        agent_id = getattr(job, "agent_id", "unknown")
    else:
        agent_id = job.get("agent_id", "unknown")
    return f"eval-generation-{agent_id}"


@task(
    name="generate-agent-evals",
    description="Generate QA evaluation pairs for agent",
    log_prints=True,
    retries=2,
    retry_delay_seconds=30,
)
async def generate_agent_evals_task(agent_id: str, force_regenerate: bool = False) -> dict:
    """
    Task that performs the actual eval generation.

    Args:
        agent_id: Agent handle
        force_regenerate: If True, regenerate even if QA pairs already exist

    Returns:
        Dict with generation results
    """
    logger = get_run_logger()
    logger.info(f"Starting eval generation for agent: {agent_id}")
    if force_regenerate:
        logger.info("Force regenerate: ON (will regenerate even if exists)")

    try:
        # Generate evals (duplicate check is built into generate_all_evals)
        generator = EvalGenerator(agent_id)
        results = await generator.generate_all_evals(force_regenerate=force_regenerate)

        logger.info(f"Eval generation completed: {results}")

        # Log skipped items
        if results.get("skipped"):
            for skip_msg in results["skipped"]:
                logger.info(f"SKIPPED: {skip_msg}")

        # Log errors
        if results.get("errors"):
            for error in results["errors"]:
                logger.warning(f"Error: {error}")

        return results

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Eval generation failed: {error_msg}")
        raise


@flow(
    name="Generate-Agent-Evals",
    description="Generate QA evaluation pairs for an agent from config and knowledge base",
    flow_run_name=generate_eval_flow_name,
    log_prints=True,
)
async def generate_agent_evals_flow(job: EvalGenerationJob) -> dict:
    """
    Main flow for generating agent evals.

    Args:
        job: EvalGenerationJob with agent_id and optional force_regenerate flag

    Returns:
        Dict with generation results including:
        - agent_id: Agent handle
        - batch_id: Unique batch identifier
        - agent_qa_count: Number of agent QA pairs
        - kb_qa_count: Number of KB QA pairs
        - total_qa_count: Total QA pairs
        - skipped: List of skipped generation reasons (if duplicates exist)
        - errors: List of any errors encountered
    """
    logger = get_run_logger()

    agent_id = job.agent_id if hasattr(job, "agent_id") else job.get("agent_id")
    force_regenerate = job.force_regenerate if hasattr(job, "force_regenerate") else job.get("force_regenerate", False)

    if not agent_id:
        raise ValueError("agent_id is required")

    logger.info(f"Starting eval generation flow for agent: {agent_id}")

    # Run the generation task
    results = await generate_agent_evals_task(agent_id, force_regenerate)

    return {
        "agent_id": agent_id,
        **results,
    }