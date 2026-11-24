"""Mirror SDK utility endpoints."""

from fastapi import APIRouter

from app.schemas import MirrorDiagnosticsResponse, MirrorModelInfo
from app.services.mirror_sdk_service import diagnostics, list_models

router = APIRouter()


@router.get("/diagnostics", response_model=MirrorDiagnosticsResponse, summary="Run Mirror diagnostics")
def mirror_diagnostics():
    summary, details = diagnostics()
    return MirrorDiagnosticsResponse(ok=True, summary=summary, details=details)


@router.get("/models", response_model=list[MirrorModelInfo], summary="List available Mirror chat models")
def mirror_models():
    return [MirrorModelInfo(**model) for model in list_models()]
