from libs.core.exceptions import API206Exception
from services.store_service.core.file import getFileExtension
from libs.core.jsondecoder import convertFromBaseModel
from libs.core.model import updateModelInstance

from services.store_service.core.mongo_store import MongoStore
from services.store_service.core.processor import StoreProcessor
from services.store_service.models.collection import (
    CollectionConfigModel,
    CollectionSchemaModel,
)
from services.store_service.models.index import IndexJobModel
from services.store_service.schemas.collection import (
    CollectionFile,
    CollectionStoreConfig,
    CollectionStoreConfigUpdate,
)


def check_if_table(collection_type):
    if collection_type in ["table", "collection", "email", "contact", "evals"]:
        return True
    return False


def get_collection(collection):
    collection_type = collection.get("collection_type")
    token = collection.get("token")
    if check_if_table(collection_type):
        return f"collection_data_{token}"
    else:
        return f"collection_data_{collection_type}"


def check_file_extension(file_name, collection):
    table_extensions = [".csv", ".tsv"]
    collection_type = collection.get("collection_type")
    file_extension = getFileExtension(file_name)
    if collection_type in ["email", "evals"]:
        raise API206Exception(
            {
                "message": f"You can't upload files for this collection type - {collection_type}",
                "success": False,
            }
        )
    if (
        check_if_table(collection_type)
        and file_extension.lower() not in table_extensions
    ) or (
        not check_if_table(collection_type)
        and file_extension.lower() in table_extensions
    ):
        raise API206Exception(
            {
                "message": f"Invalid file extension for this collection type - {collection_type}",
                "success": False,
            }
        )
    return True


def get_collection_query(collection):
    collection_type = collection.get("collection_type")
    token = collection.get("token")
    if check_if_table(collection_type):
        return {}
    else:
        return {"token": token}


def checkCollection(token, raise_ex=False):
    cond = {"token": token}
    obj = CollectionConfigModel.find_one(**cond)
    if not obj and raise_ex:
        raise API206Exception({"message": "Collection not found", "success": False})
    return obj


def getCollectionSchema(collection_id):
    cond = {"collection_id": collection_id}
    obj = CollectionSchemaModel.find_one(**cond)
    return obj


def storeCollectionConfig(data: CollectionStoreConfig):
    collection_obj = checkCollection(data.token)
    if collection_obj:
        return {"message": "Collection already exists", "success": False}
    data = data.model_dump()
    fields = data.pop("fields", {})
    keywords = data.pop("keywords", [])
    schemas = data.pop("schemas", {})
    collection_obj = CollectionConfigModel.save_single_to_db(data)
    fields_schema = {
        "collection_id": str(collection_obj.id),
        "fields": fields,
        "keywords": keywords,
        "schemas": schemas,
        "token": data.get("token"),
        "org_id": data.get("org_id"),
    }
    schema_obj = CollectionSchemaModel.save_single_to_db(fields_schema)
    return {
        "message": "Collection stored successfully",
        "success": True,
        "data": {
            "collection_id": str(collection_obj.id),
            "collection": convertFromBaseModel(collection_obj),
            "schema": convertFromBaseModel(schema_obj),
        },
    }


async def getStoreConfig(token):
    cond = {"token": token}
    obj = CollectionConfigModel.find_one(**cond)
    if obj:
        schema = CollectionSchemaModel.find_one(collection_id=str(obj.get("_id")))
        return {
            "message": "Collection found",
            "success": True,
            "data": {
                "collection_id": str(obj.get("_id")),
                "collection": convertFromBaseModel(obj),
                "schema": convertFromBaseModel(schema),
            },
        }
    return {"message": "Collection not found", "success": False}


async def updateCollectionConfig(data: CollectionStoreConfigUpdate, token: str):
    cond = {"token": token}
    obj = CollectionConfigModel.find_one(**cond)
    if obj:
        data = data.model_dump(exclude_none=True)
        fields = data.pop("fields", {})
        keywords = data.pop("keywords", [])
        schemas = data.pop("schemas", {})
        if data:
            updateModelInstance(CollectionConfigModel, cond, data)
        if fields or keywords or schemas:
            update_data = {}
            if fields:
                update_data["fields"] = fields
            if keywords:
                update_data["keywords"] = keywords
            if schemas:
                update_data["schemas"] = schemas
            cond_schema = {"collection_id": str(obj.get("_id"))}
            updateModelInstance(CollectionSchemaModel, cond_schema, update_data)
        schema = CollectionSchemaModel.find_one(collection_id=str(obj.get("_id")))
        obj = {**obj, **data}
        return {
            "message": "Collection updated successfully",
            "success": True,
            "data": {
                "collection_id": str(obj.get("_id")),
                "collection": convertFromBaseModel(obj),
                "schema": convertFromBaseModel(schema),
            },
        }
    return {"message": "Collection not found", "success": False}


async def processUploadFileOld(file: CollectionFile, token: str):
    from urllib.parse import unquote

    config = checkCollection(token)
    if not config:
        config_data = file.config
        if not config_data:
            return {"message": "Collection not found", "success": False}
        config_data["token"] = token
        config = CollectionStoreConfig(**config_data)
        storeCollectionConfig(config)
        config = checkCollection(token, raise_ex=True)
    file_path = unquote(str(file.url))
    collection_id = get_collection(config)
    db_manager = MongoStore(collection=collection_id)
    processor = StoreProcessor(db_manager)
    res = await processor.process(
        file_path, collection_id, save_log=True, token=token, index=True, config=config
    )
    if res.get("success") is False:
        return res
    return {
        "message": "File uploaded successfully",
        "success": True,
        "data": res,
    }


def updateCollectionSchema(token: str, schema: dict):
    cond = {"token": token}
    obj = CollectionConfigModel.find_one(**cond)
    if obj:
        cond = {
            "org_id": obj.get("org_id"),
            "collection_id": str(obj.get("_id")),
            "token": token,
        }
        schema_obj = CollectionSchemaModel.find_one(**cond)
        if schema_obj:
            current_schema = schema_obj.get("schemas", {})
            current_schema["properties"] = current_schema.get("properties", {})
            current_schema["properties"].update(schema["properties"])

            current_required = current_schema.get("required", [])
            new_required = schema.get("required", [])
            current_schema["required"] = list(set(current_required + new_required))

            if "type" in schema:
                current_schema["type"] = schema["type"]

            save_to_data = {"schemas": current_schema}
            updateModelInstance(CollectionSchemaModel, cond, save_to_data)
        else:
            save_to_data = {**cond, "schemas": schema}
            CollectionSchemaModel.save_single_to_db(save_to_data)
        return {
            "message": "Collection schema updated successfully",
            "success": True,
            "data": convertFromBaseModel(save_to_data),
        }
    return {"message": "Collection not found", "success": False}


async def fetch_collection_data(token: str, limit: int, skip: int):
    collection = checkCollection(token, raise_ex=True)
    collection_id = get_collection(collection)
    db_manager = MongoStore(collection=collection_id)
    processor = StoreProcessor(db_manager)
    filter = get_collection_query(collection)
    res = await processor.fetch_data(limit=limit, skip=skip, token=token, filter=filter)
    return {
        "message": "Collection data fetched successfully",
        "success": True,
        "data": res,
    }


async def check_upload_status(token: str):
    checkCollection(token, raise_ex=True)
    indexing = IndexJobModel.count(token=token, index=False)
    total_count = IndexJobModel.count(token=token)
    return {
        "message": "Upload status checked successfully",
        "success": True,
        "data": {"indexing": indexing, "total_count": total_count},
    }
