import json
import uuid
from datetime import datetime, timezone

from libs.api.logger import get_logger
from services.search_service.models.chat import ChatSessionModel
from services.search_service.core.llm import llm_stream
from services.search_service.core.search import (
    mongo_text_search,
    mongo_doc_search,
    mongo_agent_search,
    mongo_chunk_search,
    filter_docs,
    _resolve_collection_names,
)

app_logging = get_logger("search_service")

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the provided context documents to answer "
    "the user's question. If you cannot find the answer in the context, say so. "
    "Be concise and accurate."
)


def _build_context_prompt(docs):
    """Build context string from retrieved documents for LLM."""
    if not docs:
        return ""
    parts = []
    for i, doc in enumerate(docs, 1):
        name = doc.get("semantic_identifier", "")
        content = doc.get("content", "")
        if content:
            parts.append(f"[Document {i}: {name}]\n{content}\n")
    return "\n".join(parts)


async def perform_search(
    thread_id, user_id, query, kn_token=None, hub_id=None, source_type=None
):
    """
    Main search + chat endpoint.
    Gets/creates chat session, searches documents, streams LLM response.
    Yields JSON lines matching the old streaming format.
    """
    if kn_token is None:
        kn_token = []

    # Get or create chat session
    session = ChatSessionModel.find_one(thread_id=thread_id)
    if not session:
        description = f"Chat Session {thread_id} - {user_id}"
        session_data = {
            "thread_id": thread_id,
            "user_id": user_id,
            "description": description,
            "messages": [],
        }
        session = ChatSessionModel.save_single_to_db(session_data)

    # Build search filters
    filters = {}
    if source_type:
        filters["source_type"] = [source_type]

    # Resolve collection names from kn_tokens
    collection_names = []
    if kn_token:
        collection_names = _resolve_collection_names(kn_token)
    if not collection_names:
        collection_names = ["collection_data_document"]

    # Search documents
    docs = []
    if query:
        docs = mongo_text_search(
            query, collection_names, filters=filters, limit=15, skip=0
        )

    # Yield retrieved documents
    yield json.dumps({"top_documents": docs}) + "\n"

    # Build messages for LLM
    context = _build_context_prompt(docs)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add chat history from session (last 10 messages for context)
    session_messages = []
    if session and hasattr(session, "messages"):
        session_messages = session.messages or []
    elif session and isinstance(session, dict):
        session_messages = session.get("messages", [])

    for msg in session_messages[-10:]:
        messages.append(
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        )

    # Add context + user query
    if context:
        user_msg = f"Context:\n{context}\n\nQuestion: {query}"
    else:
        user_msg = query
    messages.append({"role": "user", "content": user_msg})

    # Stream LLM response
    full_answer = ""
    try:
        for token in llm_stream(messages):
            full_answer += token
            yield json.dumps({"answer_piece": token}) + "\n"
    except Exception as e:
        app_logging.error(f"LLM streaming failed: {e}")
        error_msg = "I'm sorry, I encountered an error while generating a response."
        full_answer = error_msg
        yield json.dumps({"answer_piece": error_msg}) + "\n"

    # Build final message detail
    message_id = uuid.uuid4().hex
    message_detail = {
        "message_id": message_id,
        "message": full_answer,
        "context_docs": {"top_documents": docs},
        "message_type": "assistant",
        "time_sent": datetime.now(timezone.utc).isoformat(),
    }
    yield json.dumps({"message_detail": message_detail}) + "\n"

    # Save messages to chat session
    now = datetime.now(timezone.utc).isoformat()
    new_messages = session_messages + [
        {"role": "user", "content": query, "timestamp": now},
        {"role": "assistant", "content": full_answer, "timestamp": now},
    ]
    try:
        session_id = None
        if hasattr(session, "id"):
            session_id = session.id
        elif isinstance(session, dict):
            session_id = session.get("_id") or session.get("id")
        if session_id:
            from mongomantic.core.database import MongomanticClient
            from bson import ObjectId

            db = MongomanticClient.db
            db["chat_sessions"].update_one(
                {"_id": ObjectId(str(session_id))},
                {"$set": {"messages": new_messages}},
            )
    except Exception as e:
        app_logging.error(f"Failed to save chat messages: {e}")


async def get_agent_search_tool(data, skip, limit):
    """Search for AI agents with tag filters."""
    query = data.pop("query", "")
    tags_filter = []

    for key, value in data.items():
        if value:
            if key == "kn_token":
                value = ",".join(value)
            if key == "handle":
                key = "document_id"
                value = ",".join([f"AI_AGENT__{handle}" for handle in value])
            tags_filter.append({"tag_key": key, "tag_value": value})

    results = mongo_agent_search(query, tags_filter, limit=limit, skip=skip)
    return results


async def search_doc_tool(query, kn_token, skip, limit):
    """Search documents with kn_token filter, return search_response_summary format."""
    results = mongo_doc_search(query, kn_token, limit=limit, skip=skip)
    filtered = filter_docs(results)
    return {
        "search_response_summary": {
            "top_sections": filtered,
            "rephrased_query": None,
        }
    }


async def search_docs_chunk(kn_token, skip, limit):
    """Fetch document chunks by kn_token."""
    results = mongo_chunk_search(kn_token, limit=limit, skip=skip)
    return results
