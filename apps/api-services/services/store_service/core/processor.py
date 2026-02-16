import os
import time
import inflection
import pandas as pd
import re
from datetime import datetime, timezone

from libs.core.jsondecoder import convertFromMongo, json_dumps
from libs.api.logger import get_logger

app_logging = get_logger("store_service")


class Chunker:
    @staticmethod
    def chunk_text(text, chunk_size=1000):
        import nltk
        from nltk.tokenize import sent_tokenize

        nltk.download("punkt", quiet=True)
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    @staticmethod
    def chunk_dataframe(df, chunk_size=1000):
        return [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]


class SchemaCreator:
    @staticmethod
    def create_schema(columns):
        json_schema = {"type": "object", "properties": {}}
        for key, key_type in columns.items():
            if key_type == "str":
                key_type = "string"
            elif key_type == "int":
                key_type = "integer"
            elif key_type == "float":
                key_type = "number"
            elif key_type == "dict":
                key_type = "object"
            elif key_type == "list":
                key_type = "array"
            elif key_type == "bool":
                key_type = "boolean"
            elif key_type == "None":
                key_type = "null"
            json_schema["properties"][key] = {"type": key_type}
        return json_schema

    @staticmethod
    def to_column_name(name):
        name = name.lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        name = re.sub(r"^[0-9_]+", "", name)
        name = name[:63]
        name = name.rstrip("_")
        if not name:
            name = "column"
        return name


class StoreProcessor:
    def __init__(self, db_manager, vector_store=None):
        from services.store_service.core.file_parser import FileParser

        self.parser = FileParser()
        self.chunker = Chunker()
        self.schema_creator = SchemaCreator()
        self.db_manager = db_manager

    async def process(self, file_path, collection_id, schema_path=None, **kwargs):
        from services.store_service.core.file import compute_sha1_from_content

        index = kwargs.get("index", False)
        config = kwargs.get("config", {})
        file_name = inflection.underscore(os.path.basename(file_path)).replace(" ", "_")
        processed_data = await self.parser.read_data_file(
            file_path, collection_id, **kwargs
        )
        file_sha1 = processed_data.get("file_sha1", None)
        is_success = processed_data.get("success", False)
        if not is_success:
            return processed_data
        data = processed_data.get("data", {}).get("docs", [])
        schema = processed_data.get("data", {}).get("columns", {})

        current_time = datetime.now(timezone.utc)
        for d in data:
            d["content_hash"] = compute_sha1_from_content(json_dumps(d).encode())
            d["file_name"] = file_name
            d["file_sha1"] = file_sha1
            d["created"] = current_time
            if collection_id == "collection_data_document":
                d["token"] = config.get("token", None)
                d["org_id"] = config.get("org_id", None)

        if schema_path:
            schema = self.parser.read_schema(schema_path)
        else:
            schema = self.schema_creator.create_schema(schema)

        if isinstance(data, (pd.DataFrame, list)):
            chunks = self.chunker.chunk_dataframe(data)
        elif isinstance(data, str):
            chunks = self.chunker.chunk_text(data)
        else:
            raise ValueError("Unsupported data type for chunking")

        for chunk in chunks:
            self.db_manager.save_data(chunk)

        app_logging.debug("Schema Generated", schema)

        token = kwargs.get("token", None)
        if schema and token:
            from services.store_service.views.collection import updateCollectionSchema

            updateCollectionSchema(token, schema)

        if index:
            await self.add_index_job(
                file_path,
                file_sha1,
                schema,
                token=token,
                org_id=config.get("org_id"),
                upload=True,
            )

        return {
            "message": "Data stored successfully",
            "success": True,
            "data": {
                "data": convertFromMongo(data),
                "schemas": schema,
            },
        }

    async def fetch_data(self, **kwargs):
        from services.store_service.models.collection import CollectionSchemaModel

        fields = kwargs.get("fields", {"file_name": 0, "token": 0, "org_id": 0})
        filter = kwargs.get("filter", {})
        limit = kwargs.get("limit", 0)
        skip = kwargs.get("skip", 0)
        data = self.db_manager.fetch_data(filter, fields, limit=limit, skip=skip)
        count = self.db_manager.count_data(filter)
        final_data = {"data": convertFromMongo(data), "count": count}
        token = kwargs.get("token", None)
        if token:
            schema = CollectionSchemaModel.find_one(token=token)
            final_data["schemas"] = schema.get("schemas", {}) if schema else {}
        return final_data

    async def add_index_job(
        self, file_path, file_sha1, schema, token, org_id, upload=True
    ):
        from services.store_service.models.index import IndexJobModel

        index_data = {
            "file_path": file_path,
            "file_sha1": file_sha1,
            "schema": schema,
            "token": token,
            "org_id": org_id,
            "upload": upload,
            "upload_at": int(time.time()) if upload else 0,
        }
        job = IndexJobModel.save_single_to_db(index_data)
        return job
