from __future__ import annotations

import os
from typing import List, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from libs.graph import build_thin_graph

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


class ChatResponse(BaseModel):
    messages: List[ChatMessage]


_graph = build_thin_graph()


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
    """Invoke the thin-slice LangGraph with provided messages."""
    # Convert input messages to Langchain format
    lc_messages = [_convert_to_langchain_message(m) for m in req.messages]
    state = {"messages": lc_messages}

    # Invoke the graph
    result = _graph.invoke(state)

    # Convert all messages back to our format
    all_messages = result.get("messages", [])
    converted_messages = [_convert_from_langchain_message(m) for m in all_messages]

    return ChatResponse(messages=converted_messages)
