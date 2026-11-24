# Mirror SDK Document Q&A

A small FastAPI app that lets you upload a document and ask questions about it using the **Mirror SDK**.

This version is adapted from a simple private document Q&A app and replaces the Mirror ETF OpenAI-compatible adapter with the native `mirror_sdk` client.

## Features

- Upload PDF and text documents
- Ask questions grounded only in the uploaded document
- Query via Mirror SDK chat completions
- Choose `plain`, `protected`, or `sealed` runtime lanes
- Run Mirror diagnostics from the UI or API
- List available Mirror chat models when your tenant exposes routing

## Project structure

```
mirror-doc-qa-sdk/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── frontend/
│   └── index.html
├── app/
│   ├── schemas.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── query.py
│   │   └── mirror.py
│   └── services/
│       ├── document.py
│       └── mirror_sdk_service.py
└── tests/
```

## Setup

### 1. Create a virtualenv and install app dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Mirror SDK from your local bundle

If your extracted SDK bundle is in `/path/to/mirror-sdk`:

```bash
pip install --find-links=/path/to/mirror-sdk mirror-sdk
```

Example using the bundle you shared after unzipping:

```bash
pip install --find-links=../mirror-sdk mirror-sdk
```

### 3. Download and extract your Mirror service credential

From the Mirror platform UI:

- **Credentials → Service Credentials → Add New → Download credentials**

Then extract the downloaded bundle into a local secrets folder inside your project:

```bash
unzip ~/Downloads/<credential>-service-credential-bundle.zip -d .secrets
export MIRROR_SERVICE_CREDENTIAL_FILE="$PWD/.secrets/mirror-service-credential/service-credential.json"
```

You can keep the `export` for the current shell session, or copy the resolved absolute path into `.env`.

### 4. Configure environment

```bash
cp .env.example .env
```

Set at minimum:

```env
MIRROR_SERVICE_CREDENTIAL_FILE=/absolute/path/to/service-credential.json
MIRROR_BASE_URL=https://platform.mirrorsecurity.io
MIRROR_DEFAULT_MODEL=claude-sonnet-4-6
MAX_DOC_TOKENS=8000
```

Notes:

- The native `mirror_sdk` client needs `MIRROR_BASE_URL` in addition to the service credential file.
- For the hosted Mirror SDK flow, prefer the platform host root such as `https://platform.mirrorsecurity.io`, not the local ETF proxy URL.
- If your environment uses legacy API-key auth instead of the service credential file, configure `MIRROR_BASE_URL` and `MIRROR_API_KEY` instead.

## Run the app

```bash
python main.py
```

Then open [http://localhost:8000](http://localhost:8000).

API docs are at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

## API endpoints

### `POST /api/upload`
Upload a PDF or text document.

### `POST /api/query`
Body:

```json
{
  "doc_id": "...",
  "question": "What are the main conclusions?",
  "model": "claude-sonnet-4-6",
  "runtime": "protected"
}
```

### `GET /api/mirror/diagnostics`
Run `client.diagnostics.run()` and return the report.

### `GET /api/mirror/models`
Return models from `client.routing.models.list()` when available.

## Notes

- This app currently uses simple **full-document prompting** with truncation.
- For larger documents or production use, the next upgrade should be **chunking + retrieval**.
- The app normalizes Mirror metadata into:
  - `protection`
  - `mirror_report`
  - `service_timing`

## Suggested next improvements

1. Add streaming answers
2. Add document chunking and retrieval
3. Persist uploaded docs in a database or object store
4. Add multi-document collections
5. Add conversation history
