"""
Unit tests for SQLAlchemy models.

These tests verify that the SQLAlchemy models correctly map to the schema
and that all relationships work as expected.
"""

import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from libs.models import (
    Base,
    Project,
    DecisionSet,
    Event,
    Artifact,
    AgentRun,
    Job,
    JobStatus,
    AgentRunStatus,
    get_engine,
    get_session_maker,
    create_all_tables,
    drop_all_tables,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")

    # Create tables directly without using our utility functions
    # to handle SQLite-specific requirements
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_project(db_session):
    """Create a sample project for testing."""
    project = Project(
        id=str(uuid.uuid4()),
        name="Test MLOps Project",
        description="A test project for unit testing",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_decision_set(db_session, sample_project):
    """Create a sample decision set for testing."""
    decision_set = DecisionSet(
        id=str(uuid.uuid4()),
        project_id=sample_project.id,
        thread_id="test-thread-123",
        user_prompt="Create a machine learning pipeline for image classification",
        version=1,
    )
    db_session.add(decision_set)
    db_session.commit()
    db_session.refresh(decision_set)
    return decision_set


class TestProject:
    """Test the Project model."""

    def test_create_project(self, db_session):
        """Test creating a project with required fields."""
        project = Project(id=str(uuid.uuid4()), name="Test Project")
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description is None
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_create_project_with_description(self, db_session):
        """Test creating a project with description."""
        project = Project(
            id=str(uuid.uuid4()), name="Test Project", description="A test project"
        )
        db_session.add(project)
        db_session.commit()

        assert project.description == "A test project"

    def test_project_decision_sets_relationship(self, db_session, sample_project):
        """Test the relationship between project and decision sets."""
        # Create decision sets for the project
        ds1 = DecisionSet(
            id=str(uuid.uuid4()),
            project_id=sample_project.id,
            thread_id="thread-1",
            user_prompt="Prompt 1",
            version=1,
        )
        ds2 = DecisionSet(
            id=str(uuid.uuid4()),
            project_id=sample_project.id,
            thread_id="thread-2",
            user_prompt="Prompt 2",
            version=1,
        )

        db_session.add_all([ds1, ds2])
        db_session.commit()

        # Test relationship
        assert len(sample_project.decision_sets) == 2
        assert ds1 in sample_project.decision_sets
        assert ds2 in sample_project.decision_sets


class TestDecisionSet:
    """Test the DecisionSet model."""

    def test_create_decision_set(self, db_session, sample_project):
        """Test creating a decision set with required fields."""
        decision_set = DecisionSet(
            id=str(uuid.uuid4()),
            project_id=sample_project.id,
            thread_id="unique-thread-id",
            user_prompt="Create an ML pipeline",
            version=1,
        )
        db_session.add(decision_set)
        db_session.commit()

        assert decision_set.id is not None
        assert decision_set.thread_id == "unique-thread-id"
        assert decision_set.user_prompt == "Create an ML pipeline"
        assert decision_set.version == 1
        assert decision_set.status == "active"  # Default status

    def test_decision_set_version_for_optimistic_locking(
        self, db_session, sample_project
    ):
        """Test that decision set has version column for optimistic locking."""
        decision_set = DecisionSet(
            id=str(uuid.uuid4()),
            project_id=sample_project.id,
            thread_id="thread-for-version-test",
            user_prompt="Test version",
            version=5,  # Custom version
        )
        db_session.add(decision_set)
        db_session.commit()

        assert decision_set.version == 5

    def test_decision_set_relationships(self, db_session, sample_decision_set):
        """Test all relationships from decision set."""
        # Create related objects
        event = Event(
            decision_set_id=sample_decision_set.id,
            event_type="test_event",
            event_data={"test": "data"},
        )

        artifact = Artifact(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            artifact_type="code",
            filename="test.py",
            s3_key="artifacts/test.py",
            size_bytes=1024,
            content_hash="abc123",
            extra_metadata={"language": "python"},
        )

        agent_run = AgentRun(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            agent_name="planner",
            status=AgentRunStatus.COMPLETED,
            input_data={"prompt": "plan"},
            output_data={"plan": "result"},
        )

        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            job_type="ml_workflow",
            payload={"task": "generate"},
            status=JobStatus.QUEUED,
        )

        db_session.add_all([event, artifact, agent_run, job])
        db_session.commit()

        # Test relationships
        assert len(sample_decision_set.events) == 1
        assert len(sample_decision_set.artifacts) == 1
        assert len(sample_decision_set.agent_runs) == 1
        assert len(sample_decision_set.jobs) == 1


class TestEvent:
    """Test the Event model."""

    def test_create_event(self, db_session, sample_decision_set):
        """Test creating an event with JSONB data."""
        event_data = {
            "action": "user_input",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"message": "Started new workflow"},
        }

        event = Event(
            decision_set_id=sample_decision_set.id,
            event_type="user_action",
            event_data=event_data,
        )
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert event.event_type == "user_action"
        assert event.event_data == event_data
        assert event.created_at is not None


class TestArtifact:
    """Test the Artifact model."""

    def test_create_artifact(self, db_session, sample_decision_set):
        """Test creating an artifact with all fields."""
        metadata = {"language": "python", "framework": "tensorflow", "version": "2.0"}

        artifact = Artifact(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            artifact_type="generated_code",
            filename="ml_pipeline.py",
            s3_key="artifacts/proj123/ml_pipeline.py",
            size_bytes=2048,
            content_hash="sha256abc123",
            extra_metadata=metadata,
        )
        db_session.add(artifact)
        db_session.commit()

        assert artifact.id is not None
        assert artifact.artifact_type == "generated_code"
        assert artifact.filename == "ml_pipeline.py"
        assert artifact.s3_key == "artifacts/proj123/ml_pipeline.py"
        assert artifact.size_bytes == 2048
        assert artifact.content_hash == "sha256abc123"
        assert artifact.extra_metadata == metadata


class TestAgentRun:
    """Test the AgentRun model."""

    def test_create_agent_run(self, db_session, sample_decision_set):
        """Test creating an agent run with input and output data."""
        input_data = {"user_requirements": "Build ML pipeline"}
        output_data = {"plan": "Use TensorFlow with Docker deployment"}

        agent_run = AgentRun(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            agent_name="ml_planner",
            status=AgentRunStatus.RUNNING,
            input_data=input_data,
            output_data=output_data,
        )
        db_session.add(agent_run)
        db_session.commit()

        assert agent_run.id is not None
        assert agent_run.agent_name == "ml_planner"
        assert agent_run.status == AgentRunStatus.RUNNING
        assert agent_run.input_data == input_data
        assert agent_run.output_data == output_data
        assert agent_run.started_at is not None

    def test_agent_run_status_enum(self, db_session, sample_decision_set):
        """Test that agent run status uses proper enum values."""
        agent_run = AgentRun(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            agent_name="test_agent",
            status=AgentRunStatus.FAILED,
            input_data={},
            output_data={},
            error_message="Test error message",
        )
        db_session.add(agent_run)
        db_session.commit()

        assert agent_run.status == AgentRunStatus.FAILED
        assert agent_run.error_message == "Test error message"


class TestJob:
    """Test the Job model."""

    def test_create_job(self, db_session, sample_decision_set):
        """Test creating a job with all required fields."""
        payload = {
            "workflow_type": "ml_training",
            "parameters": {"epochs": 100, "batch_size": 32},
        }

        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            job_type="ml_workflow",
            payload=payload,
            priority=5,
            max_retries=3,
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.job_type == "ml_workflow"
        assert job.payload == payload
        assert job.priority == 5
        assert job.status == JobStatus.QUEUED  # Default status
        assert job.max_retries == 3
        assert job.retry_count == 0  # Default value

    def test_job_status_enum(self, db_session, sample_decision_set):
        """Test job status enum values."""
        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            job_type="test_job",
            payload={"test": True},
            status=JobStatus.RUNNING,
            worker_id="worker-001",
        )
        db_session.add(job)
        db_session.commit()

        assert job.status == JobStatus.RUNNING
        assert job.worker_id == "worker-001"

    def test_job_for_update_skip_locked_pattern(self, db_session, sample_decision_set):
        """Test that job has fields necessary for FOR UPDATE SKIP LOCKED pattern."""
        # Use timezone-naive datetime for SQLite compatibility
        now = datetime.now()

        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=sample_decision_set.id,
            job_type="background_task",
            payload={"task": "process"},
            status=JobStatus.RUNNING,
            worker_id="worker-123",
            lease_expires_at=now,
            started_at=now,
        )
        db_session.add(job)
        db_session.commit()

        assert job.worker_id == "worker-123"
        assert job.lease_expires_at == now
        assert job.started_at == now


class TestModelUtilities:
    """Test utility functions."""

    def test_get_engine(self):
        """Test get_engine utility function."""
        engine = get_engine("sqlite:///:memory:")
        assert engine is not None

    def test_get_session_maker(self):
        """Test get_session_maker utility function."""
        engine = get_engine("sqlite:///:memory:")
        session_maker = get_session_maker(engine)
        assert session_maker is not None

    def test_create_and_drop_tables(self):
        """Test create_all_tables and drop_all_tables functions."""
        engine = get_engine("sqlite:///:memory:")

        # Create tables
        create_all_tables(engine)

        # Verify tables exist by attempting to query
        SessionLocal = get_session_maker(engine)
        session = SessionLocal()

        try:
            # This should not raise an error if tables exist
            session.query(Project).count()
            session.query(DecisionSet).count()
            session.query(Event).count()
            session.query(Artifact).count()
            session.query(AgentRun).count()
            session.query(Job).count()
        finally:
            session.close()

        # Drop tables
        drop_all_tables(engine)
