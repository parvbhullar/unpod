import json

from services.store_service.core.file import fileToUploadFile, toFile
from services.store_service.core.parsers.processors import pre_process_file
from services.store_service.schemas.collection import CollectionFile
from libs.api.logger import get_logger

app_logging = get_logger("store_service")


class FileParser:
    @staticmethod
    def read_schema(schema_path):
        with open(schema_path, "r") as f:
            return json.load(f)

    @classmethod
    async def read_data_file(
        cls,
        file_path: str,
        collection_id,
        save_log: bool = False,
        load_only: bool = False,
        **kwargs,
    ):
        if not file_path.startswith("http") and not file_path.startswith("file"):
            file_path = f"file://{file_path}"
        collectio_obj = CollectionFile(url=file_path)
        fileObj = collectio_obj.load()
        if not fileObj:
            return {
                "data": {"error": f"File not found at {file_path}"},
                "success": False,
            }
        if not load_only:
            collectio_obj.compute_file_sha1()
            exists_file = False
            if exists_file:
                return {
                    "data": {"error": f"{collectio_obj.name} already exists."},
                    "success": False,
                }
        upload_file = fileToUploadFile(
            collectio_obj.name,
            fileObj,
            size=collectio_obj.size,
            headers=collectio_obj._metadata.get("headers"),
        )
        app_logging.debug("FileParser.read_data_file", upload_file.filename)
        upload_file = toFile(upload_file)
        process_res = await pre_process_file(upload_file, False)
        is_success = process_res.get("success", False)
        if save_log and not load_only and is_success:
            collectio_obj.save_file_log(collection_id)
        process_res["file_sha1"] = collectio_obj.file_sha1
        return process_res
