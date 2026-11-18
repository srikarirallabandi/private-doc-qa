"""Document text extraction service.

Supports:
  - PDF  (.pdf)  — extracted with pypdf
  - Plain text   (.txt, .md, .csv, .log, and any other text/* content type)
"""

import io
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".log", ".text"}


def _extract_pdf(data: bytes) -> str:
    """Extract text from a PDF byte stream using pypdf."""
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_text(data: bytes) -> str:
    """Decode raw bytes as UTF-8 text, falling back to latin-1."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


async def extract_text(file: UploadFile) -> str:
    """Read an uploaded file and return its full text content.

    Raises:
        HTTPException 415  if the file type is not supported.
        HTTPException 422  if the file appears to be empty after extraction.
    """
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Allow anything whose content-type starts with text/
    content_type = (file.content_type or "").lower()
    is_text_mime = content_type.startswith("text/")

    if ext not in SUPPORTED_EXTENSIONS and not is_text_mime:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{ext or content_type}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))} "
                "or any text/* MIME type."
            ),
        )

    raw = await file.read()

    if not raw:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    if ext == ".pdf" or content_type == "application/pdf":
        text = _extract_pdf(raw)
    else:
        text = _extract_text(raw)

    text = text.strip()
    if not text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the uploaded file.",
        )

    return text
