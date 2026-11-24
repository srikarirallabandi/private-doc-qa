"""FastAPI application entry point for Mirror SDK Document Q&A."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.upload import router as upload_router
from app.routes.query import router as query_router
from app.routes.mirror import router as mirror_router

app = FastAPI(
    title="Mirror SDK Document Q&A",
    description=(
        "Upload a document and ask questions about it using the Mirror SDK. "
        "Supports plain and protected runtime lanes."
    ),
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["Documents"])
app.include_router(query_router, prefix="/api", tags=["Q&A"])
app.include_router(mirror_router, prefix="/api/mirror", tags=["Mirror"])


@app.get("/api/health", tags=["Health"])
async def health():
    return {"ok": True, "service": "mirror-doc-qa-sdk"}


app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app", "frontend"])
