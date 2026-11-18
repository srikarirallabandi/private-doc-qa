"""Basic smoke tests for the private-doc-qa API.

Run with:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

# Patch env before importing the app so the OpenAI client is configured
import os
os.environ.setdefault("MIRROR_ETF_API_KEY", "test-key")
os.environ.setdefault("MIRROR_ETF_BASE_URL", "http://127.0.0.1:8790/v1")

from main import app  # noqa: E402  (import after env setup)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def _upload_test_doc() -> str:
    """Helper: upload a small text document and return its doc_id."""
    content = b"This is a test document about renewable energy."
    res = client.post(
        "/api/upload",
        files={"file": ("test.txt", content, "text/plain")},
    )
    assert res.status_code == 200
    body = res.json()
    assert "doc_id" in body
    assert body["filename"] == "test.txt"
    assert body["char_count"] > 0
    return body["doc_id"]


def test_upload_txt():
    _upload_test_doc()  # just assert it succeeds


def test_upload_unsupported_type():
    res = client.post(
        "/api/upload",
        files={"file": ("image.png", b"\x89PNG", "image/png")},
    )
    assert res.status_code == 415


def test_upload_empty_file():
    res = client.post(
        "/api/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Query — doc not found
# ---------------------------------------------------------------------------

def test_query_missing_doc():
    res = client.post(
        "/api/query",
        json={"doc_id": "nonexistent-id", "question": "What is this about?"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Query — integration (skipped if Mirror ETF is not running)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.getenv("MIRROR_ETF_INTEGRATION") != "1",
    reason="Set MIRROR_ETF_INTEGRATION=1 to run live Mirror ETF tests",
)
def test_query_live():
    """Full round-trip: upload → query → check receipt fields."""
    doc_id = _upload_test_doc()
    res = client.post(
        "/api/query",
        json={"doc_id": doc_id, "question": "What is the document about?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["answer"]
    assert body["doc_id"] == doc_id
    assert "receipt" in body
