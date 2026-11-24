"""POST /query — ask a question about a previously uploaded document."""

from fastapi import APIRouter, HTTPException

from app.schemas import QueryRequest, QueryResponse
from app.services.mirror_sdk_service import query_document
from app.routes.upload import get_document

router = APIRouter()


@router.post("/query", response_model=QueryResponse, summary="Query a document")
async def query(body: QueryRequest):
    doc_text = get_document(body.doc_id)
    if doc_text is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{body.doc_id}' not found. Upload it first via POST /upload.",
        )

    result = query_document(doc_text, body.question, model=body.model, runtime=body.runtime)

    return QueryResponse(
        answer=result["answer"],
        doc_id=body.doc_id,
        question=body.question,
        model=result["model"],
        runtime=result["runtime"],
        protection=result["protection"],
        mirror_report=result["mirror_report"],
        service_timing=result["service_timing"],
    )
