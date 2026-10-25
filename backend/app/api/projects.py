from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.database import Project, User, ProjectStatus, NarrativeFinding, DataSource, AnalysisJob
from app.models.schemas import ProjectCreate, ProjectResponse

router = APIRouter()


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_project = Project(
        name=project.name,
        description=project.description,
        user_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
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
    
    return project


@router.delete("/{project_id}")
async def delete_project(
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
    
    # Delete dependent SQL rows explicitly. Existing databases may not have
    # ON DELETE CASCADE constraints, so deleting Project first raises an FK error.
    try:
        db.query(NarrativeFinding).filter(
            NarrativeFinding.project_id == project_id
        ).delete(synchronize_session=False)
        db.query(AnalysisJob).filter(
            AnalysisJob.project_id == project_id
        ).delete(synchronize_session=False)
        db.query(DataSource).filter(
            DataSource.project_id == project_id
        ).delete(synchronize_session=False)
        db.delete(project)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Project could not be deleted; database changes were rolled back")

    # Best-effort removal of graph nodes scoped to this project only.
    try:
        from neo4j import GraphDatabase
        from app.config import settings
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        try:
            with driver.session() as session:
                session.run(
                    "MATCH (n {project_id: $project_id}) DETACH DELETE n",
                    {"project_id": project_id}
                )
        finally:
            driver.close()
    except Exception as exc:
        print(f"Warning: graph cleanup for deleted project {project_id} failed: {exc}")

    return {"message": "Project deleted successfully"}
