"""
Streaming models and utilities for real-time MLOps workflow updates.

This module defines the data structures and utilities for streaming reason cards
and workflow progress updates via Server-Sent Events (SSE).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class StreamEventType(str, Enum):
    """Types of streaming events that can be emitted during workflow execution."""
    
    REASON_CARD = "reason-card"
    NODE_START = "node-start"
    NODE_COMPLETE = "node-complete"
    WORKFLOW_START = "workflow-start"
    WORKFLOW_COMPLETE = "workflow-complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    WORKFLOW_PAUSED = "workflow-paused"  # For HITL gates


class ReasonCard(BaseModel):
    """
    Structured rationale card emitted by agents during execution.
    
    Represents a single decision or reasoning step in the MLOps workflow,
    providing transparency into the agent's thinking process.
    """
    
    # Identification
    agent: str = Field(description="Name/ID of the agent that generated this card")
    node: str = Field(description="Graph node name where this reasoning occurred")
    decision_set_id: str = Field(description="ID of the decision set this card belongs to")
    
    # Timing
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = Field(None, description="Time taken for this reasoning step in milliseconds")
    
    # Reasoning content
    reasoning: str = Field(description="Human-readable explanation of the agent's reasoning")
    decision: str = Field(description="The key decision or conclusion reached")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level (0-1)")
    
    # Supporting data
    inputs: Optional[Dict[str, Any]] = Field(None, description="Key inputs that influenced this decision")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Structured outputs or results")
    alternatives_considered: Optional[list[str]] = Field(None, description="Alternative options that were evaluated")
    
    # Categorization
    category: str = Field(description="Category of reasoning (e.g., 'cost-analysis', 'technology-selection')")
    priority: str = Field(default="medium", description="Priority level (low/medium/high/critical)")
    
    # References
    references: Optional[list[str]] = Field(None, description="References to external resources or policies")
    
    def to_sse_data(self) -> Dict[str, Any]:
        """Convert ReasonCard to SSE-compatible data format."""
        return {
            "type": StreamEventType.REASON_CARD,
            "data": self.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat()
        }


class StreamEvent(BaseModel):
    """Generic streaming event wrapper for all types of workflow updates."""
    
    event_type: StreamEventType
    decision_set_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    
    def to_sse_format(self) -> str:
        """Format event for Server-Sent Events transmission."""
        import json
        
        event_data = {
            "type": self.event_type.value,  # Use .value to get the string
            "decision_set_id": self.decision_set_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
        
        if self.message:
            event_data["message"] = self.message
        
        return f"event: {self.event_type.value}\ndata: {json.dumps(event_data)}\n\n"


class WorkflowProgress(BaseModel):
    """Represents the current progress of a workflow execution."""
    
    decision_set_id: str
    current_node: Optional[str] = None
    nodes_completed: list[str] = Field(default_factory=list)
    nodes_remaining: list[str] = Field(default_factory=list)
    total_nodes: int = 0
    progress_percentage: float = Field(ge=0.0, le=100.0)
    status: str = Field(description="Current workflow status")
    estimated_time_remaining_ms: Optional[int] = None
    
    def to_stream_event(self) -> StreamEvent:
        """Convert to StreamEvent for transmission."""
        return StreamEvent(
            event_type=StreamEventType.NODE_COMPLETE if self.current_node else StreamEventType.WORKFLOW_START,
            decision_set_id=self.decision_set_id,
            data={
                "current_node": self.current_node,
                "nodes_completed": self.nodes_completed,
                "nodes_remaining": self.nodes_remaining,
                "progress_percentage": self.progress_percentage,
                "status": self.status,
                "estimated_time_remaining_ms": self.estimated_time_remaining_ms
            }
        )


class StreamWriter:
    """
    Utility class for emitting streaming events during graph execution.
    
    This class provides a simple interface for nodes to emit reason cards
    and other streaming updates during workflow execution.
    """
    
    def __init__(self, decision_set_id: str):
        self.decision_set_id = decision_set_id
        self._events: list[StreamEvent] = []
        self._start_time = datetime.now(timezone.utc)
    
    def emit_reason_card(self, reason_card: ReasonCard) -> None:
        """Emit a reason card event."""
        # Ensure the reason card has the correct decision_set_id
        reason_card.decision_set_id = self.decision_set_id
        
        event = StreamEvent(
            event_type=StreamEventType.REASON_CARD,
            decision_set_id=self.decision_set_id,
            data=reason_card.model_dump(mode="json")
        )
        self._events.append(event)
    
    def emit_node_start(self, node_name: str, message: Optional[str] = None) -> None:
        """Emit a node start event."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_START,
            decision_set_id=self.decision_set_id,
            data={"node": node_name},
            message=message or f"Starting {node_name}"
        )
        self._events.append(event)
    
    def emit_node_complete(self, node_name: str, outputs: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> None:
        """Emit a node completion event."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_COMPLETE,
            decision_set_id=self.decision_set_id,
            data={"node": node_name, "outputs": outputs or {}},
            message=message or f"Completed {node_name}"
        )
        self._events.append(event)
    
    def emit_error(self, error_message: str, node_name: Optional[str] = None) -> None:
        """Emit an error event."""
        event = StreamEvent(
            event_type=StreamEventType.ERROR,
            decision_set_id=self.decision_set_id,
            data={"node": node_name, "error": error_message},
            message=error_message
        )
        self._events.append(event)
    
    def emit_workflow_paused(self, reason: str, node_name: Optional[str] = None) -> None:
        """Emit a workflow paused event (e.g., for HITL gates)."""
        event = StreamEvent(
            event_type=StreamEventType.WORKFLOW_PAUSED,
            decision_set_id=self.decision_set_id,
            data={"node": node_name, "reason": reason},
            message=f"Workflow paused: {reason}"
        )
        self._events.append(event)
    
    def emit_heartbeat(self) -> None:
        """Emit a heartbeat event to keep connections alive."""
        current_time = datetime.now(timezone.utc)
        elapsed_ms = int((current_time - self._start_time).total_seconds() * 1000)
        
        event = StreamEvent(
            event_type=StreamEventType.HEARTBEAT,
            decision_set_id=self.decision_set_id,
            data={"elapsed_ms": elapsed_ms}
        )
        self._events.append(event)
    
    def get_events(self) -> list[StreamEvent]:
        """Get all emitted events."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all stored events."""
        self._events.clear()


def create_reason_card(
    agent: str,
    node: str,
    decision_set_id: str,
    reasoning: str,
    decision: str,
    category: str = "general",
    confidence: Optional[float] = None,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    alternatives_considered: Optional[list[str]] = None,
    priority: str = "medium"
) -> ReasonCard:
    """
    Convenience function for creating reason cards.
    
    Args:
        agent: Name/ID of the agent creating the card
        node: Graph node name
        decision_set_id: ID of the decision set
        reasoning: Human-readable explanation of reasoning
        decision: The key decision reached
        category: Category of reasoning
        confidence: Confidence level (0-1)
        inputs: Key inputs that influenced the decision
        outputs: Structured outputs or results
        alternatives_considered: Alternative options evaluated
        priority: Priority level
        
    Returns:
        ReasonCard: Configured reason card ready for emission
    """
    return ReasonCard(
        agent=agent,
        node=node,
        decision_set_id=decision_set_id,
        reasoning=reasoning,
        decision=decision,
        category=category,
        confidence=confidence,
        inputs=inputs,
        outputs=outputs,
        alternatives_considered=alternatives_considered,
        priority=priority
    )