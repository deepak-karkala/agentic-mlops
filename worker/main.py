"""
Worker service for processing asynchronous jobs.

This service implements the worker side of the job queue system,
claiming and processing jobs using the FOR UPDATE SKIP LOCKED pattern
for distributed, fault-tolerant processing.
"""

import asyncio
import signal
import sys
import uuid
import logging
from contextlib import contextmanager

from libs.job_service import JobService
from libs.database import create_database_engine, create_session_maker
from libs.models import Job
from libs.graph import build_thin_graph


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WorkerService:
    """
    Asynchronous worker service for processing jobs.

    Features:
    - Graceful shutdown handling
    - Configurable polling intervals
    - Automatic job retry and failure handling
    - Lease-based job processing for fault tolerance
    """

    def __init__(
        self, worker_id: str = None, poll_interval: int = 5, lease_duration: int = 30
    ):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval  # seconds between job polls
        self.lease_duration = lease_duration  # minutes to hold job lease
        self.running = False
        self.graph = build_thin_graph()

        # Database setup
        self.engine = create_database_engine()
        self.SessionMaker = create_session_maker(self.engine)

        logger.info(f"Initialized worker {self.worker_id}")

    @contextmanager
    def get_job_service(self):
        """Context manager for job service with proper session handling."""
        session = self.SessionMaker()
        try:
            job_service = JobService(session)
            yield job_service
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    async def start(self):
        """Start the worker service with graceful shutdown handling."""
        self.running = True

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info(f"Worker {self.worker_id} starting...")

        try:
            await self.run_worker_loop()
        except Exception as e:
            logger.error(f"Worker loop failed: {e}")
            raise
        finally:
            logger.info(f"Worker {self.worker_id} stopped")

    async def run_worker_loop(self):
        """Main worker loop that polls for and processes jobs."""
        consecutive_empty_polls = 0
        max_empty_polls = 12  # Max empty polls before backing off
        backoff_multiplier = 2
        max_backoff = 60  # Maximum backoff in seconds

        while self.running:
            try:
                # Try to claim and process a job
                job_processed = await self.process_next_job()

                if job_processed:
                    consecutive_empty_polls = 0
                    # Short delay between jobs
                    await asyncio.sleep(1)
                else:
                    consecutive_empty_polls += 1

                    # Implement exponential backoff when no jobs are available
                    if consecutive_empty_polls > max_empty_polls:
                        backoff_time = min(
                            self.poll_interval
                            * (
                                backoff_multiplier
                                ** (consecutive_empty_polls - max_empty_polls)
                            ),
                            max_backoff,
                        )
                        logger.debug(
                            f"No jobs available, backing off for {backoff_time}s"
                        )
                        await asyncio.sleep(backoff_time)
                    else:
                        await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def process_next_job(self) -> bool:
        """
        Claim and process the next available job.

        Returns:
            True if a job was processed, False if no jobs were available
        """
        try:
            with self.get_job_service() as job_service:
                # Claim a job using FOR UPDATE SKIP LOCKED
                job = job_service.claim_job(self.worker_id, self.lease_duration)

                if not job:
                    return False

                logger.info(f"Claimed job {job.id} of type {job.job_type}")

                try:
                    # Process the job based on its type
                    await self.process_job(job)

                    # Mark job as completed
                    success = job_service.complete_job(job.id, self.worker_id)
                    if success:
                        logger.info(f"Successfully completed job {job.id}")
                    else:
                        logger.warning(f"Failed to mark job {job.id} as completed")

                    return True

                except Exception as e:
                    logger.error(f"Job {job.id} failed: {e}")

                    # Mark job as failed (with retry logic)
                    job_service.fail_job(job.id, self.worker_id, str(e))
                    return True

        except Exception as e:
            logger.error(f"Error claiming/processing job: {e}")
            return False

    async def process_job(self, job: Job):
        """
        Process a specific job based on its type.

        Args:
            job: The job to process
        """
        logger.info(f"Processing job {job.id} of type {job.job_type}")

        if job.job_type == "ml_workflow":
            await self.process_ml_workflow_job(job)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    async def process_ml_workflow_job(self, job: Job):
        """
        Process an ML workflow job by running the LangGraph.

        This currently runs the thin-slice graph but can be extended
        to handle more complex workflows as the system evolves.

        Args:
            job: The ML workflow job to process
        """
        payload = job.payload
        thread_id = payload.get("thread_id")
        messages = payload.get("messages", [])

        if not thread_id:
            raise ValueError("Job payload missing required thread_id")

        logger.info(f"Processing ML workflow for thread {thread_id}")

        # Convert messages back to LangChain format
        from langchain_core.messages import HumanMessage, AIMessage

        lc_messages = []
        for msg_data in messages:
            role = msg_data.get("role")
            content = msg_data.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            # Add other message types as needed

        state = {"messages": lc_messages}
        config = {"configurable": {"thread_id": thread_id}}

        # Execute the graph
        # In a real system, this might involve multiple steps, streaming, etc.
        await asyncio.get_event_loop().run_in_executor(
            None, self.graph.invoke, state, config
        )

        # Log the result for now
        # In the future, this would save results to decision_set, create artifacts, etc.
        logger.info(f"Graph execution completed for job {job.id}")

        # For now, we'll simulate some processing time
        await asyncio.sleep(2)


async def main():
    """Main entry point for the worker service."""
    worker = WorkerService()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
