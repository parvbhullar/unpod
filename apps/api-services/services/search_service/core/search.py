import os
from datetime import datetime

from mongomantic.core.database import MongomanticClient
from libs.api.logger import get_logger

app_logging = get_logger("search_service")

FILTER_THRESHOLD = float(os.environ.get("FILTER_THRESHOLD", 0.5))


def get_mongo_db():
    return MongomanticClient.db


def ensure_text_indexes(collection):
    """Ensure text indexes exist on content and name fields."""
    try:
        existing = collection.index_information()
        has_text = any(
            idx.get("textScoreOrder")
            or any("_fts" in str(v) for v in idx.get("key", []))
            for idx in existing.values()
        )
        if not has_text:
            collection.create_index(
                [("content", "text"), ("name", "text")],
                background=True,
            )
    except Exception as e:
        app_logging.debug("Could not create text index", str(e))


def build_search_result(doc, score=None):
    """Convert a MongoDB document to standardized search result format."""
    doc_id = doc.get("document_id") or str(doc.get("_id", ""))
    content = doc.get("content", "")
    name = doc.get("name") or doc.get("semantic_identifier") or ""
    meta = doc.get("meta", {}) or doc.get("metadata", {}) or {}
    source_type = doc.get("source_type", "file")
    updated_at = doc.get("updated_at") or doc.get("created")
    if isinstance(updated_at, datetime):
        updated_at = updated_at.isoformat()

    return {
        "document_id": doc_id,
        "blurb": content[:200] if content else "",
        "content": content,
        "source_type": source_type,
        "semantic_identifier": name or meta.get("title", ""),
        "metadata": meta,
        "score": score,
        "match_highlights": [],
        "updated_at": updated_at,
    }


def _resolve_collection_names(kn_tokens):
    """Resolve kn_tokens to MongoDB collection names using CollectionConfigModel."""
    from services.store_service.models.collection import CollectionConfigModel

    collection_names = []
    for token in kn_tokens:
        config = CollectionConfigModel.find_one(token=token)
        if config:
            collection_type = config.get("collection_type")
            if collection_type in ["table", "collection", "email", "contact"]:
                collection_names.append(f"collection_data_{token}")
            else:
                collection_names.append(f"collection_data_{collection_type}")
        else:
            collection_names.append(f"collection_data_{token}")
    return list(set(collection_names))


def mongo_text_search(query, collection_names, filters=None, limit=15, skip=0):
    """
    Run MongoDB $text search across specified collections.
    Returns list of standardized search results sorted by textScore.
    """
    db = get_mongo_db()
    all_results = []

    for coll_name in collection_names:
        collection = db[coll_name]
        ensure_text_indexes(collection)

        pipeline = []

        # Text search match
        match_stage = {"$text": {"$search": query}}

        # Apply additional filters
        if filters:
            if filters.get("source_type"):
                match_stage["source_type"] = {"$in": filters["source_type"]}
            if filters.get("token"):
                match_stage["token"] = filters["token"]
            if filters.get("document_id"):
                if isinstance(filters["document_id"], list):
                    match_stage["document_id"] = {"$in": filters["document_id"]}
                else:
                    match_stage["document_id"] = filters["document_id"]
            if filters.get("exclude_source_type"):
                match_stage["source_type"] = {"$nin": filters["exclude_source_type"]}

        pipeline.append({"$match": match_stage})
        pipeline.append({"$addFields": {"text_score": {"$meta": "textScore"}}})
        pipeline.append({"$sort": {"text_score": -1}})
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        try:
            results = list(collection.aggregate(pipeline))
            for doc in results:
                score = doc.pop("text_score", 0)
                result = build_search_result(doc, score=score)
                all_results.append(result)
        except Exception as e:
            app_logging.error(f"Text search failed on {coll_name}: {e}")

    # Sort all results by score descending
    all_results.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
    return all_results[:limit]


def mongo_doc_search(query, kn_tokens, limit=15, skip=0):
    """Search documents filtered by kn_tokens."""
    if not kn_tokens:
        return []

    collection_names = _resolve_collection_names(kn_tokens)
    if not collection_names:
        return []

    filters = {}
    return mongo_text_search(
        query, collection_names, filters=filters, limit=limit, skip=skip
    )


def mongo_agent_search(query, tags_filter, limit=15, skip=0):
    """Search for agent documents with tag filters."""
    db = get_mongo_db()
    all_results = []

    # Agent documents can be stored in various collections
    # Search the main document collection
    collection_names = ["collection_data_document"]

    # Parse tag filters
    filters = {"source_type": ["ai_agent"]}
    document_ids = []
    kn_tokens = []

    for tag in tags_filter:
        key = tag.get("tag_key", "")
        value = tag.get("tag_value", "")
        if key == "document_id" and value:
            document_ids = [v.strip() for v in value.split(",")]
        elif key == "kn_token" and value:
            kn_tokens = [v.strip() for v in value.split(",")]
        elif key == "privacy_type" and value:
            filters["privacy_type"] = value

    if document_ids:
        filters["document_id"] = document_ids

    if kn_tokens:
        extra_collections = _resolve_collection_names(kn_tokens)
        collection_names = list(set(collection_names + extra_collections))

    if query:
        return mongo_text_search(
            query, collection_names, filters=filters, limit=limit, skip=skip
        )

    # If no query, just filter
    db_instance = get_mongo_db()
    for coll_name in collection_names:
        collection = db_instance[coll_name]
        match_filter = {}
        if filters.get("source_type"):
            match_filter["source_type"] = {"$in": filters["source_type"]}
        if filters.get("document_id"):
            match_filter["document_id"] = {"$in": filters["document_id"]}

        try:
            docs = list(
                collection.find(match_filter).sort("_id", -1).skip(skip).limit(limit)
            )
            for doc in docs:
                result = build_search_result(doc, score=1.0)
                all_results.append(result)
        except Exception as e:
            app_logging.error(f"Agent search failed on {coll_name}: {e}")

    return all_results[:limit]


def mongo_chunk_search(kn_tokens, limit=15, skip=0):
    """Fetch documents by kn_token, excluding ai_agent source type."""
    if not kn_tokens:
        return []

    collection_names = _resolve_collection_names(kn_tokens)
    if not collection_names:
        return []

    db = get_mongo_db()
    all_results = []

    for coll_name in collection_names:
        collection = db[coll_name]
        match_filter = {"source_type": {"$ne": "ai_agent"}}

        try:
            docs = list(
                collection.find(match_filter).sort("_id", -1).skip(skip).limit(limit)
            )
            for doc in docs:
                result = build_search_result(doc, score=1.0)
                all_results.append(result)
        except Exception as e:
            app_logging.error(f"Chunk search failed on {coll_name}: {e}")

    return all_results[:limit]


def filter_docs(results):
    """Filter results by score threshold and sort by score descending."""
    ranked = sorted(results, key=lambda x: x.get("score", 0) or 0, reverse=True)
    return [doc for doc in ranked if (doc.get("score", 0) or 0) > FILTER_THRESHOLD]
