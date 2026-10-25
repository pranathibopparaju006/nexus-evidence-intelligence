from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
    Float
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# IMPORTANT: Use the same Base from core.database
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="analyst")
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")


class ProjectStatus(str, enum.Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.CREATED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    owner = relationship("User", back_populates="projects")
    data_sources = relationship("DataSource", back_populates="project")
    analyses = relationship("AnalysisJob", back_populates="project")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    file_type = Column(String)
    storage_path = Column(String)
    file_size = Column(Integer)
    ingestion_status = Column(String, default="pending")
    extracted_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="data_sources")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    job_type = Column(String)
    status = Column(String, default="queued")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="analyses")


class NarrativeFinding(Base):
    __tablename__ = "narrative_findings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    finding_type = Column(String)
    confidence_score = Column(Float)
    evidence = Column(JSON)
    claim_status = Column(String)
    abstain_reason = Column(Text, nullable=True)
    narrative_dna = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)