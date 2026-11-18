"""POST /query — ask a question about a previously uploaded document."""

from fastapi import APIRouter, HTTPException

from app.schemas import QueryRequest, QueryResponse
from app.services.mirror_etf import query_document
from app.routes.upload import get_document

router = APIRouter()


@router.post("/query", response_model=QueryResponse, summary="Query a document")
async def query(body: QueryRequest):
    """Ask a natural-language question about an uploaded document.

    Mirror ETF processes the prompt and document context with fully homomorphic
    encryption — the model computes on ciphertext and returns a signed run
    receipt alongside the answer.

    Requires a valid `doc_id` from **POST /upload**.
    """
    doc_text = get_document(body.doc_id)
    if doc_text is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{body.doc_id}' not found. Upload it first via POST /upload.",
        )

    answer, receipt = await query_document(doc_text, body.question)

    return QueryResponse(
        answer=answer,
        doc_id=body.doc_id,
        question=body.question,
        receipt=receipt,
    )
