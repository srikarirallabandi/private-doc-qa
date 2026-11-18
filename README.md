# 🔒 Private Document Q&A

> Upload a PDF or plain-text file and ask questions about it.  
> Every inference call is routed through **[Mirror ETF (Encrypted Token Factory)](https://mirrorsecurity.io/etf)** so your document content stays encrypted during inference — the model computes on ciphertext and returns a signed run receipt with every answer.

---

## What this demonstrates

| Concept | Where it shows up |
|---|---|
| Mirror ETF as an OpenAI-compatible drop-in | `app/services/mirror_etf.py` — only `base_url` changes |
| Signed run receipts | Every `/api/query` response includes a `receipt` field |
| PDF + plain-text extraction | `app/services/document.py` using `pypdf` |
| FastAPI file upload → in-memory store → Q&A flow | `app/routes/upload.py` + `app/routes/query.py` |
| Single-page UI (no framework) | `frontend/index.html` |

---

## Project structure

```
private-doc-qa/
├── main.py                    # FastAPI app — entry point
├── requirements.txt
├── .env.example               # Copy to .env and fill in your key
├── .gitignore
│
├── app/
│   ├── schemas.py             # Pydantic request/response models
│   ├── routes/
│   │   ├── upload.py          # POST /api/upload
│   │   └── query.py           # POST /api/query
│   └── services/
│       ├── document.py        # PDF + plain-text extraction
│       └── mirror_etf.py      # Mirror ETF OpenAI-compatible client
│
├── frontend/
│   └── index.html             # Single-page UI
│
└── tests/
    └── test_app.py            # Smoke tests (pytest)
```

---

## Quickstart

### 1. Clone and install dependencies

```bash
git clone https://github.com/<your-username>/private-doc-qa.git
cd private-doc-qa

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Mirror ETF

```bash
cp .env.example .env
```

Open `.env` and set:

```env
# Your Mirror ETF API key from https://platform.mirrorsecurity.io
MIRROR_ETF_API_KEY=your-key-here

# Local mode — Mirror ETF node running on your machine:
MIRROR_ETF_BASE_URL=http://127.0.0.1:8790/v1

# SaaS mode — Mirror's hosted platform:
# MIRROR_ETF_BASE_URL=https://platform.mirrorsecurity.io/v1

# Model available on your Mirror ETF node
MIRROR_ETF_MODEL=gpt-4o
```

> **Local mode:** Download and run the Mirror ETF node from [mirrorsecurity.io/etf](https://mirrorsecurity.io/etf). The node starts on `http://127.0.0.1:8790` by default and routes inference through encrypted channels.

### 3. Run the server

```bash
python main.py
```

Then open **[http://localhost:8000](http://localhost:8000)** in your browser.

The interactive API docs are at **[http://localhost:8000/api/docs](http://localhost:8000/api/docs)**.

---

## API reference

### `POST /api/upload`

Upload a document. Supported types: `.pdf`, `.txt`, `.md`, `.csv`, `.log`.

**Request:** `multipart/form-data` with a `file` field.

**Response:**
```json
{
  "doc_id": "3f2a1b...",
  "filename": "contract.pdf",
  "char_count": 14823,
  "message": "Document uploaded and ready to query."
}
```

---

### `POST /api/query`

Ask a question about an uploaded document.

**Request body:**
```json
{
  "doc_id": "3f2a1b...",
  "question": "What are the termination clauses?"
}
```

**Response:**
```json
{
  "answer": "Section 12 states that either party may terminate...",
  "doc_id": "3f2a1b...",
  "question": "What are the termination clauses?",
  "receipt": {
    "receipt_id": "rcpt_...",
    "signed_at": "2026-11-18T10:23:45Z",
    "model": "gpt-4o",
    "encryption_lane": "fhe",
    "raw": { ... }
  }
}
```

The `receipt` object is Mirror ETF's **signed run receipt** — a tamper-evident record that proves what the model processed, when, and under which encryption lane.

---

## Running the tests

```bash
pytest tests/ -v
```

To run the live integration test (requires Mirror ETF to be running):

```bash
MIRROR_ETF_INTEGRATION=1 pytest tests/ -v
```

---

## How Mirror ETF integration works

The entire integration lives in `app/services/mirror_etf.py`. The key difference from a plain OpenAI call is **one line**:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="your-mirror-etf-key",
    base_url="http://127.0.0.1:8790/v1",   # ← this is all that changes
)
```

From that point on, every `client.chat.completions.create(...)` call travels encrypted through Mirror ETF. The model never sees your plaintext document — it reasons on ciphertext — and each response includes a signed receipt.

---

## Resources

- [Mirror ETF product page](https://mirrorsecurity.io/etf)
- [Mirror Security platform](https://mirrorsecurity.io/platform)
- [Mirror ETF documentation](https://docs.mirrorsecurity.io)
- [Mirror Security playground](https://mirrorsecurity.io/playground) — try FHE demos in the browser

---

## License

MIT
