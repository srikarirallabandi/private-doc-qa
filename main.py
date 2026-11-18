"""FastAPI application entry point."""

from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else imports os.getenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.upload import router as upload_router
from app.routes.query import router as query_router

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Private Document Q&A",
    description=(
        "Upload a document and ask questions about it — "
        "inference routed through Mirror ETF so your data stays encrypted end-to-end."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Allow the frontend (served from the same origin or localhost dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

app.include_router(upload_router, prefix="/api", tags=["Documents"])
app.include_router(query_router, prefix="/api", tags=["Q&A"])


@app.get("/api/health", tags=["Health"])
async def health():
    """Liveness check."""
    return {"ok": True, "service": "private-doc-qa"}


# ---------------------------------------------------------------------------
# Serve the single-page frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app", "frontend"])
