import os
import uuid
import inflection
from datetime import datetime, timezone
from collections import OrderedDict

from libs.core.exceptions import API206Exception
from libs.core.datetime import (
    convert_str_to_datetime,
    get_datetime_now,
)
from libs.core.jsondecoder import convertFromMongo, json_dumps
from services.store_service.schemas.document import CreateDocumentSchema
from services.store_service.core.file_parser import FileParser
from services.store_service.core.file import compute_sha1_from_content


async def process_gmail_creation(doc_data, config, collection_id, db_manager):
    document_id = doc_data.get("document_id", None)
    if "_id" in doc_data:
        del doc_data["_id"]
    if "date" in doc_data and isinstance(doc_data["date"], str):
        doc_data["date"] = convert_str_to_datetime(doc_data["date"])
    try:
        result = db_manager.collection.insert_one(doc_data)
        doc_data.pop("_id", None)
        if result.inserted_id:
            return {
                "message": "Document created successfully",
                "success": True,
                "data": {
                    "document_id": document_id,
                    **convertFromMongo(doc_data),
                },
            }
    except Exception as ex:
        return {"message": f"Failed to create document: {str(ex)}", "success": False}


async def process_contact_creation(doc_data, config, collection_id, db_manager):
    if "_id" in doc_data:
        del doc_data["_id"]
    if "created" not in doc_data:
        doc_data["created"] = get_datetime_now(utc=True)
    try:
        result = db_manager.collection.insert_one(doc_data)
        doc_data.pop("_id", None)
        if result.inserted_id:
            return {
                "message": "Document created successfully",
                "success": True,
                "data": {
                    "document_id": str(result.inserted_id),
                    **convertFromMongo(doc_data),
                },
            }
    except Exception as ex:
        return {"message": f"Failed to create document: {str(ex)}", "success": False}


async def process_doc_creation(doc_data, config, collection_id, db_manager):
    file_parser = FileParser()
    collection_type = config.get("collection_type")
    if collection_type != "document":
        raise API206Exception({"message": "Invalid collection type", "success": False})
    try:
        doc = CreateDocumentSchema(**doc_data)
    except Exception as ex:
        raise API206Exception({"message": str(ex), "success": False})
    kwargs = {
        "save_log": True,
        "token": config.get("token"),
        "index": True,
        "config": config,
    }
    final_res = {"total": 0, "success": 0, "failed": 0, "errors": []}
    insert_data = OrderedDict()
    attachments_data = []
    index_jobs = []
    current_time = datetime.now(timezone.utc)
    parent_id = uuid.uuid1().hex
    final_res["total"] = doc.files.__len__()
    for file in doc.files:
        file_path = file.get("url")
        title = file.get("name")
        media_relation = file.get("media_relation", None)
        media_type = file.get("media_type", None)
        file_name = inflection.underscore(os.path.basename(file_path)).replace(" ", "_")
        _, extension = os.path.splitext(file_name)
        processed_data = {"success": False, "data": {"error": "File processing failed"}}
        try:
            processed_data = await file_parser.read_data_file(
                file_path, collection_id, **kwargs
            )
        except RuntimeError as ex:
            processed_data = {"success": False, "data": {"error": str(ex)}}
        file_sha1 = processed_data.get("file_sha1", None)
        is_success = processed_data.get("success", False)
        if not is_success:
            error_message = processed_data.get("data", {}).get("error", None)
            final_res["failed"] += 1
            final_res["errors"].append(
                {
                    "file": file_name,
                    "error": error_message,
                }
            )
        data = processed_data.get("data", {}).get("docs", [])
        schema = processed_data.get("data", {}).get("columns", {})
        created_date = doc.metadata.get("date", None)
        if created_date:
            created_date = convert_str_to_datetime(created_date)
        else:
            created_date = current_time
        for d in data:
            d["content_hash"] = compute_sha1_from_content(json_dumps(d).encode())
            d["file_name"] = file_name
            d["name"] = title
            d["file_sha1"] = file_sha1
            d["url"] = file_path
            final_res["success"] += 1
            if media_relation == "content":
                d["created"] = created_date
                d["token"] = config.get("token", None)
                d["org_id"] = config.get("org_id", None)
                d["meta"] = doc.metadata
                d["meta"]["parent_id"] = parent_id
                d["meta"]["url"] = file_path
                d["meta"].update(
                    {
                        "media_relation": media_relation,
                        "media_type": media_type,
                    }
                )
                insert_data[title] = d
            else:
                attachments_data.append(d)
            if extension and is_success:
                index_jobs.append(
                    {
                        "file_path": file_path,
                        "file_sha1": file_sha1,
                        "schema": schema,
                        "token": config.get("token", None),
                        "org_id": config.get("org_id", None),
                        "upload": True,
                        "upload_at": int(created_date.timestamp()),
                        "meta": {
                            "media_relation": media_relation,
                            "media_type": media_type,
                        },
                    }
                )
    if insert_data:
        first_key = next(iter(insert_data))
        insert_data[first_key]["attachments"] = attachments_data
        insert_data = list(insert_data.values())
        db_manager.save_data(insert_data)
    if index_jobs:
        from services.store_service.models.index import IndexJobModel

        IndexJobModel.save_many_to_db(index_jobs)
    return {
        "message": "Document created successfully",
        "success": True,
        "data": final_res,
    }
