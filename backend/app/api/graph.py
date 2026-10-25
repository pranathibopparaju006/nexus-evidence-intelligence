from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.database import Project, User
from app.models.schemas import GraphData, TimelineEvent
from app.services.graph_service import get_project_graph, get_timeline_events

router = APIRouter()


@router.get("/{project_id}/graph", response_model=GraphData)
async def get_graph(
    project_id: int,
    node_type: str = None,
    time_start: str = None,
    time_end: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    graph_data = await get_project_graph(project_id, node_type, time_start, time_end)
    return graph_data


@router.get("/{project_id}/timeline", response_model=List[TimelineEvent])
async def get_timeline(
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
    
    events = await get_timeline_events(project_id)
    return events
