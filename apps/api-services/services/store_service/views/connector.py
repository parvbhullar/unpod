from libs.core.exceptions import API206Exception
from libs.api.logger import get_logger
from libs.core.jsondecoder import convertFromMongo

app_logging = get_logger("store_service")
from services.store_service.schemas.collection import (
    CollectionStoreConfig,
    BulkUpdateItem,
)
from services.store_service.utils.query import get_document_id_query
from services.store_service.views.collection import (
    checkCollection,
    get_collection,
    getCollectionSchema,
    storeCollectionConfig,
)
from services.store_service.core.mongo_store import MongoStore
from typing import List, Dict
from pymongo import UpdateOne  # Add this import at the top


def fetch_email_data(
    db_manager: MongoStore, token: str, limit: int, skip: int, query_params: dict
):
    search: str = query_params.get("search", "")
    tag: str = query_params.get("tag", "")
    from_ts = query_params.get("from_ts", None)
    doc_ids: str = query_params.get("doc_ids", "")
    if tag:
        tag = tag.replace("-", " ")
    if from_ts:
        try:
            from_ts = int(from_ts)
        except Exception as ex:
            from_ts = None
    aggregate_query = [
        {"$sort": {"date_ts": 1}},
        {
            "$group": {
                "_id": "$email_threadId",
                "count": {"$sum": 1},
                "meta": {"$first": "$meta"},
                "date_ts": {"$first": "$date_ts"},
                "date": {"$first": "$date"},
            }
        },
        {"$sort": {"date_ts": -1}},
        {
            "$project": {
                "_id": 0,
                "parent_id": "$_id",
                "document_id": "$_id",
                "count": 1,
                "date_ts": 1,
                "date": 1,
                "title": "$meta.title",
                "description": "$meta.description",
                "user": "$meta.user",
            }
        },
        {"$skip": skip},
        {"$limit": limit},
    ]
    if search and tag:
        aggregate_query.insert(
            0,
            {
                "$match": {
                    "$and": [
                        {"$text": {"$search": search}},
                        {"labels": {"$regex": tag, "$options": "i"}},
                    ]
                }
            },
        )
    elif search:
        aggregate_query.insert(
            0,
            {"$match": {"$text": {"$search": search}}},
        )
    elif tag:
        aggregate_query.insert(
            0, {"$match": {"labels": {"$regex": tag, "$options": "i"}}}
        )
    if from_ts:
        aggregate_query.insert(0, {"$match": {"date_ts": {"$gte": from_ts}}})

    if doc_ids:
        aggregate_query.insert(
            0, {"$match": {"document_id": {"$in": doc_ids.split(",")}}}
        )
    data = list(db_manager.collection.aggregate(aggregate_query))
    count = list(db_manager.collection.distinct("email_threadId")).__len__()
    return data, count


def timestamp_to_objectID(timestamp):
    from datetime import datetime, timezone
    from bson import ObjectId

    try:
        dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    except Exception as ex:
        raise API206Exception(
            {
                "message": f"Invalid Timestamp filter value, Got {timestamp}",
                "success": False,
            }
        )
    return ObjectId.from_datetime(dt)


def build_contact_filter(search: str, tag: str, from_ts: int, to_ts: int) -> Dict:
    filter_query = {}

    if search:
        filter_query["$or"] = [
            {"contact_name": {"$regex": search, "$options": "i"}},
            {"contact_number": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]

    if tag:
        filter_query["labels"] = {"$regex": tag, "$options": "i"}

    # Timestamp range filter
    if from_ts or to_ts:
        ts_filter = {}
        if from_ts:
            from_ts_obj = timestamp_to_objectID(from_ts)
            ts_filter["$gte"] = from_ts_obj
        if to_ts:
            to_ts_obj = timestamp_to_objectID(to_ts)
            ts_filter["$lte"] = to_ts_obj
        filter_query["_id"] = ts_filter

    return filter_query


def fetch_contact_data(
    db_manager: MongoStore, token: str, limit: int, skip: int, query_params: dict
):
    from bson import ObjectId

    tag: str = query_params.get("tag", "").replace("-", " ")
    search: str = query_params.get("search", "")
    app_logging.debug("fetch_contact_data_tag", tag)
    from_ts = query_params.get("from_ts", None)
    to_ts = query_params.get("to_ts", None)
    fetch_all = query_params.get("fetch_all", None)

    filter_query = build_contact_filter(search, tag, from_ts, to_ts)

    extra_fields = ["content_hash", "file_name", "file_sha1"]

    aggregate_query = [
        {"$sort": {"_id": -1}},
        {"$skip": skip},
    ]
    if not (fetch_all and fetch_all == "1"):
        aggregate_query.append({"$limit": limit})

    aggregate_query.append({"$project": {key: 0 for key in extra_fields}})
    if filter_query:
        aggregate_query.insert(0, {"$match": filter_query})
    data = list(db_manager.collection.aggregate(aggregate_query))
    for d in data:
        obj_id = d.pop("_id")
        d["title"] = d.get("contact_number")
        d["description"] = d.get("contact_name") or d.get("name")
        d["document_id"] = d.get("document_id") or str(obj_id)
        if "created" not in d:
            d["created"] = ObjectId(obj_id).generation_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
    count = db_manager.collection.count_documents(filter_query)
    return data, count


def fetch_document_data(
    db_manager: MongoStore, token: str, limit: int, skip: int, query_params: dict
):
    from bson import ObjectId

    extra_fields = ["content_hash", "file_name", "file_sha1", "token", "org_id"]
    query = {"token": token}
    aggregate_query = [
        {"$match": query},
        {"$sort": {"_id": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$project": {key: 0 for key in extra_fields}},
    ]
    data = list(db_manager.collection.aggregate(aggregate_query))
    for d in data:
        obj_id = d.pop("_id")
        meta = d.get("meta", {})
        d["title"] = meta.get("title") or d.get("name")
        d["description"] = meta.get("description")
        d["document_id"] = d.get("document_id") or str(obj_id)
        d["parent_id"] = meta.get("parent_id")
        if "created" not in d:
            d["created"] = ObjectId(obj_id).generation_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
    count = db_manager.collection.count_documents({})
    return data, count


async def fetch_collector_based_data(
    token: str, limit: int, skip: int, query_params: dict
):
    collection = checkCollection(token)
    if not collection:
        return {
            "message": "Collection data fetched successfully",
            "success": True,
            "data": {
                "data": [],
                "schema": {},
            },
            "count": -1,
        }
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)
    collection_type = collection.get("collection_type")

    method_map = {
        "email": fetch_email_data,
        "contact": fetch_contact_data,
        "document": fetch_document_data,
    }

    method = method_map.get(collection_type)
    if not method:
        return {"message": "Collection type not supported", "success": False}
    data, count = method(db_manager, token, limit, skip, query_params)
    schema = getCollectionSchema(str(collection.get("_id")))
    res_data = {
        "data": data,
        "schema": schema.get("schemas", {}),
    }
    return {
        "message": "Collection data fetched successfully",
        "success": True,
        "data": res_data,
        "count": count,
    }


async def fetch_email_info(db_manager: MongoStore, document_id: str):
    query = {"meta.parent_id": document_id}
    data = convertFromMongo(
        list(db_manager.collection.find(query, sort=[("date_ts", 1)]))
    )
    return data


async def fetch_contact_info(db_manager: MongoStore, document_id: str):
    from bson import ObjectId

    query = get_document_id_query(document_id)
    data = convertFromMongo(db_manager.collection.find_one(query, sort=[("_id", -1)]))
    if data:
        data["document_id"] = str(data.get("id"))
        obj_id = data.pop("id")
        if "created" not in data:
            data["created"] = ObjectId(obj_id).generation_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
    return data or {}


async def fetch_document_info(db_manager: MongoStore, document_id: str):
    query = get_document_id_query(document_id)
    data = convertFromMongo(db_manager.collection.find_one(query))
    if data:
        if "document_id" not in data:
            data["document_id"] = str(data.get("id"))
        data["title"] = data.get("meta", {}).get("title") or data.get("name")
    return data or {}


async def fetch_doc_info(token: str, document_id: str):
    collection = checkCollection(token, raise_ex=True)
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)
    collection_type = collection.get("collection_type")
    method_map = {
        "email": fetch_email_info,
        "contact": fetch_contact_info,
        "document": fetch_document_info,
    }

    method = method_map.get(collection_type)
    if not method:
        return {"message": "Collection type not supported", "success": False}
    res = await method(db_manager, document_id)
    return {
        "message": "Doc data fetched successfully",
        "success": True,
        "data": res,
    }


async def update_doc_info(token: str, document_id: str, update_data: dict):
    collection = checkCollection(token, raise_ex=True)
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)

    query = get_document_id_query(document_id)
    # Remove any attempts to update _id field
    if "_id" in update_data:
        del update_data["_id"]
    if "document_id" in update_data:
        del update_data["document_id"]
    if "id" in update_data:
        del update_data["id"]  # Prevent changing document_id

    result = db_manager.collection.update_one(query, {"$set": update_data})

    if result.matched_count > 0:
        return {
            "message": "Document updated successfully",
            "success": True,
        }
    return {
        "message": "Document not found or no changes made",
        "success": False,
    }


async def delete_doc_info(token: str, document_id: str):
    collection = checkCollection(token, raise_ex=True)
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)

    query = get_document_id_query(document_id)

    result = db_manager.collection.delete_one(query)

    if result.deleted_count > 0:
        return {
            "message": "Document deleted successfully",
            "success": True,
        }
    return {
        "message": "Document not found",
        "success": False,
    }


async def create_doc_info(token: str, doc_data: dict):
    config = checkCollection(token)
    config_data = doc_data.pop("config", {})
    if not config:
        if not config_data:
            return {"message": "Collection not found", "success": False}
        config_data["token"] = token
        config = CollectionStoreConfig(**config_data)
        storeCollectionConfig(config)
        config = checkCollection(token, raise_ex=True)
    collection_id = get_collection(config)
    db_manager = MongoStore(collection=collection_id)

    from services.store_service.views.create_doc import (
        process_contact_creation,
        process_doc_creation,
        process_gmail_creation,
    )

    doc_method = {
        "contact": process_contact_creation,
        "document": process_doc_creation,
        "email": process_gmail_creation,
    }
    method = doc_method.get(config.get("collection_type"))
    if not method:
        return {"message": "Collection type not supported", "success": False}
    try:
        return await method(doc_data, config, collection_id, db_manager)
    except Exception as ex:
        return {"message": f"Failed to create document: {str(ex)}", "success": False}


async def index_doc(db_manager: MongoStore, document_id: str, data: dict):
    """
    Index a document with the given data. This method should be implemented
    according to your indexing requirements.
    """
    # TODO: Implement actual indexing logic
    raise NotImplementedError("Document indexing not yet implemented")


async def bulk_update_docs(token: str, updates: List[BulkUpdateItem]):
    collection = checkCollection(token, raise_ex=True)
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)

    bulk_operations = []
    index_operations = []

    for update in updates:
        if update.action == "index":
            index_operations.append((update.document_id, update.data))
            continue

        # Handle edit operations
        query = get_document_id_query(update.document_id)
        update_data = {}
        array_updates = {}

        for key, value in update.data.model_dump(
            exclude_defaults=True, exclude_unset=True, exclude_none=True
        ).items():
            if isinstance(value, str):
                update_data[key] = value
            elif isinstance(value, list):
                array_updates[key] = value

        # Combine both types of updates into a single UpdateOne operation
        update_dict = {}
        if update_data:
            update_dict["$set"] = update_data
        if array_updates:
            update_dict["$addToSet"] = {
                key: {"$each": values} for key, values in array_updates.items()
            }
        app_logging.debug("update_dict", update_dict)
        if update_dict:
            bulk_operations.append(
                UpdateOne(filter=query, update=update_dict, upsert=True)
            )

    results = {
        "success": True,
        "message": "Operations completed",
        "edit_results": None,
        "index_results": None,
    }

    # Process edit operations
    if bulk_operations:
        try:
            edit_result = db_manager.collection.bulk_write(bulk_operations)
            results["edit_results"] = {
                "modified_count": edit_result.modified_count,
                "matched_count": edit_result.matched_count,
            }
        except Exception as e:
            results["success"] = False
            results["message"] = f"Bulk edit operations failed: {str(e)}"
            return results

    # Process index operations
    if index_operations:
        try:
            index_results = []
            for doc_id, data in index_operations:
                try:
                    await index_doc(db_manager, doc_id, data)
                    index_results.append({"document_id": doc_id, "success": True})
                except Exception as e:
                    index_results.append(
                        {"document_id": doc_id, "success": False, "error": str(e)}
                    )
            results["index_results"] = index_results
        except Exception as e:
            if results["success"]:  # Only update if not already failed
                results["success"] = False
                results["message"] = f"Index operations failed: {str(e)}"

    if not bulk_operations and not index_operations:
        return {"message": "No valid operations found", "success": False}

    return results
