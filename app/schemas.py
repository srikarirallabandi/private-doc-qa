"""Pydantic models for request and response bodies."""

from pydantic import BaseModel, Field
from typing import Any


class UploadResponse(BaseModel):
    """Returned after a successful document upload."""
    doc_id: str = Field(..., description="Unique ID for the uploaded document. Pass this to /query.")
    filename: str = Field(..., description="Original filename.")
    char_count: int = Field(..., description="Number of characters extracted from the document.")
    message: str = Field(default="Document uploaded and ready to query.")


class QueryRequest(BaseModel):
    """Body for POST /query."""
    doc_id: str = Field(..., description="The doc_id returned by /upload.")
    question: str = Field(..., min_length=1, description="The question to ask about the document.")


class RunReceipt(BaseModel):
    """Signed run receipt returned by Mirror ETF on each inference call.

    Mirror ETF attaches a signed attestation to every inference call so you have
    a tamper-evident record of what the model processed. Fields here reflect the
    extra fields Mirror ETF adds on top of the standard OpenAI response.
    """
    receipt_id: str | None = Field(None, description="Mirror ETF receipt identifier.")
    signed_at: str | None = Field(None, description="ISO 8601 timestamp when the receipt was signed.")
    model: str | None = Field(None, description="Model that produced the response.")
    encryption_lane: str | None = Field(None, description="Encryption lane used (plain / e2e / fhe / local).")
    raw: dict[str, Any] = Field(default_factory=dict, description="Full raw receipt fields from Mirror ETF.")


class QueryResponse(BaseModel):
    """Response from POST /query."""
    answer: str = Field(..., description="The model's answer to the question.")
    doc_id: str = Field(..., description="The document that was queried.")
    question: str = Field(..., description="The original question.")
    receipt: RunReceipt = Field(..., description="Mirror ETF signed run receipt.")
