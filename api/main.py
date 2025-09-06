from __future__ import annotations

import os
import uuid
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session

from libs.graph import build_thin_graph
from libs.job_service import JobService, create_decision_set_for_thread
from libs.database import create_database_engine, create_session_maker
from libs.models import JobStatus, Job

app = FastAPI()

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
def chat(req: ChatRequest) -> ChatResponse:
    """
    Synchronous chat endpoint for backward compatibility.

    This endpoint processes messages immediately and returns results.
    For production use, prefer the async endpoint /api/chat/async
    """
    # Generate thread_id if not provided
    thread_id = req.thread_id or str(uuid.uuid4())

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

    return ChatResponse(messages=converted_messages, thread_id=thread_id)


@app.post("/api/chat/async", response_model=AsyncChatResponse)
def chat_async(req: ChatRequest, db: Session = Depends(get_db)) -> AsyncChatResponse:
    """
    Asynchronous chat endpoint that enqueues jobs for worker processing.

    This is the preferred endpoint for production as it:
    - Returns immediately with job tracking information
    - Allows the API to remain responsive under load
    - Enables distributed processing via workers
    """
    # Generate thread_id if not provided
    thread_id = req.thread_id or str(uuid.uuid4())

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

        return AsyncChatResponse(
            decision_set_id=decision_set.id,
            thread_id=thread_id,
            job_id=job.id,
            status=job.status.value,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    """
    Get the current status of a job.

    Use this endpoint to poll for job completion after using /api/chat/async
    """
    # Get the job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        decision_set_id=job.decision_set_id,
        thread_id=job.decision_set.thread_id,
    )
