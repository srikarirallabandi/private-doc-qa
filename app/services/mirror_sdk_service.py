"""Mirror SDK inference service."""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException

from app.schemas import MirrorReportInfo, ProtectionInfo


SYSTEM_PROMPT = """\
You are a precise document assistant. The user has uploaded a document and
will ask questions about it. Answer only from the document content provided.
If the answer is not in the document, say \"I could not find that in the
document.\" Do not speculate or use outside knowledge.
"""


DEFAULT_MODEL = os.getenv("MIRROR_DEFAULT_MODEL", "claude-sonnet-4-6")
MAX_DOC_TOKENS = int(os.getenv("MAX_DOC_TOKENS", "8000"))


def _get_mirror_client():
    try:
        from mirror_sdk import Mirror
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "mirror_sdk is not installed. Install it from your Mirror SDK bundle, "
                "for example: pip install --find-links=/path/to/mirror-sdk mirror-sdk"
            ),
        ) from exc

    try:
        return Mirror()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Mirror client. Check credential env vars and SDK setup. Detail: {exc}",
        ) from exc


def _extract_object_fields(obj: Any, fields: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if obj is None:
        return result
    for field in fields:
        if hasattr(obj, field):
            result[field] = getattr(obj, field)
    if hasattr(obj, "to_dict"):
        try:
            result.update(obj.to_dict())
        except Exception:
            pass
    return result


def _normalize_protection(response: Any) -> ProtectionInfo | None:
    protection = getattr(response, "protection", None)
    if protection is None:
        return None
    raw = _extract_object_fields(
        protection,
        ["profile", "contract", "contract_satisfied", "compute_mode", "all_stages_encrypted"],
    )
    return ProtectionInfo(
        profile=raw.get("profile"),
        contract=raw.get("contract"),
        contract_satisfied=raw.get("contract_satisfied"),
        compute_mode=raw.get("compute_mode"),
        all_stages_encrypted=raw.get("all_stages_encrypted"),
        raw=raw,
    )


def _normalize_report(response: Any) -> MirrorReportInfo | None:
    report = getattr(response, "mirror_report", None)
    if report is None:
        return None
    raw = _extract_object_fields(
        report,
        ["session_id", "family", "execution_kind", "runtime_mode", "decode_mode", "receipt_mode"],
    )
    return MirrorReportInfo(
        session_id=raw.get("session_id"),
        family=raw.get("family"),
        execution_kind=raw.get("execution_kind"),
        runtime_mode=raw.get("runtime_mode"),
        decode_mode=raw.get("decode_mode"),
        receipt_mode=raw.get("receipt_mode"),
        raw=raw,
    )


def _extract_answer_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    choices = getattr(response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "") if message else ""
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            content = "\n".join(parts)
        if isinstance(content, str):
            return content.strip()

    return ""


def _truncate_document(doc_text: str) -> str:
    max_chars = MAX_DOC_TOKENS * 4
    truncated = doc_text[:max_chars]
    if len(doc_text) > max_chars:
        truncated += "\n\n[... document truncated to fit context window ...]"
    return truncated


def list_models() -> list[dict[str, Any]]:
    client = _get_mirror_client()
    try:
        models = client.routing.models.list()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not list Mirror models: {exc}") from exc

    normalized: list[dict[str, Any]] = []
    for model in models or []:
        normalized.append(
            {
                "id": getattr(model, "id", None) or (model.get("id") if isinstance(model, dict) else None),
                "provider": getattr(model, "provider", None) or (model.get("provider") if isinstance(model, dict) else None),
                "surface": getattr(model, "surface", None) or (model.get("surface") if isinstance(model, dict) else None),
            }
        )
    return [item for item in normalized if item.get("id")]


def diagnostics() -> tuple[str, dict[str, Any]]:
    client = _get_mirror_client()
    try:
        report = client.diagnostics.run()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Mirror diagnostics failed: {exc}") from exc

    summary = str(report)
    if hasattr(report, "to_dict"):
        try:
            details = report.to_dict()
        except Exception:
            details = {"summary": summary}
    else:
        details = {"summary": summary}

    return summary, details


def query_document(doc_text: str, question: str, model: str | None = None, runtime: str = "plain"):
    truncated = _truncate_document(doc_text)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Here is the document:\n\n"
                f"---\n{truncated}\n---\n\n"
                f"Question: {question}"
            ),
        },
    ]

    selected_model = model or DEFAULT_MODEL
    client = _get_mirror_client()

    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            max_tokens=400,
            temperature=0,
            runtime=runtime,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Mirror chat request failed: {exc}") from exc

    answer = _extract_answer_text(response)
    if not answer:
        raise HTTPException(status_code=502, detail="Mirror returned an empty answer.")

    service_timing = getattr(response, "service_timing", None) or {}
    return {
        "answer": answer,
        "model": getattr(response, "model", None) or selected_model,
        "runtime": runtime,
        "protection": _normalize_protection(response),
        "mirror_report": _normalize_report(response),
        "service_timing": service_timing if isinstance(service_timing, dict) else {},
    }
