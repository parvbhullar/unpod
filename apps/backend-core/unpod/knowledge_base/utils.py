from bson import ObjectId
from django.conf import settings
import requests

from unpod.common.file import getFileExtension
from unpod.common.mongodb import MongoDBQueryManager
from unpod.common.pagination import getPagination


def check_if_table(content_type):
    if content_type in ["table", "collection", "email", "contact"]:
        return True
    return False


def check_file_extension(file_name, content_type):
    file_extension = getFileExtension(file_name)
    table_allowed_extensions = [".csv", ".xls", "xlsx", ".tsv"]
    if (
        check_if_table(content_type) and file_extension not in table_allowed_extensions
    ) or (
        not check_if_table(content_type) and file_extension in table_allowed_extensions
    ):
        return False
    return True


def get_collection(token, collection_type):
    if check_if_table(collection_type):
        return f"collection_data_{token}"
    else:
        return f"collection_data_{collection_type}"


def get_collection_type(collection_type):
    if collection_type in ["general"]:
        return "document"
    return collection_type


def create_store_config(space_obj, schema_data):
    fields = {}
    # for s in schema_data:
    #     fields[s["name"]] = s
    config_data = {
        "name": space_obj.name,
        "desc": space_obj.description or space_obj.name,
        "collection_type": get_collection_type(space_obj.content_type),
        "org_id": space_obj.space_organization.id,
        "token": space_obj.token,
        "fields": fields,
        "schemas": schema_data,
    }
    print(config_data)
    url = f"{settings.API_SERVICE_URL}/store/config/"
    res = requests.post(url, json=config_data, timeout=30)
    res.raise_for_status()
    return res.json()


def upload_store_file(space_obj, file_obj: dict):
    token = space_obj.token
    url = f"{settings.API_SERVICE_URL}/store/upload-file/{token}/"
    config_data = {
        "name": space_obj.name,
        "desc": space_obj.description or space_obj.name,
        "collection_type": get_collection_type(space_obj.content_type),
        "org_id": space_obj.space_organization.id,
        "token": space_obj.token,
        "fields": {},
    }
    file_obj["config"] = config_data
    res = requests.post(url, json=file_obj, timeout=30)
    res.raise_for_status()
    res = res.json()
    if res.get("success") is False:
        print("upload_store_file_res", res, file_obj)
    return res


def process_store_config(store_data):
    from unpod.common.file import getS3FileURLFromURL

    space = store_data.pop("space", None)
    files = store_data.pop("files", [])
    create_store_config(space, store_data.get("schema", {}))
    for file in files:
        upload_store_file(space, {"url": getS3FileURLFromURL(file.file.url)})


def update_store_schema(space_obj, schema_data):
    token = space_obj.token
    url = f"{settings.API_SERVICE_URL}/store/config/{token}/"
    config_data = {
        "schemas": schema_data,
    }
    res = requests.put(url, json=config_data, timeout=30)
    res.raise_for_status()
    return res.json()


def get_document_tasks(document_id: str, query_params: dict):
    """
    Fetch tasks related to a specific document ID from the MongoDB collection.
    Args:
        document_id (str): The ID of the document to fetch tasks for.
        query_params (dict): Query parameters for pagination (e.g., skip, limit).
    Returns:
        tuple: A tuple containing the total count of tasks and a list of task documents.
    """
    collection_name = "tasks"
    skip, limit = getPagination(query_params)
    query = {"ref_id": document_id}
    exclude_fields = [
        "space_id",
        "retry_attempt",
        "thread_id",
        "user_org_id",
        "collection_ref",
    ]
    projection = {field: 0 for field in exclude_fields}

    collection = MongoDBQueryManager.get_collection(collection_name)
    cursor = (
        collection.find(query, projection, sort=[("_id", -1)]).skip(skip).limit(limit)
    )
    total_count = collection.count_documents(query)
    documents = list(cursor)

    for doc in documents:
        doc_id = str(doc.pop("_id"))
        doc["id"] = doc_id

        if "created" not in doc:
            doc["created"] = ObjectId(doc_id).generation_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

    return total_count, documents
