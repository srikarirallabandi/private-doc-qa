"""Pydantic models for request and response bodies."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    doc_id: str = Field(..., description="Unique ID for the uploaded document. Pass this to /query.")
    filename: str = Field(..., description="Original filename.")
    char_count: int = Field(..., description="Number of characters extracted from the document.")
    message: str = Field(default="Document uploaded and ready to query.")


class QueryRequest(BaseModel):
    doc_id: str = Field(..., description="The doc_id returned by /upload.")
    question: str = Field(..., min_length=1, description="The question to ask about the document.")
    model: str | None = Field(default=None, description="Optional Mirror model override.")
    runtime: Literal["plain", "protected", "sealed"] = Field(
        default="plain",
        description="Mirror runtime lane to use for the question.",
    )


class MirrorDiagnosticsResponse(BaseModel):
    ok: bool
    summary: str
    details: dict[str, Any]


class MirrorModelInfo(BaseModel):
    id: str
    provider: str | None = None
    surface: str | None = None


class ProtectionInfo(BaseModel):
    profile: str | None = None
    contract: str | None = None
    contract_satisfied: bool | None = None
    compute_mode: str | None = None
    all_stages_encrypted: bool | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class MirrorReportInfo(BaseModel):
    session_id: str | None = None
    family: str | None = None
    execution_kind: str | None = None
    runtime_mode: str | None = None
    decode_mode: str | None = None
    receipt_mode: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The model's answer to the question.")
    doc_id: str = Field(..., description="The document that was queried.")
    question: str = Field(..., description="The original question.")
    model: str = Field(..., description="The model used for the answer.")
    runtime: str = Field(..., description="The Mirror runtime lane used.")
    protection: ProtectionInfo | None = Field(default=None, description="Protected-lane metadata if available.")
    mirror_report: MirrorReportInfo | None = Field(default=None, description="Mirror attestation/report fields if available.")
    service_timing: dict[str, Any] = Field(default_factory=dict, description="Timing metadata returned by Mirror.")
