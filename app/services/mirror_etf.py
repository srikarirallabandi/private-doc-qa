"""Mirror ETF inference service.

Mirror ETF is OpenAI-compatible — the only difference is the base_url.
Every response also carries a signed run receipt that proves what the model
processed, when, and under which encryption lane.

Docs:   https://mirrorsecurity.io/etf
Local:  http://127.0.0.1:8790/v1   (Mirror ETF node on your machine)
SaaS:   configure MIRROR_ETF_BASE_URL in .env
"""

import os
from openai import AsyncOpenAI, APIConnectionError, APIStatusError
from fastapi import HTTPException

from app.schemas import RunReceipt


# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

def _get_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client pointed at Mirror ETF."""
    api_key = os.getenv("MIRROR_ETF_API_KEY", "mirror-etf-local")
    base_url = os.getenv("MIRROR_ETF_BASE_URL", "http://127.0.0.1:8790/v1")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


# ---------------------------------------------------------------------------
# Receipt extraction
# ---------------------------------------------------------------------------

def _extract_receipt(raw_response) -> RunReceipt:
    """Pull Mirror ETF's signed run receipt out of the API response.

    Mirror ETF extends the OpenAI response object with extra fields such as
    `receipt_id`, `signed_at`, and `encryption_lane`. We collect whatever is
    present into a RunReceipt, with the full raw dict for transparency.
    """
    # The OpenAI SDK exposes extra (non-standard) fields via model_extra or
    # the raw response dict depending on SDK version.
    extra: dict = {}

    # Try model_extra (pydantic v2 style used by openai>=1.x)
    if hasattr(raw_response, "model_extra") and raw_response.model_extra:
        extra.update(raw_response.model_extra)

    # Also check the first choice for per-choice receipt fields
    if raw_response.choices:
        choice = raw_response.choices[0]
        if hasattr(choice, "model_extra") and choice.model_extra:
            extra.update(choice.model_extra)

    return RunReceipt(
        receipt_id=extra.get("receipt_id") or extra.get("x_receipt_id"),
        signed_at=extra.get("signed_at") or extra.get("x_signed_at"),
        model=raw_response.model,
        encryption_lane=extra.get("encryption_lane") or extra.get("lane"),
        raw=extra,
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a precise document assistant. The user has uploaded a document and
will ask questions about it. Answer only from the document content provided.
If the answer is not in the document, say "I could not find that in the
document." Do not speculate or use outside knowledge.
"""


async def query_document(doc_text: str, question: str) -> tuple[str, RunReceipt]:
    """Send a document Q&A request to Mirror ETF and return (answer, receipt).

    Args:
        doc_text:  The full text of the document (already extracted).
        question:  The user's natural-language question.

    Returns:
        A (answer_text, RunReceipt) tuple.

    Raises:
        HTTPException 502  on Mirror ETF connectivity issues.
        HTTPException 503  on Mirror ETF API errors.
    """
    # Truncate document text to stay within context limits
    max_chars = int(os.getenv("MAX_DOC_TOKENS", "8000")) * 4  # ~4 chars per token
    truncated = doc_text[:max_chars]
    if len(doc_text) > max_chars:
        truncated += "\n\n[... document truncated to fit context window ...]"

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

    model = os.getenv("MIRROR_ETF_MODEL", "gpt-4o")
    client = _get_client()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to Mirror ETF. "
                "Make sure the Mirror ETF node is running and MIRROR_ETF_BASE_URL is correct. "
                f"Detail: {exc}"
            ),
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Mirror ETF returned an error: {exc.status_code} — {exc.message}",
        ) from exc

    answer = response.choices[0].message.content or ""
    receipt = _extract_receipt(response)

    return answer, receipt
