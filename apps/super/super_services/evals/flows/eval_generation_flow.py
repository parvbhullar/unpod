"""
Prefect Flow for Eval Generation
Async flow that generates QA evaluation pairs for an agent.
"""

import logging
from pydantic import BaseModel, Field
from typing import Optional

from prefect import flow, task, get_run_logger
from prefect.runtime import flow_run

from super_services.evals.eval_generator import EvalGenerator


logger = logging.getLogger(__name__)


class EvalGenerationJob(BaseModel):
    """Job parameters for eval generation flow."""

    gen_type: str
    pilot_handle: Optional[str] = Field(default=None)
    kn_token: Optional[str] = Field(default=None)
    force: Optional[bool] = Field(default=False)
    language: Optional[str] = Field(default=None)


def generate_eval_flow_name() -> str:
    """Generate dynamic flow run name."""
    parameters = flow_run.parameters
    job = parameters.get("job", {})
    if hasattr(job, "model_dump"):
        job = job.model_dump()
    gen_type = job.get("gen_type")
    pilot_handle = job.get("pilot_handle")
    kn_token = job.get("kn_token")
    return f"eval-generation-{gen_type}-{pilot_handle or kn_token}"


@task(
    name="generate-agent-evals",
    description="Generate QA evaluation pairs for agent",
    log_prints=True,
)
async def generate_agent_evals_task(
    gen_type, agent_id, kn_token, force_regenerate: bool = False, language: Optional[str] = None
) -> dict:
    logger = get_run_logger()
    logger.info(
        f"Starting eval generation for config: gen_type={gen_type}, agent_id={agent_id}, kn_token={kn_token}"
    )
    if force_regenerate:
        logger.info("Force regenerate: ON (will regenerate even if exists)")

    try:
        # Generate evals (duplicate check is built into generate_all_evals)
        generator = EvalGenerator(gen_type, agent_id, kn_token, logger, language=language)
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

    gen_type = job.gen_type
    agent_id = job.pilot_handle
    kn_token = job.kn_token
    force = job.force
    language = job.language

    if not agent_id and not kn_token:
        raise ValueError("Either pilot_handle or kn_token is required")

    logger.info(f"Starting eval generation flow for genType: {gen_type}")
    results = await generate_agent_evals_task(
        gen_type, agent_id, kn_token, force_regenerate=force, language=language
    )

    return {
        "agent_id": agent_id,
        "kn_token": kn_token,
        "gen_type": gen_type,
        "language": language,
        **results,
    }
