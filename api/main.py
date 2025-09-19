from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import contextmanager
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session
import logging
import time

from libs.graph import build_full_graph, build_thin_graph, build_streaming_test_graph, build_hitl_graph, build_hitl_enhanced_graph
from libs.job_service import JobService, create_decision_set_for_thread
from libs.database import create_database_engine, create_session_maker
from libs.models import JobStatus, Job, DecisionSet
from langgraph.types import Command

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure structured logging (Issue #16)
# Enhanced format for CloudWatch logs with run_id and thread_id correlation
log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
if os.getenv("ENVIRONMENT") == "production":
    # CloudWatch-friendly JSON structured logging for production
    import json
    import logging.config

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "default": {
                "format": log_format,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if os.getenv("ENVIRONMENT") == "production" else "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "handlers": ["console"],
        },
    }

    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except ImportError:
        # Fallback to basic logging if pythonjsonlogger is not available
        logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=log_format)
else:
    # Development: simple formatted logs
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=log_format)

logger = logging.getLogger(__name__)

# Configure LangSmith tracing (Issue #16)
# LangSmith will automatically be enabled if LANGCHAIN_TRACING_V2=true in environment
if os.getenv("LANGCHAIN_TRACING_V2"):
    logger.info("LangSmith tracing enabled for project: %s", os.getenv("LANGCHAIN_PROJECT", "agentic-mlops"))

# CORS configuration based on environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production: Allow AWS App Runner domains (more secure than wildcard)
    allowed_origins = [
        # AWS App Runner domains have predictable patterns
        "https://*.amazonaws.com",
    ]

    allow_credentials = True
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    allowed_headers = ["Content-Type", "Authorization"]
else:
    # Development: Allow localhost and common dev ports
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    allow_credentials = True
    allowed_methods = ["*"]
    allowed_headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Simple root endpoint for health checks."""
    logger.debug("Health check invoked")
    return {"message": "Agentic MLOps API"}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    thread_id: Optional[str] = None  # Optional for backward compatibility


class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    thread_id: str  # Always return thread_id for client tracking


class AsyncChatResponse(BaseModel):
    decision_set_id: str  # ID for tracking the conversation
    thread_id: str  # LangGraph thread_id for state persistence
    job_id: str  # ID for tracking job status
    status: str  # Current job status


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    decision_set_id: str
    thread_id: str


class ApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: Optional[str] = None
    approved_by: Optional[str] = None


class ApprovalResponse(BaseModel):
    success: bool
    message: str
    decision_set_id: str
    thread_id: str
    approval_status: str


class WorkflowPlanResponse(BaseModel):
    nodes: List[str]
    graph_type: str


# Select graph based on env flag, with safe fallback
# Support both legacy USE_FULL_GRAPH and new GRAPH_TYPE environment variables
USE_FULL_GRAPH = os.getenv("USE_FULL_GRAPH", "false").lower() in {"1", "true", "yes"}
GRAPH_TYPE = os.getenv("GRAPH_TYPE", "thin").lower()

try:
    if GRAPH_TYPE == "full" or USE_FULL_GRAPH:
        logger.info("Initializing full graph with agent reasoning and streaming")
        _graph = build_full_graph()
    elif GRAPH_TYPE == "streaming_test":
        logger.info("Initializing streaming test graph with 2-agent workflow for debugging: intake_extract (30s sleep) → coverage_check (60s sleep)")
        _graph = build_streaming_test_graph()
    elif GRAPH_TYPE == "hitl":
        logger.info("Initializing HITL graph for Human-in-the-Loop testing: intake_extract → coverage_check → adaptive_questions → gate_hitl → planner")
        _graph = build_hitl_graph()
    elif GRAPH_TYPE == "hitl_enhanced":
        logger.info("Initializing Enhanced HITL graph with auto-approval and loop-back: intake_extract → coverage_check → adaptive_questions → hitl_gate_user → loop-back or continue → planner")
        _graph = build_hitl_enhanced_graph()
    else:
        logger.info("Initializing thin graph for fast development")
        _graph = build_thin_graph()
except Exception as e:
    logger.warning(
        "Graph init failed; falling back to thin graph", extra={"error": str(e)}
    )
    _graph = build_thin_graph()

# Database setup
engine = create_database_engine()
SessionMaker = create_session_maker(engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionMaker()
    try:
        yield db
    finally:
        db.close()


def _convert_to_langchain_message(chat_msg: ChatMessage):
    """Convert our ChatMessage to a Langchain message object."""
    if chat_msg.role == "user":
        return HumanMessage(content=chat_msg.content)
    elif chat_msg.role == "assistant":
        return AIMessage(content=chat_msg.content)
    elif chat_msg.role == "system":
        return SystemMessage(content=chat_msg.content)
    elif chat_msg.role == "tool":
        return ToolMessage(content=chat_msg.content, tool_call_id="")
    else:
        return HumanMessage(content=chat_msg.content)


def _convert_from_langchain_message(lc_msg) -> ChatMessage:
    """Convert a Langchain message object to our ChatMessage format."""
    if isinstance(lc_msg, HumanMessage):
        role = "user"
    elif isinstance(lc_msg, AIMessage):
        role = "assistant"
    elif isinstance(lc_msg, SystemMessage):
        role = "system"
    elif isinstance(lc_msg, ToolMessage):
        role = "tool"
    else:
        role = "assistant"

    return ChatMessage(role=role, content=lc_msg.content)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """
    Synchronous chat endpoint for backward compatibility.

    This endpoint processes messages immediately and returns results.
    For production use, prefer the async endpoint /api/chat/async
    """
    start = time.time()
    # Generate thread_id if not provided
    thread_id = req.thread_id or str(uuid.uuid4())
    logger.info(
        "POST /api/chat received",
        extra={
            "thread_id": thread_id,
            "client": request.client.host if request.client else None,
            "msg_count": len(req.messages),
        },
    )

    try:
        # Convert input messages to Langchain format
        lc_messages = [_convert_to_langchain_message(m) for m in req.messages]
        state = {"messages": lc_messages}

        # Create config with thread_id for checkpointing
        config = {"configurable": {"thread_id": thread_id}}

        # Invoke the graph with config for persistence
        result = _graph.invoke(state, config=config)

        # Convert all messages back to our format
        all_messages = result.get("messages", [])
        converted_messages = [_convert_from_langchain_message(m) for m in all_messages]

        logger.info(
            "POST /api/chat completed",
            extra={
                "thread_id": thread_id,
                "duration_ms": int((time.time() - start) * 1000),
                "response_msg_count": len(converted_messages),
            },
        )
        return ChatResponse(messages=converted_messages, thread_id=thread_id)
    except Exception as e:
        logger.exception(
            "POST /api/chat failed",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Chat processing failed")


@app.post("/api/chat/async", response_model=AsyncChatResponse)
def chat_async(
    req: ChatRequest, db: Session = Depends(get_db), request: Request = None
) -> AsyncChatResponse:
    """
    Asynchronous chat endpoint that enqueues jobs for worker processing.

    This is the preferred endpoint for production as it:
    - Returns immediately with job tracking information
    - Allows the API to remain responsive under load
    - Enables distributed processing via workers
    """
    start = time.time()
    # Generate thread_id if not provided
    thread_id = req.thread_id or str(uuid.uuid4())
    logger.info(
        "POST /api/chat/async received",
        extra={
            "thread_id": thread_id,
            "client": request.client.host if request and request.client else None,
            "msg_count": len(req.messages),
        },
    )

    # Extract user prompt from the last user message
    user_prompt = "Default chat request"
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_prompt = msg.content
            break

    try:
        # Create decision set for this conversation
        decision_set = create_decision_set_for_thread(db, thread_id, user_prompt)

        # Create job service and enqueue the job
        job_service = JobService(db)
        job = job_service.create_job(
            decision_set_id=decision_set.id,
            job_type="ml_workflow",
            payload={
                "thread_id": thread_id,
                "messages": [msg.model_dump() for msg in req.messages],
            },
        )

        logger.info(
            "Job enqueued",
            extra={
                "thread_id": thread_id,
                "decision_set_id": decision_set.id,
                "job_id": job.id,
                "duration_ms": int((time.time() - start) * 1000),
            },
        )

        return AsyncChatResponse(
            decision_set_id=decision_set.id,
            thread_id=thread_id,
            job_id=job.id,
            status=job.status.value,
        )

    except Exception as e:
        logger.exception(
            "POST /api/chat/async failed",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to create job")


@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    """
    Get the current status of a job.

    Use this endpoint to poll for job completion after using /api/chat/async
    """
    # Get the job
    logger.debug("GET /api/jobs/status", extra={"job_id": job_id})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning("Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        decision_set_id=job.decision_set_id,
        thread_id=job.decision_set.thread_id,
    )


@app.post(
    "/api/decision-sets/{decision_set_id}/approve", response_model=ApprovalResponse
)
def approve_plan(
    decision_set_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    request: Request = None,
) -> ApprovalResponse:
    """
    Approve or reject a plan and resume the workflow execution.

    This endpoint handles human-in-the-loop approval decisions by:
    - Validating the decision set exists
    - Finding the associated thread_id
    - Resuming graph execution with the approval decision
    """
    start = time.time()
    logger.info(
        f"POST /api/decision-sets/{decision_set_id}/approve received",
        extra={
            "decision_set_id": decision_set_id,
            "decision": req.decision,
            "client": request.client.host if request and request.client else None,
        },
    )

    try:
        # Find the decision set to get the thread_id
        decision_set = (
            db.query(DecisionSet).filter(DecisionSet.id == decision_set_id).first()
        )
        if not decision_set:
            logger.warning(
                "Decision set not found", extra={"decision_set_id": decision_set_id}
            )
            raise HTTPException(status_code=404, detail="Decision set not found")

        thread_id = decision_set.thread_id

        # Prepare the approval data to resume the graph
        approval_data = {
            "decision": req.decision,
            "comment": req.comment or "",
            "approved_by": req.approved_by or "anonymous",
            "timestamp": time.time(),
        }

        # Resume the graph execution with the approval decision using Command
        config = {"configurable": {"thread_id": thread_id}}

        # Use Command(resume=approval_data) to resume from interrupt
        resume_command = Command(resume=approval_data)
        result = _graph.invoke(resume_command, config=config)

        # Check if the graph execution completed successfully
        hitl_status = result.get("hitl", {})
        final_status = hitl_status.get("status", "unknown")

        logger.info(
            f"Plan approval processed: {req.decision}",
            extra={
                "decision_set_id": decision_set_id,
                "thread_id": thread_id,
                "decision": req.decision,
                "final_status": final_status,
                "duration_ms": int((time.time() - start) * 1000),
            },
        )

        return ApprovalResponse(
            success=True,
            message=f"Plan {req.decision} successfully. Workflow resumed.",
            decision_set_id=decision_set_id,
            thread_id=thread_id,
            approval_status=final_status,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.exception(
            f"POST /api/decision-sets/{decision_set_id}/approve failed",
            extra={"decision_set_id": decision_set_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to process approval: {str(e)}"
        )


@app.get("/api/streams/{decision_set_id}")
async def stream_workflow_progress(decision_set_id: str, db: Session = Depends(get_db)):
    """
    Stream real-time workflow progress and reason cards via Server-Sent Events (SSE).

    This endpoint provides live updates during MLOps workflow execution including:
    - Node start/completion events
    - Reason cards from agents
    - Error notifications
    - Heartbeat messages to keep connection alive

    Usage:
        const eventSource = new EventSource(`/api/streams/${decision_set_id}`);
        eventSource.addEventListener('reason-card', handleReasonCard);
        eventSource.addEventListener('node-complete', handleNodeComplete);
    """
    from sse_starlette.sse import EventSourceResponse
    from libs.streaming_service import get_streaming_service

    logger.info(f"SSE connection established for decision_set_id: {decision_set_id}")

    # Verify decision set exists
    decision_set = None
    retry_delay = float(os.getenv("STREAM_DECISION_SET_RETRY_DELAY", "0.2"))
    max_wait_seconds = float(os.getenv("STREAM_DECISION_SET_MAX_WAIT", "6.0"))

    loop = asyncio.get_running_loop()
    start_time = loop.time()
    attempts = 0
    while True:
        decision_set = (
            db.query(DecisionSet).filter(DecisionSet.id == decision_set_id).first()
        )
        if decision_set:
            break

        attempts += 1
        elapsed = loop.time() - start_time
        if elapsed >= max_wait_seconds:
            logger.warning(
                "Decision set not found after waiting",
                extra={
                    "decision_set_id": decision_set_id,
                    "attempts": attempts,
                    "wait_seconds": round(elapsed, 3),
                },
            )
            raise HTTPException(status_code=404, detail="Decision set not found")

        await asyncio.sleep(retry_delay)

    if attempts:
        logger.info(
            "Decision set lookup succeeded after retries",
            extra={
                "decision_set_id": decision_set_id,
                "attempts": attempts,
                "wait_seconds": round(loop.time() - start_time, 3),
            },
        )

    # Get the streaming service instance
    streaming_service = get_streaming_service()

    async def event_generator():
        """Generate streaming events for the workflow using StreamingService.

        Important: Yield dicts with explicit "event" and JSON-encoded "data" so
        sse_starlette formats named events correctly. Do NOT yield preformatted
        SSE strings here, or the middleware will wrap them as data-only messages
        and custom event listeners (e.g., 'reason-card') will never fire on the
        client.
        """
        try:
            import json as _json
            from fastapi.encoders import jsonable_encoder

            logger.info(
                f"Starting SSE event generator for decision_set_id: {decision_set_id}"
            )
            event_count = 0
            # Subscribe to the streaming service for this decision set
            async for event in streaming_service.subscribe(decision_set_id):
                event_count += 1

                # Build payload expected by the frontend hook
                payload = {
                    "type": event.event_type.value,
                    "decision_set_id": event.decision_set_id,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                }
                if event.message:
                    payload["message"] = event.message

                serialized_payload = jsonable_encoder(payload)
                out = {
                    "event": event.event_type.value,
                    "data": _json.dumps(serialized_payload),
                }
                logger.info(f"SSE yielding event #{event_count}: {event.event_type}")
                yield out

        except asyncio.CancelledError:
            logger.info(
                f"SSE connection cancelled for decision_set_id: {decision_set_id}"
            )
            raise
        except Exception as e:
            logger.exception(f"SSE stream error for decision_set_id: {decision_set_id}")
            # Try to emit an error event through the streaming service
            await streaming_service.emit_error(
                decision_set_id, f"Stream error: {str(e)}"
            )

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/streams/{decision_set_id}/emit")
async def emit_streaming_event(
    decision_set_id: str, event_data: dict, db: Session = Depends(get_db)
):
    """
    Endpoint for worker to emit streaming events to connected SSE clients.

    This allows the worker process to send events to the API server's streaming service
    so they reach the frontend SSE connections.
    """
    from libs.streaming_service import get_streaming_service
    from libs.streaming_models import create_reason_card

    streaming_service = get_streaming_service()

    try:
        event_type = event_data.get("event_type")

        if event_type == "reason_card":
            # Create and emit reason card
            reason_card = create_reason_card(
                agent=event_data.get("agent", "unknown"),
                node=event_data.get("node", "unknown"),
                decision_set_id=decision_set_id,
                reasoning=event_data.get("reasoning", ""),
                decision=event_data.get("decision", ""),
                category=event_data.get("category", "unknown"),
                confidence=event_data.get("confidence", 0.5),
                inputs=event_data.get("inputs", {}),
                outputs=event_data.get("outputs", {}),
                alternatives_considered=event_data.get("alternatives_considered", []),
                priority=event_data.get("priority", "medium"),
            )
            await streaming_service.emit_reason_card(reason_card)

        elif event_type == "node_start":
            await streaming_service.emit_node_start(
                decision_set_id,
                event_data.get("node_name", "unknown"),
                event_data.get("message", ""),
            )

        elif event_type == "node_complete":
            await streaming_service.emit_node_complete(
                decision_set_id,
                event_data.get("node_name", "unknown"),
                event_data.get("outputs", {}),
                event_data.get("message", ""),
            )

        elif event_type == "error":
            await streaming_service.emit_error(
                decision_set_id, event_data.get("message", "Unknown error")
            )

        return {"status": "success", "message": "Event emitted"}

    except Exception as e:
        logger.exception(f"Failed to emit streaming event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to emit event: {str(e)}")


@app.get("/api/workflow/plan", response_model=WorkflowPlanResponse)
def get_workflow_plan() -> WorkflowPlanResponse:
    """Return the canonical workflow execution plan for the active graph."""

    from libs.graph import get_execution_plan

    plan = get_execution_plan()
    return WorkflowPlanResponse(nodes=plan, graph_type=GRAPH_TYPE)


# ============================================================================
# INTEGRATED WORKER SERVICE
# ============================================================================


class IntegratedWorkerService:
    """
    Integrated worker service that runs in the same process as the API server.

    This provides the benefits of job persistence while eliminating the need
    for separate worker processes and HTTP-based event streaming.
    """

    def __init__(
        self, worker_id: str = None, poll_interval: int = 5, lease_duration: int = 30
    ):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval  # seconds between job polls
        self.lease_duration = lease_duration  # minutes to hold job lease
        self.running = False
        self.task = None

        # Use the same graph instance as the API server
        self.graph = _graph

        # Use the same database session maker as the API server
        self.SessionMaker = SessionMaker

        logger.info(f"Initialized integrated worker {self.worker_id}")

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

    async def start_background_worker(self):
        """Start the worker as a background asyncio task."""
        if self.running:
            logger.warning("Worker already running")
            return

        self.running = True
        self.task = asyncio.create_task(self.run_worker_loop())
        logger.info(f"Background worker {self.worker_id} started")
        return self.task

    async def stop_background_worker(self):
        """Stop the background worker gracefully."""
        self.running = False
        if self.task:
            try:
                await asyncio.wait_for(self.task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Worker shutdown timed out, cancelling task")
                self.task.cancel()
            except Exception as e:
                logger.error(f"Error stopping worker: {e}")
        logger.info(f"Background worker {self.worker_id} stopped")

    async def run_worker_loop(self):
        """Main worker loop that polls for and processes jobs."""
        consecutive_empty_polls = 0
        max_empty_polls = 12  # Max empty polls before backing off
        backoff_multiplier = 2
        max_backoff = 60  # Maximum backoff in seconds

        logger.info(f"Worker {self.worker_id} loop started")

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

        logger.info(f"Worker {self.worker_id} loop completed")

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
        """Process a specific job based on its type."""
        logger.info(f"Processing job {job.id} of type {job.job_type}")

        if job.job_type == "ml_workflow":
            await self.process_ml_workflow_job(job)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    async def process_ml_workflow_job(self, job: Job):
        """Process an ML workflow job by running the LangGraph."""
        payload = job.payload
        thread_id = payload.get("thread_id")
        messages = payload.get("messages", [])

        # Use decision_set_id for streaming events (this is what frontend SSE uses)
        decision_set_id = job.decision_set_id

        # Generate run_id for correlation in logs and LangSmith (Issue #16)
        run_id = str(uuid.uuid4())

        if not thread_id:
            raise ValueError("Job payload missing required thread_id")

        # Structured logging with run_id and thread_id for CloudWatch correlation (Issue #16)
        logger.info(
            f"Processing ML workflow for thread {thread_id}, decision_set {decision_set_id}",
            extra={"run_id": run_id, "thread_id": thread_id, "decision_set_id": decision_set_id, "job_id": job.id}
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

        state = {"messages": lc_messages, "decision_set_id": decision_set_id}

        # Configure LangGraph with run_id for LangSmith tracing (Issue #16)
        config = {
            "configurable": {
                "thread_id": thread_id,
                # Add run_id for LangSmith trace correlation
                "run_id": run_id,
            }
        }

        # Execute the graph with streaming
        # Use direct streaming service access (no HTTP bridge needed)
        from libs.streaming_service import get_streaming_service

        streaming_service = get_streaming_service()

        try:
            # Use enhanced multi-mode streaming for richer agent reasoning data
            # Following LangGraph best practices: combine "updates" and "messages" modes
            stream_modes = ["updates", "messages"]
            logger.info(
                f"Starting LangGraph multi-mode streaming for thread {thread_id}, modes: {stream_modes}, emitting events to decision_set {decision_set_id}",
                extra={"run_id": run_id, "thread_id": thread_id, "decision_set_id": decision_set_id, "stream_modes": stream_modes}
            )

            async for stream_mode, chunk in self.graph.astream(
                state, config, stream_mode=stream_modes
            ):
                # Process different stream modes for comprehensive agent insights
                logger.info(
                    f"Received {stream_mode} stream chunk: {type(chunk)} keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'not-dict'}"
                )
                await self._process_multi_mode_chunk(
                    stream_mode, chunk, decision_set_id, streaming_service
                )
            logger.info(
                f"LangGraph multi-mode streaming completed for thread {thread_id}",
                extra={"run_id": run_id, "thread_id": thread_id, "decision_set_id": decision_set_id}
            )
        except Exception as stream_error:
            logger.error(
                f"Streaming execution failed: {stream_error}",
                extra={"run_id": run_id, "thread_id": thread_id, "decision_set_id": decision_set_id, "error": str(stream_error)}
            )
            await streaming_service.emit_error(
                decision_set_id, f"Workflow execution failed: {str(stream_error)}"
            )
            raise

        # Log the result for now
        # In the future, this would save results to decision_set, create artifacts, etc.
        logger.info(
            f"Graph execution completed for job {job.id}",
            extra={"run_id": run_id, "thread_id": thread_id, "decision_set_id": decision_set_id, "job_id": job.id}
        )

        # For now, we'll simulate some processing time
        await asyncio.sleep(2)

    async def _process_stream_chunk(
        self, chunk, decision_set_id: str, streaming_service
    ):
        """
        Process a single stream chunk from LangGraph and emit appropriate SSE events.

        Args:
            chunk: Stream chunk from LangGraph (contains node updates)
            decision_set_id: Decision set ID for routing SSE events
            streaming_service: Direct streaming service instance (no HTTP needed)
        """
        try:
            logger.debug(f"Processing stream chunk: {chunk}")

            # chunk format: {node_name: node_state_update}
            for node_name, node_update in chunk.items():
                logger.info(f"Node update: {node_name} -> {node_update}")

                # Look for reason cards in the node state
                if hasattr(node_update, "reason_cards") and node_update.reason_cards:
                    # Deduplicate reason cards based on content
                    unique_reason_cards = self._deduplicate_reason_cards(
                        node_update.reason_cards
                    )
                    logger.info(
                        f"Found {len(node_update.reason_cards)} reason cards, {len(unique_reason_cards)} unique after deduplication"
                    )
                    for reason_card in unique_reason_cards:
                        await streaming_service.emit_reason_card(reason_card)

                # Look for reason cards in nested state structures
                elif isinstance(node_update, dict):
                    reason_cards = node_update.get("reason_cards", [])
                    logger.info(
                        f"Found {len(reason_cards)} reason cards in dict structure"
                    )

                    # Deduplicate reason cards before processing
                    unique_reason_cards = self._deduplicate_reason_cards(reason_cards)
                    logger.info(
                        f"After deduplication: {len(unique_reason_cards)} unique reason cards"
                    )

                    for i, reason_card in enumerate(unique_reason_cards):
                        logger.info(
                            f"Processing unique reason card {i + 1}: type={type(reason_card)}, has_model_dump={hasattr(reason_card, 'model_dump')}"
                        )
                        if hasattr(reason_card, "model_dump"):  # Pydantic model
                            # Emit reason card directly via streaming service
                            await streaming_service.emit_reason_card(reason_card)
                        elif isinstance(
                            reason_card, dict
                        ):  # Dictionary-based reason card
                            logger.info(
                                f"Emitting dict-based reason card: {reason_card.get('agent', 'unknown')}"
                            )
                            # Normalize dictionaries produced by .model_dump()
                            from pydantic import ValidationError
                            from libs.streaming_models import (
                                ReasonCard,
                                create_reason_card,
                            )

                            try:
                                reason_card_obj = ReasonCard.model_validate(reason_card)
                                normalized_node = (
                                    reason_card_obj.node
                                    or reason_card.get("node")
                                    or reason_card.get("node_name")
                                    or node_name
                                )
                                if reason_card_obj.decision_set_id in (
                                    None,
                                    "",
                                    "unknown",
                                ):
                                    reason_card_obj = reason_card_obj.model_copy(
                                        update={"decision_set_id": decision_set_id}
                                    )
                                if normalized_node and reason_card_obj.node != normalized_node:
                                    reason_card_obj = reason_card_obj.model_copy(
                                        update={"node": normalized_node}
                                    )
                            except ValidationError as validation_error:
                                logger.debug(
                                    "Reason card dict validation failed: %s",
                                    validation_error,
                                )
                                normalized_node = (
                                    reason_card.get("node")
                                    or reason_card.get("node_name")
                                    or node_name
                                )
                                reason_card_obj = create_reason_card(
                                    agent=reason_card.get(
                                        "agent", normalized_node or "unknown"
                                    ),
                                    node=normalized_node,
                                    decision_set_id=reason_card.get(
                                        "decision_set_id", decision_set_id
                                    ),
                                    reasoning=
                                        reason_card.get("reasoning")
                                        or reason_card.get("outputs", {}).get(
                                            "extraction_rationale",
                                            "No rationale provided",
                                        ),
                                    decision=
                                        reason_card.get("decision")
                                        or reason_card.get("message")
                                        or f"Completed {normalized_node}",
                                    category=reason_card.get(
                                        "category", "constraint_extraction"
                                    ),
                                    confidence=reason_card.get("confidence"),
                                    inputs=reason_card.get("inputs", {}),
                                    outputs=reason_card.get("outputs", {}),
                                    alternatives_considered=reason_card.get(
                                        "alternatives_considered", []
                                    ),
                                    priority=reason_card.get("priority", "medium"),
                                )

                            if reason_card_obj.decision_set_id in (
                                None,
                                "",
                                "unknown",
                            ):
                                reason_card_obj = reason_card_obj.model_copy(
                                    update={"decision_set_id": decision_set_id}
                                )

                            await streaming_service.emit_reason_card(reason_card_obj)
                        else:
                            logger.warning(
                                f"Unknown reason card type: {type(reason_card)}, skipping"
                            )

                # Emit node completion
                await streaming_service.emit_node_complete(
                    decision_set_id, node_name, {}, f"Completed {node_name}"
                )

        except Exception as e:
            logger.error(f"Error processing stream chunk: {e}")
            await streaming_service.emit_error(
                decision_set_id, f"Stream processing error: {str(e)}"
            )

    def _deduplicate_reason_cards(self, reason_cards):
        """
        Deduplicate reason cards based on their key content to prevent identical cards.

        Args:
            reason_cards: List of reason card objects or dictionaries

        Returns:
            List of unique reason cards
        """
        if not reason_cards:
            return []

        seen_cards = set()
        unique_cards = []

        for card in reason_cards:
            # Create a hash key based on the card's content
            if hasattr(card, "model_dump"):  # Pydantic model
                # Use key fields to create a unique identifier
                key = (
                    card.agent,
                    card.node_name,
                    card.trigger,
                    str(card.inputs),
                    str(card.outputs),
                    card.confidence,
                )
            elif isinstance(card, dict):  # Dictionary-based reason card
                # Use key fields to create a unique identifier
                key = (
                    card.get("agent", ""),
                    card.get("node_name", ""),
                    card.get("trigger", ""),
                    str(card.get("inputs", {})),
                    str(card.get("outputs", {})),
                    card.get("confidence", 0),
                )
            else:
                # Fallback: convert to string
                key = str(card)

            if key not in seen_cards:
                seen_cards.add(key)
                unique_cards.append(card)
            else:
                logger.info(f"Skipping duplicate reason card with key: {key[:100]}...")

        return unique_cards

    async def _process_multi_mode_chunk(
        self, stream_mode: str, chunk, decision_set_id: str, streaming_service
    ):
        """
        Process LangGraph multi-mode stream chunks for enhanced agent reasoning.

        Args:
            stream_mode: The streaming mode ("updates", "messages", etc.)
            chunk: Stream chunk data specific to the mode
            decision_set_id: Decision set ID for routing SSE events
            streaming_service: Direct streaming service instance
        """
        try:
            logger.debug(f"Processing {stream_mode} stream chunk: {chunk}")

            if stream_mode == "updates":
                # Process node state updates (contains reason cards and node execution info)
                await self._process_stream_chunk(
                    chunk, decision_set_id, streaming_service
                )

            elif stream_mode == "messages":
                # Process LLM message streams (contains token-level reasoning)
                await self._process_message_chunk(
                    chunk, decision_set_id, streaming_service
                )

            else:
                logger.debug(f"Unhandled stream mode: {stream_mode}")

        except Exception as e:
            logger.error(f"Error processing {stream_mode} stream chunk: {e}")
            await streaming_service.emit_error(
                decision_set_id,
                f"Stream processing error in {stream_mode} mode: {str(e)}",
            )

    async def _process_message_chunk(
        self, chunk, decision_set_id: str, streaming_service
    ):
        """
        Process LLM message chunks for token-level reasoning insights.

        Args:
            chunk: Message chunk from LangGraph message streaming
            decision_set_id: Decision set ID for routing SSE events
            streaming_service: Direct streaming service instance
        """
        try:
            # Message chunks provide token-level LLM reasoning
            # These can be used for real-time thinking displays

            if isinstance(chunk, dict):
                # Extract message metadata for live reasoning display
                message_data = {
                    "type": "llm_reasoning",
                    "timestamp": chunk.get("timestamp"),
                    "content": chunk.get("content", ""),
                    "tokens": chunk.get("tokens", 0),
                    "model": chunk.get("model", "unknown"),
                }

                # Emit as a generic stream event for advanced UIs
                from libs.streaming_models import StreamEvent, StreamEventType

                event = StreamEvent(
                    event_type=StreamEventType.NODE_START,  # Reuse for now
                    decision_set_id=decision_set_id,
                    data=message_data,
                    message=f"LLM reasoning: {message_data['content'][:100]}...",
                )
                await streaming_service.emit_event(event)

        except Exception as e:
            logger.error(f"Error processing message chunk: {e}")


# Global worker instance
_worker_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize and start the integrated worker service on API startup."""
    global _worker_service

    logger.info("Starting integrated API + Worker server")

    # Initialize and start the integrated worker
    _worker_service = IntegratedWorkerService()
    await _worker_service.start_background_worker()

    logger.info("Integrated API + Worker server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown the integrated worker service on API shutdown."""
    global _worker_service

    logger.info("Shutting down integrated API + Worker server")

    if _worker_service:
        await _worker_service.stop_background_worker()

    logger.info("Integrated API + Worker server shutdown complete")
