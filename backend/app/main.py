import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_all_tables
from app.routers import dashboard, clinical_record, patient_intake

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed clinical data
    init_all_tables()
    yield

app = FastAPI(
    title="MedLens Clinical Intelligence Platform API",
    description="Backend service powering the MedLens Clinical Triage & Provider Dashboard (Module 7), Structured Clinical Records (Module 6, 12, 13, 14, 23), and Patient Intake & Nomination (Module 3).",
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

# Mount frontend directories for unified hosting if desired
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCREENS_DIR = os.path.join(PROJECT_ROOT, "screens")
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
INDEX_HTML = os.path.join(PROJECT_ROOT, "index.html")

if os.path.exists(SCREENS_DIR):
    app.mount("/screens", StaticFiles(directory=SCREENS_DIR), name="screens")
if os.path.exists(SCREENSHOTS_DIR):
    app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")
if os.path.exists(DOCS_DIR):
    app.mount("/docs-files", StaticFiles(directory=DOCS_DIR), name="docs-files")

@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY", "service": "MedLens Dashboard Backend", "version": "1.0.0"}

@app.get("/app")
def serve_app():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return {"message": "index.html not found"}
