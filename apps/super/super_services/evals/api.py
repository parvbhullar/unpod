"""
API Endpoints for Eval Generation
Provides REST API for generating and managing agent evaluation pairs.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from super_services.prefect_setup.deployments.utils import trigger_deployment
from super_services.evals.eval_generator import (
    EvalGenerator,
    get_all_qa_pairs_for_agent,
    get_agent_qa_pairs,
    get_kb_qa_pairs,
)
from super_services.db.services.models.agent_eval import (
    AgentQAPairModel,
    KBQAPairModel,
)
from super_services.voice.models.config import ModelConfig


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])


class EvalGenerationRequest(BaseModel):
    """Request body for generating evals."""
    agent_id: str = Field(..., description="Agent handle/ID")
    force_regenerate: bool = Field(default=False, description="Force regenerate even if QA pairs exist")
    language: Optional[str] = Field(
        default=None,
        description="Language for QA pairs (default: English)",
    )


class EvalGenerationResponse(BaseModel):
    """Response for eval generation request."""
    agent_id: str
    status: str
    message: str


class QAPairResponse(BaseModel):
    """Single QA pair response."""
    question: str
    answer: str
    keywords: List[str]
    source: str = "agent"


class QAPairsListResponse(BaseModel):
    """Response for QA pairs list."""
    agent_id: str
    total_count: int
    agent_qa_count: int
    kb_qa_count: int
    qa_pairs: List[QAPairResponse]


class QAPairsCountResponse(BaseModel):
    """Response for QA pairs count check."""
    agent_id: str
    agent_qa_count: int
    kb_qa_count: int
    total_count: int
    has_qa_pairs: bool


@router.post("/generate", response_model=EvalGenerationResponse)
async def generate_evals(request: EvalGenerationRequest) -> EvalGenerationResponse:
    """
    Trigger eval generation for an agent.

    This endpoint starts an async Prefect flow that:
    1. Fetches agent configuration
    2. Fetches knowledge base documents
    3. Generates QA pairs using OpenAI
    4. Saves QA pairs to MongoDB

    If QA pairs already exist for the agent, generation is skipped unless force_regenerate=True.
    """
    agent_id = request.agent_id
    force_regenerate = request.force_regenerate
    language = request.language

    # Validate agent exists
    try:
        config = ModelConfig().get_config(agent_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {agent_id}"
            )
    except Exception as e:
        logger.error(f"Error validating agent: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error validating agent: {str(e)}"
        )

    # Check if QA pairs already exist (unless force_regenerate)
    if not force_regenerate:
        existing_agent = AgentQAPairModel._get_collection().count_documents({
            "agent_id": agent_id,
            "status": "active"
        })
        if existing_agent > 0:
            return EvalGenerationResponse(
                agent_id=agent_id,
                status="skipped",
                message=f"QA pairs already exist ({existing_agent} pairs). Use force_regenerate=true to regenerate."
            )

    # Trigger Prefect deployment
    try:
        await trigger_deployment(
            "Generate-Agent-Evals",
            {
                "job": {
                    "agent_id": agent_id,
                    "force_regenerate": force_regenerate,
                    "language": language,
                }
            }
        )
    except ValueError as e:
        # Deployment not found - run inline for development/testing
        logger.warning(f"Deployment not found, running inline: {e}")
        try:
            generator = EvalGenerator(
                gen_type="pilot",
                agent_id=agent_id,
                kn_token="",
                logger=logger,
                language=language,
            )
            results = await generator.generate_all_evals(force_regenerate=force_regenerate)
            return EvalGenerationResponse(
                agent_id=agent_id,
                status="completed",
                message=f"Generated {results['total_qa_count']} QA pairs (agent: {results['agent_qa_count']}, kb: {results['kb_qa_count']})"
            )
        except Exception as inline_error:
            logger.error(f"Inline generation failed: {inline_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Eval generation failed: {str(inline_error)}"
            )
    except Exception as e:
        logger.error(f"Error triggering deployment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering eval generation: {str(e)}"
        )

    return EvalGenerationResponse(
        agent_id=agent_id,
        status="pending",
        message="Eval generation started. QA pairs will be available shortly."
    )


@router.get("/check/{agent_id}", response_model=QAPairsCountResponse)
async def check_qa_pairs(agent_id: str) -> QAPairsCountResponse:
    """
    Check if QA pairs exist for an agent.
    Returns count of agent and KB QA pairs.
    """
    try:
        agent_count = AgentQAPairModel._get_collection().count_documents({
            "agent_id": agent_id,
            "status": "active"
        })
        kb_count = KBQAPairModel._get_collection().count_documents({
            "agent_id": agent_id,
            "status": "active"
        })
        total = agent_count + kb_count

        return QAPairsCountResponse(
            agent_id=agent_id,
            agent_qa_count=agent_count,
            kb_qa_count=kb_count,
            total_count=total,
            has_qa_pairs=total > 0
        )
    except Exception as e:
        logger.error(f"Error checking QA pairs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking QA pairs: {str(e)}"
        )


@router.get("/qa-pairs/{agent_id}", response_model=QAPairsListResponse)
async def get_qa_pairs(agent_id: str, source: Optional[str] = None) -> QAPairsListResponse:
    """
    Get all active QA pairs for an agent.

    Args:
        agent_id: Agent handle
        source: Optional filter - "agent" or "kb" to get only specific source
    """
    try:
        if source == "agent":
            agent_pairs = get_agent_qa_pairs(agent_id)
            kb_pairs = []
        elif source == "kb":
            agent_pairs = []
            kb_pairs = get_kb_qa_pairs(agent_id)
        else:
            agent_pairs = get_agent_qa_pairs(agent_id)
            kb_pairs = get_kb_qa_pairs(agent_id)

        all_pairs = agent_pairs + kb_pairs

        return QAPairsListResponse(
            agent_id=agent_id,
            total_count=len(all_pairs),
            agent_qa_count=len(agent_pairs),
            kb_qa_count=len(kb_pairs),
            qa_pairs=[
                QAPairResponse(
                    question=qa["question"],
                    answer=qa["answer"],
                    keywords=qa.get("keywords", []),
                    source=qa.get("source", "agent"),
                )
                for qa in all_pairs
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching QA pairs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching QA pairs: {str(e)}"
        )


@router.delete("/qa-pairs/{agent_id}")
async def delete_qa_pairs(agent_id: str, source: Optional[str] = None, archive: bool = True):
    """
    Delete (or archive) QA pairs for an agent.

    Args:
        agent_id: Agent handle
        source: Optional - "agent" or "kb" to delete only specific source
        archive: If True, mark as archived. If False, permanently delete.
    """
    try:
        results = {"agent_id": agent_id, "agent_deleted": 0, "kb_deleted": 0}

        if source in [None, "agent"]:
            if archive:
                result = AgentQAPairModel._get_collection().update_many(
                    {"agent_id": agent_id, "status": "active"},
                    {"$set": {"status": "archived"}}
                )
                results["agent_deleted"] = result.modified_count
            else:
                result = AgentQAPairModel._get_collection().delete_many(
                    {"agent_id": agent_id}
                )
                results["agent_deleted"] = result.deleted_count

        if source in [None, "kb"]:
            if archive:
                result = KBQAPairModel._get_collection().update_many(
                    {"agent_id": agent_id, "status": "active"},
                    {"$set": {"status": "archived"}}
                )
                results["kb_deleted"] = result.modified_count
            else:
                result = KBQAPairModel._get_collection().delete_many(
                    {"agent_id": agent_id}
                )
                results["kb_deleted"] = result.deleted_count

        action = "Archived" if archive else "Deleted"
        total = results["agent_deleted"] + results["kb_deleted"]
        results["message"] = f"{action} {total} QA pairs (agent: {results['agent_deleted']}, kb: {results['kb_deleted']})"

        return results

    except Exception as e:
        logger.error(f"Error deleting QA pairs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting QA pairs: {str(e)}"
        )


@router.post("/generate-inline")
async def generate_evals_inline(request: EvalGenerationRequest):
    """
    Generate evals inline (synchronously) without Prefect.
    Useful for testing and development.
    """
    agent_id = request.agent_id
    force_regenerate = request.force_regenerate
    language = request.language

    # Validate agent exists
    try:
        config = ModelConfig().get_config(agent_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {agent_id}"
            )
    except Exception as e:
        logger.error(f"Error validating agent: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error validating agent: {str(e)}"
        )

    try:
        generator = EvalGenerator(
            gen_type="pilot",
            agent_id=agent_id,
            kn_token="",
            logger=logger,
            language=language,
        )
        results = await generator.generate_all_evals(force_regenerate=force_regenerate)

        return {
            "agent_id": agent_id,
            "status": "completed",
            "batch_id": results.get("batch_id"),
            "agent_qa_count": results.get("agent_qa_count", 0),
            "kb_qa_count": results.get("kb_qa_count", 0),
            "total_qa_count": results.get("total_qa_count", 0),
            "skipped": results.get("skipped", []),
            "errors": results.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Eval generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Eval generation failed: {str(e)}"
        )
