from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.database import Project, User, AnalysisJob, ProjectStatus
from app.models.schemas import AnalysisRequest, AnalysisStatusResponse, FindingResponse
from app.agents.orchestrator import run_analysis
from app.api.narratives import _ensure_narrative_dna

router = APIRouter()


@router.post("/{project_id}/analyze", response_model=AnalysisStatusResponse)
async def start_analysis(
    project_id: int,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    job = AnalysisJob(
    project_id=project_id,
    job_type=request.analysis_type,
    status="queued"
)
    db.add(job)
    project.status = ProjectStatus.ANALYZING
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(run_analysis, job.id, project_id)
    
    return AnalysisStatusResponse(
        job_id=job.id,
        status="queued",
        message="Analysis job queued successfully"
    )


@router.get("/{project_id}/analyze/{job_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    project_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.project_id == project_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    return AnalysisStatusResponse(
        job_id=job.id,
        status=job.status,
        current_stage=job.results.get("current_stage") if job.results else None,
        message=job.error_message if job.status == "error" else None
    )


@router.get("/{project_id}/findings", response_model=List[FindingResponse])
async def get_findings(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from app.models.database import NarrativeFinding
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    findings = db.query(NarrativeFinding).filter(
        NarrativeFinding.project_id == project_id
    ).all()

    enriched = _ensure_narrative_dna(db, project_id, findings)

    # Keep the API human-facing: collapse repeated signals produced by
    # overlapping entity/content combinations. Raw evidence remains available
    # inside each finding's evidence object.
    seen = set()
    unique = []
    for finding in enriched:
        evidence = finding.evidence or {}
        pair = evidence.get("entity_pair") or []
        if isinstance(pair, (list, tuple)):
            pair = tuple(sorted(str(x).strip().lower() for x in pair))
        key = (
            finding.finding_type,
            evidence.get("title") or evidence.get("signal_type"),
            pair,
            evidence.get("content_a"),
            evidence.get("content_b"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)

    return unique
