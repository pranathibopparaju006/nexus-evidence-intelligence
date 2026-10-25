from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
import os
import time

from app.api import auth, projects, ingest, analyze, graph, narratives
from app.core.database import engine, Base
from app.config import settings


def initialize_database():
    """Create tables with a short retry window for Docker startup ordering."""
    last_error = None
    for attempt in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


# Docker Compose starts dependencies before the backend, but databases can
# still need a few seconds to accept connections. Retry instead of exiting.
initialize_database()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="NEXUS API",
    description="Narrative Evolution & Evidence Intelligence System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(ingest.router, prefix="/api/v1/projects", tags=["Ingestion"])
app.include_router(analyze.router, prefix="/api/v1/projects", tags=["Analysis"])
app.include_router(graph.router, prefix="/api/v1/projects", tags=["Graph"])
app.include_router(narratives.router, prefix="/api/v1/projects", tags=["Narratives"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "NEXUS API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to NEXUS API",
        "description": "Narrative Evolution & Evidence Intelligence System",
        "docs": "/docs",
        "version": "1.0.0"
    }
