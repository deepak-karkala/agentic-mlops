"""
Worker service for processing asynchronous jobs.

This service implements the worker side of the job queue system,
claiming and processing jobs using the FOR UPDATE SKIP LOCKED pattern
for distributed, fault-tolerant processing.
"""

import asyncio
import os
import signal
import sys
import uuid
import logging
import httpx
from contextlib import contextmanager
from dotenv import load_dotenv

from libs.job_service import JobService
from libs.database import create_database_engine, create_session_maker
from libs.models import Job
from libs.graph import build_thin_graph, build_full_graph, build_streaming_test_graph
from libs.streaming_service import get_streaming_service

# Load environment variables from .env file
load_dotenv()


class WorkerStreamingClient:
    """HTTP client for worker to emit streaming events to API server."""

    def __init__(
        self, decision_set_id: str, api_base_url: str = "http://localhost:8000"
    ):
        self.decision_set_id = decision_set_id
        self.api_base_url = api_base_url

    async def _emit_event(self, event_data: dict):
        """Send event to API server."""
        url = f"{self.api_base_url}/api/streams/{self.decision_set_id}/emit"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=event_data, timeout=5.0)
                if response.status_code != 200:
                    logging.error(
                        f"Failed to emit event: {response.status_code} {response.text}"
                    )
        except Exception as e:
            logging.error(f"Error emitting streaming event: {e}")

    async def emit_reason_card(
        self,
        agent: str,
        node: str,
        reasoning: str,
        decision: str,
        category: str = "unknown",
        confidence: float = 0.5,
        inputs: dict = None,
        outputs: dict = None,
        alternatives_considered: list = None,
        priority: str = "medium",
    ):
        """Emit a reason card event."""
        await self._emit_event(
            {
                "event_type": "reason_card",
                "agent": agent,
                "node": node,
                "reasoning": reasoning,
                "decision": decision,
                "category": category,
                "confidence": confidence,
                "inputs": inputs or {},
                "outputs": outputs or {},
                "alternatives_considered": alternatives_considered or [],
                "priority": priority,
            }
        )

    async def emit_node_start(self, node_name: str, message: str = ""):
        """Emit a node start event."""
        await self._emit_event(
            {"event_type": "node_start", "node_name": node_name, "message": message}
        )

    async def emit_node_complete(
        self, node_name: str, message: str = "", outputs: dict = None
    ):
        """Emit a node completion event."""
        await self._emit_event(
            {
                "event_type": "node_complete",
                "node_name": node_name,
                "message": message,
                "outputs": outputs or {},
            }
        )

    async def emit_error(self, message: str):
        """Emit an error event."""
        await self._emit_event({"event_type": "error", "message": message})


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
        # Choose graph type based on environment variable
        graph_type = os.getenv("GRAPH_TYPE", "thin").lower()
        if graph_type == "full":
            logger.info("Using full graph with agent reasoning and streaming")
            self.graph = build_full_graph()
        elif graph_type == "streaming_test":
            logger.info("Using streaming test graph with only intake_extract agent")
            self.graph = build_streaming_test_graph()
        else:
            logger.info("Using thin graph for fast development")
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

        # Use decision_set_id for streaming events (this is what frontend SSE uses)
        decision_set_id = job.decision_set_id

        if not thread_id:
            raise ValueError("Job payload missing required thread_id")

        logger.info(
            f"Processing ML workflow for thread {thread_id}, decision_set {decision_set_id}"
        )

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

        # Execute the graph with streaming
        # Use HTTP-based streaming client to emit events to API server
        streaming_client = WorkerStreamingClient(decision_set_id)

        try:
            # Use .stream() with "updates" mode to get real-time agent reasoning
            logger.info(
                f"Starting LangGraph streaming for thread {thread_id}, emitting events to decision_set {decision_set_id}"
            )
            for chunk in self.graph.stream(state, config, stream_mode="updates"):
                # Process streaming updates and emit to SSE clients
                logger.info(
                    f"Received stream chunk: {type(chunk)} keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'not-dict'}"
                )
                await self._process_stream_chunk(
                    chunk, decision_set_id, streaming_client
                )
            logger.info(f"LangGraph streaming completed for thread {thread_id}")
        except Exception as stream_error:
            logger.error(f"Streaming execution failed: {stream_error}")
            await streaming_client.emit_error(
                f"Workflow execution failed: {str(stream_error)}"
            )
            raise

        # Log the result for now
        # In the future, this would save results to decision_set, create artifacts, etc.
        logger.info(f"Graph execution completed for job {job.id}")

        # For now, we'll simulate some processing time
        await asyncio.sleep(2)

    async def _process_stream_chunk(
        self, chunk, decision_set_id: str, streaming_client
    ):
        """
        Process a single stream chunk from LangGraph and emit appropriate SSE events.

        Args:
            chunk: Stream chunk from LangGraph (contains node updates)
            decision_set_id: Decision set ID for routing SSE events
            streaming_client: HTTP streaming client for emitting events to API server
        """
        try:
            logger.debug(f"Processing stream chunk: {chunk}")

            # chunk format: {node_name: node_state_update}
            for node_name, node_update in chunk.items():
                logger.info(f"Node update: {node_name} -> {node_update}")

                # Emit node start event
                await streaming_client.emit_node_start(
                    node_name, f"Starting {node_name}"
                )

                # Look for reason cards in the node state
                if hasattr(node_update, "reason_cards") and node_update.reason_cards:
                    streaming_service = get_streaming_service()
                    for reason_card in node_update.reason_cards:
                        await streaming_service.emit_reason_card(reason_card)

                # Look for reason cards in nested state structures
                elif isinstance(node_update, dict):
                    reason_cards = node_update.get("reason_cards", [])
                    logger.info(
                        f"Found {len(reason_cards)} reason cards in dict structure"
                    )
                    for i, reason_card in enumerate(reason_cards):
                        logger.info(
                            f"Processing reason card {i + 1}: type={type(reason_card)}, has_model_dump={hasattr(reason_card, 'model_dump')}"
                        )
                        if hasattr(reason_card, "model_dump"):  # Pydantic model
                            # Emit reason card via HTTP API
                            await streaming_client.emit_reason_card(
                                agent=reason_card.agent,
                                node=reason_card.node,
                                reasoning=reason_card.reasoning,
                                decision=reason_card.decision,
                                category=reason_card.category,
                                confidence=reason_card.confidence,
                                inputs=reason_card.inputs,
                                outputs=reason_card.outputs,
                                alternatives_considered=reason_card.alternatives_considered,
                                priority=reason_card.priority,
                            )
                        elif isinstance(
                            reason_card, dict
                        ):  # Dictionary-based reason card
                            logger.info(
                                f"Emitting dict-based reason card: {reason_card.get('agent', 'unknown')}"
                            )
                            # Emit dictionary-based reason card via HTTP API
                            await streaming_client.emit_reason_card(
                                agent=reason_card.get("agent", "unknown"),
                                node=reason_card.get("node_name", "unknown"),
                                reasoning=reason_card.get("outputs", {}).get(
                                    "extraction_rationale", "No rationale provided"
                                ),
                                decision=f"Extracted constraints with {reason_card.get('confidence', 0)} confidence",
                                category="constraint_extraction",
                                confidence=reason_card.get("confidence", 0.5),
                                inputs=reason_card.get("inputs", {}),
                                outputs=reason_card.get("outputs", {}),
                                alternatives_considered=[],
                                priority="medium",
                            )
                        else:
                            logger.warning(
                                f"Unknown reason card type: {type(reason_card)}, skipping"
                            )

                # Emit node completion
                await streaming_client.emit_node_complete(
                    node_name, f"Completed {node_name}"
                )

        except Exception as e:
            logger.error(f"Error processing stream chunk: {e}")
            await streaming_client.emit_error(f"Stream processing error: {str(e)}")


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
