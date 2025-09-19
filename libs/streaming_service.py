"""
Streaming service for managing real-time workflow events.

This service provides functionality to store, retrieve, and broadcast
streaming events during MLOps workflow execution.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from libs.streaming_models import StreamEvent, StreamEventType, ReasonCard

logger = logging.getLogger(__name__)


class StreamingService:
    """
    Service for managing real-time streaming events during workflow execution.

    This service handles:
    - Storing streaming events in memory/database
    - Broadcasting events to connected clients
    - Managing SSE connections
    - Cleanup of expired events
    """

    def __init__(self):
        # In-memory event storage (in production, use Redis or database)
        self._events: Dict[str, List[StreamEvent]] = {}
        self._connections: Dict[str, List[asyncio.Queue]] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def emit_event(self, event: StreamEvent) -> None:
        """
        Emit a streaming event to all connected clients for a decision set.

        Args:
            event: The StreamEvent to emit
        """
        decision_set_id = event.decision_set_id

        # Store event in memory
        if decision_set_id not in self._events:
            self._events[decision_set_id] = []
        self._events[decision_set_id].append(event)

        # Limit event history to prevent memory growth
        if len(self._events[decision_set_id]) > 1000:
            self._events[decision_set_id] = self._events[decision_set_id][-500:]

        # Broadcast to connected clients
        await self._broadcast_event(decision_set_id, event)

        logger.info(
            f"Emitted {event.event_type} event for decision_set: {decision_set_id}, connections: {len(self._connections.get(decision_set_id, []))}"
        )

    async def emit_reason_card(self, reason_card: ReasonCard) -> None:
        """
        Emit a reason card as a streaming event.

        Args:
            reason_card: The ReasonCard to emit
        """
        event = StreamEvent(
            event_type=StreamEventType.REASON_CARD,
            decision_set_id=reason_card.decision_set_id,
            data=reason_card.model_dump(mode="json"),
            message=f"{reason_card.agent}: {reason_card.decision}",
        )
        await self.emit_event(event)

    async def emit_node_start(
        self, decision_set_id: str, node_name: str, message: Optional[str] = None
    ) -> None:
        """Emit a node start event."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_START,
            decision_set_id=decision_set_id,
            data={"node": node_name},
            message=message or f"Starting {node_name}",
        )
        await self.emit_event(event)

    async def emit_node_complete(
        self,
        decision_set_id: str,
        node_name: str,
        outputs: Optional[Dict] = None,
        message: Optional[str] = None,
    ) -> None:
        """Emit a node completion event."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_COMPLETE,
            decision_set_id=decision_set_id,
            data={"node": node_name, "outputs": outputs or {}},
            message=message or f"Completed {node_name}",
        )
        await self.emit_event(event)

    async def emit_error(
        self, decision_set_id: str, error_message: str, node_name: Optional[str] = None
    ) -> None:
        """Emit an error event."""
        event = StreamEvent(
            event_type=StreamEventType.ERROR,
            decision_set_id=decision_set_id,
            data={"node": node_name, "error": error_message},
            message=error_message,
        )
        await self.emit_event(event)

    async def emit_workflow_paused(
        self, decision_set_id: str, reason: str, node_name: Optional[str] = None
    ) -> None:
        """Emit a workflow paused event."""
        event = StreamEvent(
            event_type=StreamEventType.WORKFLOW_PAUSED,
            decision_set_id=decision_set_id,
            data={"node": node_name, "reason": reason},
            message=f"Workflow paused: {reason}",
        )
        await self.emit_event(event)

    async def emit_questions_presented(
        self,
        decision_set_id: str,
        questions: List[Dict],
        smart_defaults: Dict[str, str],
        timeout_seconds: int,
        node_name: Optional[str] = None,
    ) -> None:
        """Emit a questions presented event for HITL interaction."""
        event = StreamEvent(
            event_type=StreamEventType.QUESTIONS_PRESENTED,
            decision_set_id=decision_set_id,
            data={
                "node": node_name,
                "questions": questions,
                "smart_defaults": smart_defaults,
                "timeout_seconds": timeout_seconds,
                "questions_count": len(questions),
            },
            message=f"Presented {len(questions)} questions with {timeout_seconds}s timeout",
        )
        await self.emit_event(event)

    async def emit_auto_approving(
        self,
        decision_set_id: str,
        remaining_seconds: int,
        smart_defaults: Dict[str, str],
        node_name: Optional[str] = None,
    ) -> None:
        """Emit an auto-approval countdown event."""
        event = StreamEvent(
            event_type=StreamEventType.AUTO_APPROVING,
            decision_set_id=decision_set_id,
            data={
                "node": node_name,
                "remaining_seconds": remaining_seconds,
                "smart_defaults": smart_defaults,
            },
            message=f"Auto-approving in {remaining_seconds} seconds",
        )
        await self.emit_event(event)

    async def emit_countdown_tick(
        self,
        decision_set_id: str,
        remaining_seconds: int,
        node_name: Optional[str] = None,
    ) -> None:
        """Emit a countdown tick for real-time timer updates."""
        event = StreamEvent(
            event_type=StreamEventType.COUNTDOWN_TICK,
            decision_set_id=decision_set_id,
            data={"node": node_name, "remaining_seconds": remaining_seconds},
            message=f"{remaining_seconds}s remaining",
        )
        await self.emit_event(event)

    async def emit_responses_collected(
        self,
        decision_set_id: str,
        responses: List[Dict],
        approval_method: str,
        node_name: Optional[str] = None,
    ) -> None:
        """Emit a responses collected event."""
        event = StreamEvent(
            event_type=StreamEventType.RESPONSES_COLLECTED,
            decision_set_id=decision_set_id,
            data={
                "node": node_name,
                "responses": responses,
                "approval_method": approval_method,
                "responses_count": len(responses),
            },
            message=f"Collected {len(responses)} responses via {approval_method}",
        )
        await self.emit_event(event)

    async def emit_workflow_resumed(
        self, decision_set_id: str, next_node: str, node_name: Optional[str] = None
    ) -> None:
        """Emit a workflow resumed event after HITL interaction."""
        event = StreamEvent(
            event_type=StreamEventType.WORKFLOW_RESUMED,
            decision_set_id=decision_set_id,
            data={"node": node_name, "next_node": next_node},
            message=f"Workflow resumed, continuing to {next_node}",
        )
        await self.emit_event(event)

    async def subscribe(
        self, decision_set_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Subscribe to streaming events for a decision set.

        Args:
            decision_set_id: The decision set ID to subscribe to

        Yields:
            StreamEvent: Stream events as they occur
        """
        # Create a queue for this connection
        connection_queue = asyncio.Queue()

        # Register the connection
        if decision_set_id not in self._connections:
            self._connections[decision_set_id] = []
        self._connections[decision_set_id].append(connection_queue)

        try:
            # Send historical events first
            historical_events = self._events.get(decision_set_id, [])
            logger.info(
                f"SSE connection for {decision_set_id}: Found {len(historical_events)} historical events, sending last 50"
            )

            historical_to_send = (
                historical_events[-50:]
                if len(historical_events) > 50
                else historical_events
            )
            for i, event in enumerate(historical_to_send):
                logger.info(
                    f"SSE sending historical event {i + 1}/{len(historical_to_send)}: {event.event_type} at {event.timestamp}"
                )
                yield event

            # Send ongoing events
            while True:
                try:
                    event = await asyncio.wait_for(connection_queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat
                    heartbeat = StreamEvent(
                        event_type=StreamEventType.HEARTBEAT,
                        decision_set_id=decision_set_id,
                        data={"timestamp": datetime.now(timezone.utc).isoformat()},
                    )
                    yield heartbeat

        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for decision_set: {decision_set_id}")
            raise
        finally:
            # Clean up connection
            if decision_set_id in self._connections:
                try:
                    self._connections[decision_set_id].remove(connection_queue)
                    if not self._connections[decision_set_id]:
                        del self._connections[decision_set_id]
                except ValueError:
                    pass  # Connection already removed

    async def _broadcast_event(self, decision_set_id: str, event: StreamEvent) -> None:
        """
        Broadcast an event to all connected clients for a decision set.

        Args:
            decision_set_id: The decision set ID
            event: The event to broadcast
        """
        connections = self._connections.get(decision_set_id, [])
        if not connections:
            return

        # Send event to all connections
        for (
            connection_queue
        ) in connections.copy():  # Copy to avoid modification during iteration
            try:
                connection_queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    f"Connection queue full for decision_set: {decision_set_id}"
                )
                # Remove slow/disconnected client
                try:
                    self._connections[decision_set_id].remove(connection_queue)
                except (ValueError, KeyError):
                    pass

    def get_events(self, decision_set_id: str, limit: int = 100) -> List[StreamEvent]:
        """
        Get historical events for a decision set.

        Args:
            decision_set_id: The decision set ID
            limit: Maximum number of events to return

        Returns:
            List of StreamEvent objects
        """
        events = self._events.get(decision_set_id, [])
        return events[-limit:] if limit else events

    def get_event_count(self, decision_set_id: str) -> int:
        """
        Get the number of events for a decision set.

        Args:
            decision_set_id: The decision set ID

        Returns:
            Number of events
        """
        return len(self._events.get(decision_set_id, []))

    def cleanup_events(self, decision_set_id: str) -> None:
        """
        Clean up events for a decision set (call when workflow is complete).

        Args:
            decision_set_id: The decision set ID to clean up
        """
        if decision_set_id in self._events:
            del self._events[decision_set_id]

        if decision_set_id in self._connections:
            # Close all connections
            for connection_queue in self._connections[decision_set_id]:
                try:
                    connection_queue.put_nowait(
                        StreamEvent(
                            event_type=StreamEventType.WORKFLOW_COMPLETE,
                            decision_set_id=decision_set_id,
                            message="Workflow completed, closing connection",
                        )
                    )
                except asyncio.QueueFull:
                    pass
            del self._connections[decision_set_id]

        logger.info(f"Cleaned up events for decision_set: {decision_set_id}")

    async def get_connection_count(self, decision_set_id: str) -> int:
        """
        Get the number of active connections for a decision set.

        Args:
            decision_set_id: The decision set ID

        Returns:
            Number of active connections
        """
        return len(self._connections.get(decision_set_id, []))

    def get_all_active_streams(self) -> Dict[str, int]:
        """
        Get information about all active streaming sessions.

        Returns:
            Dict mapping decision_set_id to connection count
        """
        return {
            decision_set_id: len(connections)
            for decision_set_id, connections in self._connections.items()
        }


# Global streaming service instance
_streaming_service = None


def get_streaming_service() -> StreamingService:
    """Get the global streaming service instance."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service
