import os
import io
import base64
import mimetypes
from services.store_service.core.parsers.file import File


def encode_file(file_obj: io.BytesIO):
    """Encode the file to base64."""
    try:
        return base64.b64encode(file_obj.read()).decode("utf-8")
    except Exception:
        return None


async def common_mistralai_process_file(file: File, enable_summarization: bool):
    from mistralai.models import OCRResponse
    from mistralai import Mistral

    def replace_image_with_empty_in_markdown(
        markdown_str: str, images_dict: dict
    ) -> str:
        for img_name in images_dict.keys():
            markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", "")
        return markdown_str

    def get_combined_markdown(ocr_response: OCRResponse) -> str:
        markdowns: list[str] = []
        for page in ocr_response.pages:
            image_data = {}
            for img in page.images:
                image_data[img.id] = img.image_base64
            markdowns.append(
                replace_image_with_empty_in_markdown(page.markdown, image_data)
            )
        return "\n\n".join(markdowns)

    if file.file_is_empty():
        return {
            "data": {"error": f"❌ {file.file.filename} is empty."},
            "success": False,
        }
    file_name = file.file.filename
    file_obj = io.BytesIO(file.file.file)
    try:
        client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

        base64_data = encode_file(file_obj)
        mime_type = mimetypes.MimeTypes().guess_type(file_name)[0]
        doc_type = "document_url"
        if "image" in mime_type:
            doc_type = "image_url"

        document = {
            "type": doc_type,
            doc_type: f"data:{mime_type};base64,{base64_data}",
        }
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document=document,
        )
        response = get_combined_markdown(ocr_response)
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
