from typing import Optional
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request

from services.search_service.views.search import (
    perform_search,
    get_agent_search_tool,
    search_doc_tool,
    search_docs_chunk,
)
from libs.core.jsondecoder import customResponse
from libs.core.pagination import getPagination

router = APIRouter()


class SearchQuery(BaseModel):
    thread_id: str
    user_id: str
    query: str
    hub_id: Optional[str] = None
    kn_token: Optional[list[str]] = Field(default_factory=list)
    source_type: Optional[str] = None


class SearchAgent(BaseModel):
    query: str
    hub_id: Optional[str] = None
    kn_token: Optional[list[str]] = Field(default_factory=list)
    handle: Optional[list[str]] = Field(default_factory=list)
    privacy_type: Optional[str] = None


class SearchAgentData(BaseModel):
    blurb: str
    content: str
    source_type: str
    document_id: str
    semantic_identifier: str
    metadata: dict


class SearchAgentResponse(BaseModel):
    data: list[SearchAgentData]


class SearchDocs(BaseModel):
    query: str
    kn_token: Optional[list[str]] = Field(default_factory=list)


class ChunkSearchDocs(BaseModel):
    kn_token: list[str] = Field(default_factory=list)


@router.get("/health/")
async def health(request: Request):
    return customResponse({"status": 200}, False)


@router.post("/query/")
async def query(
    request: Request,
    data: SearchQuery,
):
    packets = perform_search(
        data.thread_id,
        data.user_id,
        data.query,
        kn_token=data.kn_token,
        hub_id=data.hub_id,
        source_type=data.source_type,
    )
    return StreamingResponse(
        packets,
        media_type="application/json",
    )


@router.post("/query/agents/")
async def query_agents(
    request: Request,
    data: SearchAgent,
):
    skip, limit = getPagination(request)
    results = await get_agent_search_tool(
        data.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True),
        skip,
        limit,
    )
    return {"data": results}


@router.post("/query/docs/")
async def query_documents(
    request: Request,
    data: SearchDocs,
):
    skip, limit = getPagination(request)
    results = await search_doc_tool(data.query, data.kn_token, skip, limit)
    return {"data": results}


@router.post("/chunk/docs/")
async def query_document_chunks(
    request: Request,
    data: ChunkSearchDocs,
):
    if data.kn_token is None or len(data.kn_token) == 0:
        return {"data": [], "error": "kn_token is required"}
    if "string" in data.kn_token:
        return {"data": [], "error": "string is not valid kn_token"}
    if len(data.kn_token) != len(set(data.kn_token)):
        return {"data": [], "error": "There should be no duplicate kn_tokens passed"}
    skip, limit = getPagination(request)
    results = await search_docs_chunk(data.kn_token, skip, limit)
    return {"data": results}
