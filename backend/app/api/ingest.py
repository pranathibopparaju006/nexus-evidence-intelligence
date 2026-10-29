import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.database import Project, User, DataSource, ProjectStatus
from app.models.schemas import DataSourceResponse
from app.services.ingestion import process_file
from app.config import settings
from app.utils.upload_validation import validate_upload

router = APIRouter()


@router.post("/{project_id}/ingest", response_model=DataSourceResponse)
async def ingest_file(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    original_filename = os.path.basename((file.filename or "").replace("\\", "/"))
    file_ext = os.path.splitext(original_filename)[1].lower()
    try:
        original_filename, file_ext = validate_upload(
            file.filename, file_size, settings.MAX_FILE_SIZE
        )
    except ValueError as exc:
        status_code = 415 if str(exc) == "Unsupported file type" else 413
        detail = "Unsupported file type" if status_code == 415 else (
            f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc

    content = await file.read()

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    storage_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(storage_path, "wb") as buffer:
        buffer.write(content)
    
    db_source = DataSource(
        project_id=project_id,
        filename=original_filename,
        file_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        file_size=file_size,
        ingestion_status="pending"
    )
    db.add(db_source)
    project.status = ProjectStatus.INGESTING
    db.commit()
    db.refresh(db_source)
    
    background_tasks.add_task(process_file, db_source.id, storage_path)
    
    return db_source


@router.get("/{project_id}/ingest", response_model=List[DataSourceResponse])
async def list_data_sources(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    sources = db.query(DataSource).filter(DataSource.project_id == project_id).all()
    return sources


@router.get("/{project_id}/ingest/{source_id}/status", response_model=DataSourceResponse)
async def get_ingest_status(
    project_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Return the current processing status of one uploaded source."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.project_id == project_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Upload not found")

    return source
