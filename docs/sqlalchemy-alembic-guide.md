# SQLAlchemy & Alembic Guide for Agentic MLOps Platform

This guide explains all the database-related concepts used in our project, from basic SQLAlchemy concepts to how they integrate into our agentic MLOps architecture.

## Table of Contents

1. [What is SQLAlchemy?](#what-is-sqlalchemy)
2. [Basic SQLAlchemy Concepts](#basic-sqlalchemy-concepts)
3. [What is Alembic?](#what-is-alembic)
4. [Our Project's Database Architecture](#our-projects-database-architecture)
5. [Detailed Code Walkthrough](#detailed-code-walkthrough)
6. [How It All Fits Together](#how-it-all-fits-together)

## What is SQLAlchemy?

**SQLAlchemy** is Python's most popular Object-Relational Mapping (ORM) library. It allows you to:

- Work with databases using Python objects instead of raw SQL
- Define database tables as Python classes
- Handle relationships between tables automatically
- Write database-agnostic code (works with PostgreSQL, SQLite, MySQL, etc.)

Think of it as a translator between Python objects and database tables.

## Basic SQLAlchemy Concepts

### 1. DeclarativeBase

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
```

**What it does**: This is the foundation class that all your database models inherit from. It provides the magic that turns Python classes into database tables.

### 2. mapped_column

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
```

**What it does**: 
- `Mapped[str]` tells Python the type of the field
- `mapped_column()` defines how this field becomes a database column
- `String(36)` = varchar(36) in the database
- `primary_key=True` makes this the table's primary key
- `nullable=False` means this field cannot be empty

### 3. Relationships

```python
class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # One project has many decision sets
    decision_sets: Mapped[list["DecisionSet"]] = relationship(
        "DecisionSet", back_populates="project"
    )

class DecisionSet(Base):
    __tablename__ = "decision_sets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    
    # Each decision set belongs to one project
    project: Mapped["Project"] = relationship("Project", back_populates="decision_sets")
```

**What it does**:
- `relationship()` creates Python object connections between tables
- `ForeignKey("projects.id")` creates the actual database foreign key
- `back_populates` creates bidirectional relationships
- Now you can do: `project.decision_sets` to get all decision sets for a project

### 4. Sessions and SessionMaker

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database connection
engine = create_engine("postgresql://user:pass@localhost/dbname")

# Create session factory
SessionLocal = sessionmaker(bind=engine)

# Use session to interact with database
session = SessionLocal()
project = Project(name="My Project")
session.add(project)
session.commit()
session.close()
```

**What it does**:
- `engine` = connection to the database
- `sessionmaker` = factory for creating database sessions
- `session` = your workspace for database operations (like a transaction)
- `add()` = stage an object to be saved
- `commit()` = actually save to database
- `close()` = cleanup the session

## What is Alembic?

**Alembic** is SQLAlchemy's database migration tool. It handles:

- **Schema evolution**: Adding/removing tables and columns over time
- **Version control for your database**: Track changes to your database structure
- **Team synchronization**: Everyone gets the same database structure
- **Production deployments**: Safely update production databases

### Migration Workflow

1. **You change your models** (add a new field, create a new table)
2. **Generate migration**: `alembic revision --autogenerate -m "Add new field"`
3. **Review migration**: Check the generated SQL is correct
4. **Apply migration**: `alembic upgrade head`
5. **Commit migration file**: Add to version control

## Our Project's Database Architecture

Our database is designed to support the complete MLOps agent workflow:

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│   Project   │ 1:N│  DecisionSet    │ 1:N│   Event     │
│             │───▶│                 │───▶│             │
│ - id        │    │ - id            │    │ - id        │
│ - name      │    │ - project_id    │    │ - event_data│
│ - desc      │    │ - version ⚡     │    │ - type      │
└─────────────┘    │ - thread_id     │    └─────────────┘
                   │ - user_prompt   │
                   └─────────────────┘
                           │ 1:N
                   ┌───────┼───────┐
                   │       │       │
                   ▼       ▼       ▼
            ┌─────────┐ ┌─────────┐ ┌─────────┐
            │Artifact │ │AgentRun │ │   Job   │
            │         │ │         │ │         │
            │- s3_key │ │- status │ │- status │
            │- size   │ │- input  │ │- payload│
            └─────────┘ │- output │ │- worker │
                        └─────────┘ └─────────┘
```

**⚡ Version Column**: Used for optimistic locking - prevents concurrent updates from corrupting data.

## Detailed Code Walkthrough

Let's break down our models step by step:

### 1. Project Model

```python
class Project(Base):
    """A project represents a single MLOps system being designed."""
    
    __tablename__ = "projects"
    
    # Primary key - unique identifier
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Basic project information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Automatic timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    
    # Relationships - one project can have many decision sets
    decision_sets: Mapped[list["DecisionSet"]] = relationship(
        "DecisionSet", back_populates="project", cascade="all, delete-orphan"
    )
```

**Key points**:
- `Optional[str]` means the field can be None (nullable)
- `Text` allows unlimited text (vs String which has a limit)
- `default=lambda: ...` sets the value when creating new records
- `onupdate=lambda: ...` updates the value when modifying records
- `cascade="all, delete-orphan"` means if you delete a project, all its decision sets get deleted too

### 2. DecisionSet Model - The Heart of Our Workflow

```python
class DecisionSet(Base):
    """A decision set represents a complete run of the MLOps design process."""
    
    __tablename__ = "decision_sets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    
    # CRITICAL: Version for optimistic locking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # LangGraph integration
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    # User's original request
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    
    # ... timestamps and relationships
```

**Key points**:
- `ForeignKey("projects.id")` links this to a specific project
- `version` is crucial for optimistic locking (prevents concurrent edits)
- `thread_id` connects to LangGraph's conversation threading
- `unique=True` ensures no duplicate thread_ids

### 3. Event Model - Audit Trail

```python
class Event(Base):
    """Events track all significant occurrences in the system."""
    
    __tablename__ = "events"
    
    # Auto-incrementing integer ID (good for high-volume inserts)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # JSON field for flexible event data
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
```

**Key points**:
- `autoincrement=True` makes the database auto-generate sequential IDs
- `JSON` column stores structured data (becomes JSONB in PostgreSQL for better performance)
- Perfect for logging user actions, agent state changes, etc.

### 4. Job Model - Asynchronous Processing

```python
class Job(Base):
    """Jobs represent units of work to be processed asynchronously by workers."""
    
    __tablename__ = "jobs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_sets.id"), nullable=False
    )
    
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), nullable=False, default=JobStatus.QUEUED
    )
    
    # The actual work to be done
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # FOR UPDATE SKIP LOCKED pattern fields
    worker_id: Mapped[Optional[str]] = mapped_column(String(255))
    lease_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    
    # Retry logic
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

**Key points**:
- `SQLEnum(JobStatus)` creates a database enum for job statuses
- `worker_id` and `lease_expires_at` enable distributed job processing
- `FOR UPDATE SKIP LOCKED` pattern prevents multiple workers from claiming the same job

## How It All Fits Together

### 1. In Our FastAPI Application

```python
from libs.models import get_engine, get_session_maker

# Create database connection
engine = get_engine(database_url)
SessionLocal = get_session_maker(engine)

# In your FastAPI endpoint
def create_project(name: str):
    session = SessionLocal()
    try:
        project = Project(id=str(uuid.uuid4()), name=name)
        session.add(project)
        session.commit()
        return project
    finally:
        session.close()
```

### 2. LangGraph Integration

```python
# When starting a new workflow
def start_workflow(project_id: str, user_prompt: str):
    session = SessionLocal()
    
    # Create decision set (represents one complete workflow run)
    decision_set = DecisionSet(
        id=str(uuid.uuid4()),
        project_id=project_id,
        thread_id=f"thread_{uuid.uuid4()}",  # LangGraph thread ID
        user_prompt=user_prompt,
        version=1
    )
    session.add(decision_set)
    
    # Log the start event
    event = Event(
        decision_set_id=decision_set.id,
        event_type="workflow_started",
        event_data={"prompt": user_prompt, "timestamp": datetime.utcnow().isoformat()}
    )
    session.add(event)
    
    session.commit()
    return decision_set.thread_id  # Pass to LangGraph
```

### 3. Job Queue Pattern

```python
# Worker claiming jobs (FOR UPDATE SKIP LOCKED pattern)
def claim_next_job(worker_id: str):
    session = SessionLocal()
    
    # This is atomic - only one worker can claim each job
    job = session.query(Job).filter(
        Job.status == JobStatus.QUEUED
    ).order_by(Job.priority.desc(), Job.created_at).with_for_update(
        skip_locked=True
    ).first()
    
    if job:
        job.status = JobStatus.RUNNING
        job.worker_id = worker_id
        job.lease_expires_at = datetime.utcnow() + timedelta(minutes=30)
        session.commit()
    
    return job
```

### 4. Database Migrations in Practice

```bash
# You modify a model (add a new field)
class Project(Base):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    budget: Mapped[Optional[float]] = mapped_column(Float)  # NEW FIELD

# Generate migration
alembic revision --autogenerate -m "Add budget field to projects"

# This creates a file like: versions/abc123_add_budget_field.py
def upgrade():
    op.add_column('projects', sa.Column('budget', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('projects', 'budget')

# Apply migration
alembic upgrade head
```

## Why This Architecture Works for Our MLOps Platform

### 1. **Scalable Workflow Tracking**
- Each `DecisionSet` represents one complete MLOps design workflow
- All related data (events, artifacts, agent runs, jobs) link to the decision set
- Easy to track progress and resume interrupted workflows

### 2. **Asynchronous Processing**
- Long-running agent workflows don't block the API
- Jobs can be distributed across multiple worker processes
- Retry logic handles failures gracefully

### 3. **Optimistic Locking**
- The `version` field prevents concurrent modifications
- Critical for multi-user environments where multiple people might edit the same project

### 4. **Comprehensive Audit Trail**
- Every action gets logged as an `Event`
- Full history of what happened when
- Essential for debugging and compliance

### 5. **Flexible Data Storage**
- JSON fields store complex agent inputs/outputs
- Schema can evolve without breaking existing data

### 6. **LangGraph Integration**
- `thread_id` connects our database to LangGraph conversations
- Persistent state survives service restarts
- Can resume workflows from any point

This architecture provides the robust foundation needed for a production-ready agentic system that can handle complex, long-running workflows with proper error handling, scalability, and observability.