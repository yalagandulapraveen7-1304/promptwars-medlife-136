import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_all_tables
from app.routers import dashboard, clinical_record, patient_intake, copilot
from app.copilot.knowledge_base import get_knowledge_base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed clinical data
    init_all_tables()
    # Initialize Copilot Knowledge Base from synthetic dataset
    get_knowledge_base()
    yield

app = FastAPI(
    title="MedLens Clinical Intelligence Platform API",
    description="Backend service powering the MedLens Clinical Triage & Provider Dashboard (Module 7), Structured Clinical Records (Module 6, 12, 13, 14, 23), Patient Intake & Nomination (Module 3), and AI Copilot Intelligence Service.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development and file:/// origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(dashboard.router)
app.include_router(clinical_record.router)
app.include_router(patient_intake.router)
app.include_router(copilot.router)

# Mount frontend directories for unified hosting if desired
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _resolve_dir(name: str):
    for base in [PROJECT_ROOT, os.getcwd(), os.path.abspath(".")]:
        p = os.path.join(base, name)
        if os.path.isdir(p):
            return p
    return None

def _resolve_file(name: str):
    for base in [PROJECT_ROOT, os.getcwd(), os.path.abspath(".")]:
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return None

SCREENS_DIR = _resolve_dir("screens")
SCREENSHOTS_DIR = _resolve_dir("screenshots")
DOCS_DIR = _resolve_dir("docs")
INDEX_HTML = _resolve_file("index.html")

if SCREENS_DIR:
    app.mount("/screens", StaticFiles(directory=SCREENS_DIR), name="screens")
if SCREENSHOTS_DIR:
    app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")
if DOCS_DIR:
    app.mount("/docs-files", StaticFiles(directory=DOCS_DIR), name="docs-files")

@app.middleware("http")
async def vercel_rewrite_middleware(request: Request, call_next):
    # 1. Check if Vercel passed the path in query params (?path=$1)
    q_path = request.query_params.get("path") or request.query_params.get("__path")
    if q_path:
        clean = "/" + q_path.lstrip("/")
        if not clean.startswith("/api") and not clean.startswith("/screens"):
            clean = "/api" + clean
        request.scope["path"] = clean
    else:
        path = request.scope.get("path", "")
        # 2. If Vercel stripped /api prefix (e.g. /health, /dashboard/overview)
        if not path.startswith("/api") and not path.startswith("/screens") and not path.startswith("/screenshots"):
            if path == "/health":
                request.scope["path"] = "/api/health"
            elif any(path.startswith(p) for p in ["/dashboard", "/records", "/intake", "/copilot"]):
                request.scope["path"] = "/api" + path

        # 3. If Vercel internal rewrite passed /api/index.py
        if path.startswith("/api/index.py") or path.startswith("/api/index"):
            matched = request.headers.get("x-matched-path")
            if matched:
                request.scope["path"] = matched
            else:
                sub = path.replace("/api/index.py", "").replace("/api/index", "")
                request.scope["path"] = sub if sub else "/"

    return await call_next(request)

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY", "service": "MedLens Dashboard Backend", "version": "1.0.0"}


@app.get("/")
@app.get("/index.html")
@app.get("/app")
@app.get("/api/index.py")
@app.get("/api/index")
def serve_app():
    target = _resolve_file("index.html")
    if target and os.path.exists(target):
        return FileResponse(target)
    return {"status": "HEALTHY", "service": "MedLens Clinical Intelligence Platform", "version": "1.0.0"}


