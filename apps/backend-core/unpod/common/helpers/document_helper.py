from django.http import HttpResponse


def generate_pdf_from_html(html_content: str):
    """
    Generates a PDF file from the given HTML content.

    Args:
        html_content (str): The HTML content to convert to PDF.
    Returns:
        BytesIO: A BytesIO object containing the generated PDF file.
    """
    from weasyprint import HTML
    from io import BytesIO

    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer


def download_pdf_from_html(html_content: str, filename: str) -> HttpResponse:
    """
    Download a PDF file from the given HTML content.

    Args:
        html_content (str): The HTML content to convert to PDF.
        filename (str): The desired filename for the generated PDF.
    Returns:
        HttpResponse: A Django HttpResponse containing the PDF file.
    """
    pdf_buffer = generate_pdf_from_html(html_content)

    filename = filename.replace(".pdf", "").replace(".PDF", "")
    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}.pdf"'

    return response
