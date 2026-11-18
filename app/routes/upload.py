"""POST /upload — accept a document and return a doc_id for later querying."""

import uuid
from fastapi import APIRouter, UploadFile, File

from app.schemas import UploadResponse
from app.services.document import extract_text

router = APIRouter()

# In-memory document store: { doc_id: text }
# For a production app you would swap this for Redis, a database, or
# a proper file-store with TTL-based eviction.
_document_store: dict[str, str] = {}


def get_document(doc_id: str) -> str | None:
    """Retrieve document text by doc_id. Returns None if not found."""
    return _document_store.get(doc_id)


@router.post("/upload", response_model=UploadResponse, summary="Upload a document")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or plain-text file.

    The server extracts the text, assigns it a unique `doc_id`, and holds it
    in memory for the lifetime of the server process. Pass the returned
    `doc_id` to **POST /query** to ask questions about this document.

    Supported file types: `.pdf`, `.txt`, `.md`, `.csv`, `.log`
    """
    text = await extract_text(file)
    doc_id = str(uuid.uuid4())
    _document_store[doc_id] = text

    return UploadResponse(
        doc_id=doc_id,
        filename=file.filename or "unknown",
        char_count=len(text),
    )
