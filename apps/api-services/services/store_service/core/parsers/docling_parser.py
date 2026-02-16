import os
import io
from services.store_service.core.parsers.file import File


async def common_docling_process_file(file: File, enable_summarization: bool):
    if file.file_is_empty():
        return {
            "data": {"error": f"❌ {file.file.filename} is empty."},
            "success": False,
        }
    file_name = file.file.filename
    file_obj = io.BytesIO(file.file.file)
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import DocumentStream

        md = DocumentConverter()
        doc = DocumentStream(name=file_name, stream=file_obj)
        res = md.convert(doc)
        response = res.document.export_to_markdown()
    except Exception:
        return {
            "data": {"error": f"❌ {file.file.filename} is not supported."},
            "success": False,
        }

    columns = {
        "name": "string",
        "source": "string",
        "file_path": "string",
        "content": "string",
    }
    docs = [
        {
            "name": os.path.basename(file_name),
            "source": "file",
            "file_path": file_name,
            "content": response,
        }
    ]
    return {
        "docs": docs,
        "columns": columns,
        "metadata": {},
    }
