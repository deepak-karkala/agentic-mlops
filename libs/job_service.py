"""
Job service for managing asynchronous job queue operations.

This module provides the core functionality for creating, claiming, and
processing jobs in the distributed worker system.
"""

import datetime
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

import logging

from libs.models import Job, JobStatus, DecisionSet, Project
from libs.database import create_database_engine, create_session_maker

logger = logging.getLogger(__name__)


class JobService:
    """Service class for job queue operations."""

    def __init__(self, session: Session):
        self.session = session

    def create_job(
        self,
        decision_set_id: str,
        job_type: str,
        payload: dict,
        priority: int = 0,
        max_retries: int = 3,
    ) -> Job:
        """
        Create a new job in the queue.

        Args:
            decision_set_id: The decision set this job belongs to
            job_type: Type of job (e.g., "ml_workflow", "codegen")
            payload: Job-specific data including thread_id
            priority: Job priority (higher = more important)
            max_retries: Maximum number of retry attempts

        Returns:
            The created Job instance
        """
        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=decision_set_id,
            job_type=job_type,
            priority=priority,
            status=JobStatus.QUEUED,
            payload=payload,
            max_retries=max_retries,
            retry_count=0,
        )

        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        logger.info(
            "Job created",
            extra={
                "job_id": job.id,
                "type": job_type,
                "decision_set_id": decision_set_id,
                "priority": priority,
            },
        )
        return job

    def claim_job(
        self, worker_id: str, lease_duration_minutes: int = 30
    ) -> Optional[Job]:
        """
        Claim the next available job using FOR UPDATE SKIP LOCKED pattern.

        This ensures exactly-once processing by atomically claiming jobs
        and preventing race conditions between workers.

        Args:
            worker_id: Unique identifier for the worker
            lease_duration_minutes: How long to hold the job lease

        Returns:
            Claimed Job instance or None if no jobs available
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        lease_expires_at = now + datetime.timedelta(minutes=lease_duration_minutes)

        # Find the next job to process using FOR UPDATE SKIP LOCKED
        # This query will:
        # 1. Find jobs that are QUEUED or have expired leases
        # 2. Order by priority (desc) then created_at (asc)
        # 3. Lock the first row for update, skipping locked rows
        # 4. Update the job atomically to claim it

        job = (
            self.session.query(Job)
            .filter(
                and_(
                    Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
                    # Include jobs that are running but have expired leases
                    func.coalesce(Job.lease_expires_at, now) <= now,
                )
            )
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )

        if job:
            # Claim the job
            job.status = JobStatus.RUNNING
            job.worker_id = worker_id
            job.lease_expires_at = lease_expires_at
            job.started_at = now

            self.session.commit()
            self.session.refresh(job)
            logger.info(
                "Job claimed",
                extra={
                    "job_id": job.id,
                    "worker_id": worker_id,
                    "lease_expires_at": str(lease_expires_at),
                },
            )

        return job

    def complete_job(self, job_id: str, worker_id: str) -> bool:
        """
        Mark a job as completed.

        Args:
            job_id: ID of the job to complete
            worker_id: ID of the worker completing the job (for verification)

        Returns:
            True if job was successfully completed, False otherwise
        """
        job = (
            self.session.query(Job)
            .filter(
                and_(
                    Job.id == job_id,
                    Job.worker_id == worker_id,
                    Job.status == JobStatus.RUNNING,
                )
            )
            .first()
        )

        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            job.worker_id = None
            job.lease_expires_at = None

            self.session.commit()
            logger.info(
                "Job completed", extra={"job_id": job_id, "worker_id": worker_id}
            )
            return True

        return False

    def fail_job(self, job_id: str, worker_id: str, error_message: str) -> bool:
        """
        Mark a job as failed, with retry logic.

        Args:
            job_id: ID of the job that failed
            worker_id: ID of the worker reporting the failure
            error_message: Description of the failure

        Returns:
            True if job was processed, False otherwise
        """
        job = (
            self.session.query(Job)
            .filter(
                and_(
                    Job.id == job_id,
                    Job.worker_id == worker_id,
                    Job.status == JobStatus.RUNNING,
                )
            )
            .first()
        )

        if job:
            job.retry_count += 1
            job.error_message = error_message

            if job.retry_count >= job.max_retries:
                # Max retries exceeded, mark as failed
                job.status = JobStatus.FAILED
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                job.worker_id = None
                job.lease_expires_at = None
                logger.error(
                    "Job failed (max retries)",
                    extra={
                        "job_id": job_id,
                        "worker_id": worker_id,
                        "error": error_message,
                    },
                )
            else:
                # Retry the job by putting it back in the queue
                job.status = JobStatus.QUEUED
                job.worker_id = None
                job.lease_expires_at = None
                job.started_at = None
                logger.warning(
                    "Job requeued after failure",
                    extra={
                        "job_id": job_id,
                        "worker_id": worker_id,
                        "retry_count": job.retry_count,
                        "error": error_message,
                    },
                )

            self.session.commit()
            return True

        return False

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get the current status of a job."""
        job = self.session.query(Job).filter(Job.id == job_id).first()
        return job.status if job else None

    def get_pending_jobs_count(self) -> int:
        """Get the number of jobs waiting to be processed."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return (
            self.session.query(Job)
            .filter(
                and_(
                    Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
                    func.coalesce(Job.lease_expires_at, now) <= now,
                )
            )
            .count()
        )

    def get_jobs_for_decision_set(self, decision_set_id: str) -> List[Job]:
        """Get all jobs for a specific decision set."""
        return (
            self.session.query(Job)
            .filter(Job.decision_set_id == decision_set_id)
            .order_by(Job.created_at.desc())
            .all()
        )


def create_job_service() -> JobService:
    """
    Create a JobService instance with a database session.

    This is a convenience function for creating job services.
    In production, you may want to use dependency injection.
    """
    engine = create_database_engine()
    session_maker = create_session_maker(engine)
    session = session_maker()

    return JobService(session)


def create_decision_set_for_thread(
    session: Session,
    thread_id: str,
    user_prompt: str,
    project_id: str = "default-project",
) -> DecisionSet:
    """
    Create a decision set for a thread_id.

    This links the LangGraph thread_id to our job system.

    Args:
        session: Database session
        thread_id: Thread ID from LangGraph
        user_prompt: The user's initial prompt
        project_id: Project this decision set belongs to

    Returns:
        Created DecisionSet instance
    """
    # Ensure default project exists
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        project = Project(
            id=project_id,
            name="Default Project",
            description="Default project for chat interactions",
        )
        session.add(project)

    decision_set = DecisionSet(
        id=str(uuid.uuid4()),
        project_id=project_id,
        thread_id=thread_id,
        user_prompt=user_prompt,
        status="active",
    )

    session.add(decision_set)
    session.commit()
    session.refresh(decision_set)

    return decision_set
