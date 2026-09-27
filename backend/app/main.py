import sys
from pathlib import Path

# Ensure paths are configured before importing internal packages
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
_root_dir = _backend_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

import app.config  # Initializes pathing and environment
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from app.api.documents import router as documents_router
    from app.api.research import router as research_router
except ModuleNotFoundError:
    from backend.app.api.documents import router as documents_router
    from backend.app.api.research import router as research_router

app = FastAPI(
    title="ResearchPilot",
    description="Agentic AI-powered document research platform",
    version="0.1.0"
)

# Robust CORS configuration allowing all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(documents_router)
app.include_router(research_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ResearchPilot API"
    }


# Frontend static files mounting
_frontend_dir = _root_dir / "frontend"
if _frontend_dir.exists():
    css_dir = _frontend_dir / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    js_dir = _frontend_dir / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    assets_dir = _frontend_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def serve_index():
        index_file = _frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "ResearchPilot API is running"}
else:
    @app.get("/")
    def root():
        return {
            "message": "ResearchPilot API is running"
        }