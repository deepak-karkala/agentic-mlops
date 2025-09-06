from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.pregel import Pregel
from langchain_core.messages import AIMessage, HumanMessage

from libs.database import create_appropriate_checkpointer


class ChatMessage(TypedDict):
    """Simplified message format for API serialization."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str


def call_llm(state: MessagesState) -> MessagesState:
    """
    Thin-slice node: returns a deterministic assistant reply without
    calling external providers (offline-friendly for CI).

    Args:
        state: The current graph state containing messages

    Returns:
        Updated state with new assistant message
    """
    messages = state.get("messages", [])

    # Find the last user message content to echo back
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if last_user_msg:
        reply = f"You said: {last_user_msg}. Thin slice online."
    else:
        reply = "Thin slice online."

    return {"messages": [AIMessage(content=reply)]}


def build_thin_graph() -> Pregel:
    """
    Build and compile the minimal deterministic LangGraph graph with checkpointing.

    This creates a simple linear graph with a single node that processes
    user messages and returns deterministic responses. It includes PostgreSQL
    checkpointing for durable state when available.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MessagesState)

    # Add the single processing node
    graph.add_node("call_llm", call_llm)

    # Define the execution flow: START -> call_llm -> END
    graph.add_edge(START, "call_llm")
    graph.add_edge("call_llm", END)

    # Create appropriate checkpointer based on environment
    checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()
