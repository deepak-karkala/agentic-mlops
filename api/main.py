from __future__ import annotations

import os
import uuid
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session
import logging
import time

from libs.graph import build_full_graph, build_thin_graph
from libs.job_service import JobService, create_decision_set_for_thread
from libs.database import create_database_engine, create_session_maker
from libs.models import JobStatus, Job, DecisionSet
from langgraph.types import Command

app = FastAPI()

# Configure logging (API)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

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


# Select graph based on env flag, with safe fallback
USE_FULL_GRAPH = os.getenv("USE_FULL_GRAPH", "false").lower() in {"1", "true", "yes"}
try:
    if USE_FULL_GRAPH:
        logger.info("Initializing full graph (USE_FULL_GRAPH=true)")
        _graph = build_full_graph()
    else:
        logger.info("Initializing thin graph (default)")
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
