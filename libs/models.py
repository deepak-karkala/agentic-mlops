"""
SQLAlchemy models for the Agentic MLOps platform.

These models define the core database schema for projects, decision sets,
events, artifacts, agent runs, and jobs as specified in Issue #6.
"""

import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_json_type():
    """Get appropriate JSON type for the current database."""
    # Use JSONB for PostgreSQL, JSON for others
    try:
        from sqlalchemy.dialects import postgresql
        return postgresql.JSONB
    except ImportError:
        return JSON


def get_uuid_type():
    """Get appropriate UUID type for the current database."""
    # Use UUID for PostgreSQL, String for others
    try:
        from sqlalchemy.dialects import postgresql
        return postgresql.UUID(as_uuid=False)
    except ImportError:
        return String(36)


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(str, Enum):
    """Agent run status enumeration."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class Project(Base):
    """
    A project represents a single MLOps system being designed.
    
    Each project can have multiple decision sets representing
    different iterations or versions of the design.
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    decision_sets: Mapped[list["DecisionSet"]] = relationship(
        "DecisionSet", back_populates="project", cascade="all, delete-orphan"
    )


class DecisionSet(Base):
    """
    A decision set represents a complete run of the MLOps design process.
    
    Each decision set has a version for optimistic locking and contains
    the state of the LangGraph workflow, including all agent decisions
    and user inputs.
    """

    __tablename__ = "decision_sets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="decision_sets")
    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="decision_set", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="decision_set", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="decision_set", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        "Job", back_populates="decision_set", cascade="all, delete-orphan"
    )


class Event(Base):
    """
    Events track all significant occurrences in the system.
    
    This includes user actions, agent state changes, job status updates,
    and other audit trail information.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    # Relationships
    decision_set: Mapped["DecisionSet"] = relationship(
        "DecisionSet", back_populates="events"
    )


class Artifact(Base):
    """
    Artifacts are generated outputs from the system.
    
    This includes generated code repositories, validation reports,
    cost analyses, and other files produced during the MLOps design process.
    """

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extra_metadata: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    # Relationships
    decision_set: Mapped["DecisionSet"] = relationship(
        "DecisionSet", back_populates="artifacts"
    )


class AgentRun(Base):
    """
    Agent runs track the execution of individual agents within a decision set.
    
    Each agent (planner, critic, codegen, etc.) creates a run record
    that tracks its inputs, outputs, and execution status.
    """

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        SQLEnum(AgentRunStatus), nullable=False, default=AgentRunStatus.RUNNING
    )
    input_data: Mapped[dict] = mapped_column(JSON)
    output_data: Mapped[dict] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    decision_set: Mapped["DecisionSet"] = relationship(
        "DecisionSet", back_populates="agent_runs"
    )


class Job(Base):
    """
    Jobs represent units of work to be processed asynchronously by workers.
    
    The job queue uses the FOR UPDATE SKIP LOCKED pattern for
    distributed processing with exactly-once semantics.
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), nullable=False, default=JobStatus.QUEUED
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(String(255))
    lease_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    decision_set: Mapped["DecisionSet"] = relationship(
        "DecisionSet", back_populates="jobs"
    )


def get_engine(database_url: str):
    """Create a SQLAlchemy engine from a database URL."""
    return create_engine(database_url, echo=False, pool_pre_ping=True)


def get_session_maker(engine):
    """Create a session maker from an engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_all_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all tables in the database (for testing)."""
    Base.metadata.drop_all(engine)