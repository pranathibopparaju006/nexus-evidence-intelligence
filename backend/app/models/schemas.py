from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataSourceResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    ingestion_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    analysis_type: str = "full"
    options: Dict[str, Any] = Field(default_factory=dict)


class NarrativeDNA(BaseModel):
    # Flexible by design: local and LLM extraction can provide
    # different enrichment fields without breaking the API.
    core_claim: str = ""
    entities: List[Any] = Field(default_factory=list)
    events: List[Any] = Field(default_factory=list)
    locations: List[Any] = Field(default_factory=list)
    time_references: List[Any] = Field(default_factory=list)
    emotional_framing: str = "neutral"
    key_phrases: List[Any] = Field(default_factory=list)
    semantic_embedding: List[float] = Field(default_factory=list)
    supporting_claims: List[Any] = Field(default_factory=list)
    contradicting_claims: List[Any] = Field(default_factory=list)
    mutation_history: List[Dict[str, Any]] = Field(default_factory=list)
    propagation_pattern: str = "unknown"
    extraction_method: str = "unknown"

    # Mutation enrichment fields, when available.
    mutation_type: Optional[str] = None
    semantic_continuity: Optional[float] = None
    linguistic_change: Optional[float] = None
    entity_change: Optional[float] = None
    emotional_change: Optional[float] = None

    class Config:
        extra = "allow"


class EvidenceItem(BaseModel):
    # Findings currently store structured evidence as a JSON object.
    # Keep this flexible so new evidence fields do not break responses.
    type: Optional[str] = None
    description: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    supporting: bool = True

    class Config:
        extra = "allow"


class FindingResponse(BaseModel):
    id: int
    finding_type: str
    confidence_score: float
    claim_status: str
    abstain_reason: Optional[str] = None
    narrative_dna: Optional[NarrativeDNA] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    properties: Dict[str, Any]
    x: Optional[float] = None
    y: Optional[float] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    node_ids: List[str]
    significance: float


class AnalysisStatusResponse(BaseModel):
    job_id: int
    status: str
    progress: Optional[float] = None
    current_stage: Optional[str] = None
    message: Optional[str] = None
