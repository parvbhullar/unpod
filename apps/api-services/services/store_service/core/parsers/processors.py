from services.store_service.core.parsers.file import File
from services.store_service.core.parsers.csv_loader import CSVLoader
from services.store_service.core.parsers.tsv_loader import TSVLoader
from services.store_service.core.parsers.docling_parser import (
    common_docling_process_file,
)
from services.store_service.core.parsers.mistral_parser import (
    common_mistralai_process_file,
)

from libs.api.logger import get_logger

app_logging = get_logger("store_service")


async def process_csv(file: File, enable_summarization):
    file.compute_documents(CSVLoader)
    return file.documents


async def process_tsv(file: File, enable_summarization):
    file.compute_documents(TSVLoader)
    return file.documents


file_processors = {
    ".csv": process_csv,
    ".tsv": process_tsv,
    ".pdf": common_mistralai_process_file,
    "common": common_docling_process_file,
}


async def pre_process_file(file: File, enable_summarization: bool):
    if file.file_is_empty():
        return {
            "data": {"error": f"❌ {file.file.filename} is empty."},
            "success": False,
        }
    if file.file_extension in file_processors:
        try:
            response = await file_processors[file.file_extension](
                file=file, enable_summarization=enable_summarization
            )
            return {"data": response, "success": True}
        except Exception as e:
            app_logging.error(f"Error processing file: {e}")
            raise e
    else:
        common_processor = file_processors.get("common")
        response = await common_processor(file, enable_summarization)
        return {"data": response, "success": True}
