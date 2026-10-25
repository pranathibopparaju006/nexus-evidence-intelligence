from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.database import Project, User, NarrativeFinding, DataSource
from app.models.schemas import FindingResponse
from app.agents.narrative_dna import NarrativeDNAAgent

router = APIRouter()


def _build_content_nodes(db: Session, project_id: int) -> list:
    """Reconstruct the uploaded source content for on-demand narrative fallback."""
    sources = db.query(DataSource).filter(
        DataSource.project_id == project_id,
        DataSource.ingestion_status == "completed"
    ).all()

    nodes = []
    for source in sources:
        metadata = source.extracted_metadata or {}
        extracted = metadata.get("content", {})
        items = extracted if isinstance(extracted, list) else [extracted]
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                item = {"text": str(item)}
            text = item.get("text") or item.get("content") or ""
            if not isinstance(text, str) or not text.strip():
                continue
            nodes.append({
                "id": f"content_{source.id}_{index}",
                "text": text,
                "timestamp": item.get("timestamp") or item.get("created_at") or metadata.get("processed_at"),
                "source": source.filename,
            })
    return nodes


def _ensure_narrative_dna(db: Session, project_id: int, findings: list) -> list:
    """Guarantee that the Narratives UI has usable DNA even if older findings were stored without it."""
    if not findings:
        return findings

    content_nodes = _build_content_nodes(db, project_id)
    if not content_nodes:
        return findings

    agent = NarrativeDNAAgent()
    dna_by_content = {}
    for node in content_nodes:
        try:
            dna = agent._local_extract_dna(node)
        except Exception as exc:
            print(f"Narrative fallback failed for {node.get('id')}: {exc}")
            dna = None
        if dna:
            dna_by_content[node["id"]] = dna

    if not dna_by_content:
        return findings

    first_dna = next(iter(dna_by_content.values()))
    first_id = next(iter(dna_by_content.keys()))

    enriched = []
    for finding in findings:
        # SQLAlchemy objects are converted to plain response dictionaries only
        # where needed; otherwise mutate the JSON field for this response.
        current = finding.narrative_dna if isinstance(finding.narrative_dna, dict) else {}
        has_claim = bool(str(current.get("core_claim", "")).strip())
        if has_claim:
            enriched.append(finding)
            continue

        evidence = finding.evidence if isinstance(finding.evidence, dict) else {}
        candidate = None

        for key in ("content_id", "content_a", "content_b"):
            value = evidence.get(key)
            if value in dna_by_content:
                candidate = dna_by_content[value]
                break

        if candidate is None:
            pair = evidence.get("entity_pair") or []
            wanted = {str(v).strip().lower() for v in pair if str(v).strip()}
            if wanted:
                for dna in dna_by_content.values():
                    entities = {
                        str(v.get("name") if isinstance(v, dict) else v).strip().lower()
                        for v in (dna.get("entities") or [])
                    }
                    if wanted.intersection(entities):
                        candidate = dna
                        break

        if candidate is None:
            candidate = first_dna

        # Make a fresh dict so the response never exposes a shared mutable object.
        finding.narrative_dna = dict(candidate)
        finding.narrative_dna["extraction_method"] = finding.narrative_dna.get(
            "extraction_method", "local_fallback"
        )
        evidence = dict(evidence)
        evidence.setdefault("narrative_content_id", first_id)
        finding.evidence = evidence
        enriched.append(finding)

    return enriched


@router.get("/{project_id}/narratives", response_model=List[FindingResponse])
async def get_narratives(
    project_id: int,
    finding_type: str = None,
    claim_status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(NarrativeFinding).filter(
        NarrativeFinding.project_id == project_id
    )
    if finding_type:
        query = query.filter(NarrativeFinding.finding_type == finding_type)
    if claim_status:
        query = query.filter(NarrativeFinding.claim_status == claim_status)

    findings = query.order_by(NarrativeFinding.confidence_score.desc()).all()
    return _ensure_narrative_dna(db, project_id, findings)


@router.get("/{project_id}/narratives/{finding_id}", response_model=FindingResponse)
async def get_narrative_detail(
    project_id: int,
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    finding = db.query(NarrativeFinding).filter(
        NarrativeFinding.id == finding_id,
        NarrativeFinding.project_id == project_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    return _ensure_narrative_dna(db, project_id, [finding])[0]
