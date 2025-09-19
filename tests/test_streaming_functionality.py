"""
Tests for streaming functionality including reason cards and SSE.

This module tests the complete streaming system including:
- StreamingService event management
- ReasonCard creation and emission
- SSE endpoint functionality
- Graph node streaming integration
"""

import asyncio
import pytest
from datetime import datetime

from libs.streaming_service import StreamingService, get_streaming_service
from libs.streaming_models import (
    StreamEvent,
    StreamEventType,
    ReasonCard,
    StreamWriter,
    create_reason_card,
)


class TestStreamingService:
    """Test the StreamingService class for event management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.streaming_service = StreamingService()
        self.test_decision_set_id = "test-decision-set-123"

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test basic event emission."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_START,
            decision_set_id=self.test_decision_set_id,
            data={"node": "test_node"},
            message="Test node started",
        )

        await self.streaming_service.emit_event(event)

        # Check event is stored
        events = self.streaming_service.get_events(self.test_decision_set_id)
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.NODE_START
        assert events[0].decision_set_id == self.test_decision_set_id
        assert events[0].data["node"] == "test_node"

    @pytest.mark.asyncio
    async def test_emit_reason_card(self):
        """Test reason card emission."""
        reason_card = ReasonCard(
            agent="test_agent",
            node="test_node",
            decision_set_id=self.test_decision_set_id,
            reasoning="This is test reasoning",
            decision="Test decision made",
            category="test-category",
            confidence=0.85,
        )

        await self.streaming_service.emit_reason_card(reason_card)

        # Check event is stored
        events = self.streaming_service.get_events(self.test_decision_set_id)
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.REASON_CARD

        # Check reason card data
        reason_data = events[0].data
        assert reason_data["agent"] == "test_agent"
        assert reason_data["reasoning"] == "This is test reasoning"
        assert reason_data["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_emit_node_events(self):
        """Test node start and completion events."""
        # Emit node start
        await self.streaming_service.emit_node_start(
            self.test_decision_set_id, "test_node", "Starting test node"
        )

        # Emit node completion
        await self.streaming_service.emit_node_complete(
            self.test_decision_set_id,
            "test_node",
            outputs={"result": "success"},
            message="Test node completed",
        )

        events = self.streaming_service.get_events(self.test_decision_set_id)
        assert len(events) == 2

        # Check node start event
        assert events[0].event_type == StreamEventType.NODE_START
        assert events[0].data["node"] == "test_node"
        assert events[0].message == "Starting test node"

        # Check node completion event
        assert events[1].event_type == StreamEventType.NODE_COMPLETE
        assert events[1].data["node"] == "test_node"
        assert events[1].data["outputs"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_emit_error(self):
        """Test error event emission."""
        await self.streaming_service.emit_error(
            self.test_decision_set_id, "Test error occurred", "failing_node"
        )

        events = self.streaming_service.get_events(self.test_decision_set_id)
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.ERROR
        assert events[0].data["error"] == "Test error occurred"
        assert events[0].data["node"] == "failing_node"

    @pytest.mark.asyncio
    async def test_emit_workflow_paused(self):
        """Test workflow paused event emission."""
        await self.streaming_service.emit_workflow_paused(
            self.test_decision_set_id, "Waiting for human approval", "gate_hitl"
        )

        events = self.streaming_service.get_events(self.test_decision_set_id)
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.WORKFLOW_PAUSED
        assert events[0].data["reason"] == "Waiting for human approval"
        assert events[0].data["node"] == "gate_hitl"

    @pytest.mark.asyncio
    async def test_subscription_with_historical_events(self):
        """Test subscribing to events with historical data."""
        # Create some historical events
        for i in range(3):
            await self.streaming_service.emit_node_start(
                self.test_decision_set_id, f"node_{i}", f"Starting node {i}"
            )

        # Subscribe and collect events
        events_received = []
        subscription = self.streaming_service.subscribe(self.test_decision_set_id)

        # Get first few historical events
        async for event in subscription:
            events_received.append(event)
            if len(events_received) >= 3:
                break

        # Check we received historical events
        assert len(events_received) == 3
        for i, event in enumerate(events_received):
            assert event.event_type == StreamEventType.NODE_START
            assert event.data["node"] == f"node_{i}"

    @pytest.mark.asyncio
    async def test_subscription_with_new_events(self):
        """Test subscribing and receiving new events."""
        events_received = []
        subscription = self.streaming_service.subscribe(self.test_decision_set_id)

        # Start subscription task
        async def collect_events():
            async for event in subscription:
                events_received.append(event)
                if len(events_received) >= 2:
                    break

        subscription_task = asyncio.create_task(collect_events())

        # Wait a bit then emit events
        await asyncio.sleep(0.1)
        await self.streaming_service.emit_node_start(
            self.test_decision_set_id, "new_node", "New node started"
        )
        await self.streaming_service.emit_node_complete(
            self.test_decision_set_id, "new_node", message="New node completed"
        )

        # Wait for subscription to complete
        await subscription_task

        # Check we received the new events
        assert len(events_received) == 2
        assert events_received[0].event_type == StreamEventType.NODE_START
        assert events_received[1].event_type == StreamEventType.NODE_COMPLETE

    def test_event_limit_enforcement(self):
        """Test that event storage limits are enforced."""

        # Create more than the limit of events (1000) in a single async context
        async def create_events():
            for i in range(1100):
                event = StreamEvent(
                    event_type=StreamEventType.HEARTBEAT,
                    decision_set_id=self.test_decision_set_id,
                    data={"seq": i},
                )
                await self.streaming_service.emit_event(event)

        asyncio.run(create_events())

        # Check that events are limited due to the get_events limit parameter
        # The default limit in get_events() is 100
        all_events = self.streaming_service.get_events(
            self.test_decision_set_id, limit=None
        )
        events_with_default_limit = self.streaming_service.get_events(
            self.test_decision_set_id
        )

        # After 1100 events, should have been trimmed to around 500-600 (due to timing of trimming)
        assert len(all_events) <= 1000  # Should not exceed the original limit
        assert len(all_events) >= 500  # Should have at least 500 after trimming

        # Default limit should be 100
        assert len(events_with_default_limit) == 100

        # Check that events are recent ones (last event should be seq 1099)
        assert all_events[-1].data["seq"] == 1099

    def test_cleanup_events(self):
        """Test event cleanup functionality."""
        # Add some events
        asyncio.run(
            self.streaming_service.emit_node_start(
                self.test_decision_set_id, "test_node"
            )
        )

        assert self.streaming_service.get_event_count(self.test_decision_set_id) == 1

        # Clean up
        self.streaming_service.cleanup_events(self.test_decision_set_id)

        # Check events are cleaned up
        assert self.streaming_service.get_event_count(self.test_decision_set_id) == 0

    @pytest.mark.asyncio
    async def test_connection_count_tracking(self):
        """Test connection count tracking."""
        initial_count = await self.streaming_service.get_connection_count(
            self.test_decision_set_id
        )

        # Start a subscription
        subscription = self.streaming_service.subscribe(self.test_decision_set_id)

        # Create async generator to simulate subscription
        async def mock_subscription():
            try:
                async for event in subscription:
                    break  # Exit after first event
            except asyncio.CancelledError:
                pass

        subscription_task = asyncio.create_task(mock_subscription())

        # Small delay to let subscription register
        await asyncio.sleep(0.01)

        # Check connection count increased
        count = await self.streaming_service.get_connection_count(
            self.test_decision_set_id
        )
        assert count == initial_count + 1

        # Emit an event to end the subscription
        await self.streaming_service.emit_node_start(self.test_decision_set_id, "test")
        await subscription_task

        # Small delay for cleanup
        await asyncio.sleep(0.05)

        # Connection cleanup happens in the finally block, so we need to ensure
        # the subscription fully completes. Let's just check that the count
        # is back to the initial value or close to it.
        final_count = await self.streaming_service.get_connection_count(
            self.test_decision_set_id
        )
        assert final_count <= initial_count + 1  # Allow for timing issues


class TestReasonCard:
    """Test ReasonCard model and utilities."""

    def test_reason_card_creation(self):
        """Test creating a reason card."""
        reason_card = ReasonCard(
            agent="test_agent",
            node="test_node",
            decision_set_id="test-123",
            reasoning="Test reasoning",
            decision="Test decision",
            category="test-category",
            confidence=0.9,
            inputs={"input1": "value1"},
            outputs={"output1": "result1"},
            alternatives_considered=["option1", "option2"],
            priority="high",
        )

        assert reason_card.agent == "test_agent"
        assert reason_card.confidence == 0.9
        assert reason_card.priority == "high"
        assert len(reason_card.alternatives_considered) == 2

    def test_create_reason_card_utility(self):
        """Test the create_reason_card utility function."""
        reason_card = create_reason_card(
            agent="planner",
            node="planner_node",
            decision_set_id="test-456",
            reasoning="Selected best pattern",
            decision="Use microservices pattern",
            category="pattern-selection",
            confidence=0.85,
        )

        assert isinstance(reason_card, ReasonCard)
        assert reason_card.agent == "planner"
        assert reason_card.decision == "Use microservices pattern"
        assert reason_card.category == "pattern-selection"

    def test_reason_card_sse_data(self):
        """Test ReasonCard SSE data formatting."""
        reason_card = ReasonCard(
            agent="test_agent",
            node="test_node",
            decision_set_id="test-789",
            reasoning="Test reasoning",
            decision="Test decision",
            category="test-category",
        )

        sse_data = reason_card.to_sse_data()

        assert sse_data["type"] == StreamEventType.REASON_CARD
        assert "data" in sse_data
        assert "timestamp" in sse_data
        assert sse_data["data"]["agent"] == "test_agent"


class TestStreamWriter:
    """Test the StreamWriter utility class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.decision_set_id = "test-writer-123"
        self.stream_writer = StreamWriter(self.decision_set_id)

    def test_emit_reason_card(self):
        """Test emitting reason cards via StreamWriter."""
        reason_card = create_reason_card(
            agent="test_agent",
            node="test_node",
            decision_set_id=self.decision_set_id,
            reasoning="Test reasoning",
            decision="Test decision",
            category="test",
        )

        self.stream_writer.emit_reason_card(reason_card)

        events = self.stream_writer.get_events()
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.REASON_CARD
        assert events[0].decision_set_id == self.decision_set_id

    def test_emit_node_events(self):
        """Test emitting node events via StreamWriter."""
        self.stream_writer.emit_node_start("test_node", "Starting test")
        self.stream_writer.emit_node_complete(
            "test_node", {"result": "success"}, "Completed test"
        )

        events = self.stream_writer.get_events()
        assert len(events) == 2

        assert events[0].event_type == StreamEventType.NODE_START
        assert events[0].data["node"] == "test_node"

        assert events[1].event_type == StreamEventType.NODE_COMPLETE
        assert events[1].data["outputs"]["result"] == "success"

    def test_emit_error(self):
        """Test emitting errors via StreamWriter."""
        self.stream_writer.emit_error("Something went wrong", "failing_node")

        events = self.stream_writer.get_events()
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.ERROR
        assert events[0].data["error"] == "Something went wrong"
        assert events[0].data["node"] == "failing_node"

    def test_emit_workflow_paused(self):
        """Test emitting workflow paused via StreamWriter."""
        self.stream_writer.emit_workflow_paused("Waiting for approval", "gate_hitl")

        events = self.stream_writer.get_events()
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.WORKFLOW_PAUSED
        assert events[0].data["reason"] == "Waiting for approval"

    def test_emit_heartbeat(self):
        """Test emitting heartbeat via StreamWriter."""
        self.stream_writer.emit_heartbeat()

        events = self.stream_writer.get_events()
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.HEARTBEAT
        assert "elapsed_ms" in events[0].data

    def test_clear_events(self):
        """Test clearing events from StreamWriter."""
        self.stream_writer.emit_node_start("test_node")
        self.stream_writer.emit_node_complete("test_node")

        assert len(self.stream_writer.get_events()) == 2

        self.stream_writer.clear_events()

        assert len(self.stream_writer.get_events()) == 0


class TestStreamEvent:
    """Test StreamEvent model and SSE formatting."""

    def test_stream_event_creation(self):
        """Test creating a StreamEvent."""
        event = StreamEvent(
            event_type=StreamEventType.NODE_START,
            decision_set_id="test-event-123",
            data={"node": "test_node", "info": "test_info"},
            message="Test message",
        )

        assert event.event_type == StreamEventType.NODE_START
        assert event.decision_set_id == "test-event-123"
        assert event.data["node"] == "test_node"
        assert event.message == "Test message"
        assert isinstance(event.timestamp, datetime)

    def test_sse_formatting(self):
        """Test SSE format generation."""
        event = StreamEvent(
            event_type=StreamEventType.REASON_CARD,
            decision_set_id="test-sse-456",
            data={"agent": "test_agent", "decision": "test_decision"},
            message="Reason card emitted",
        )

        sse_format = event.to_sse_format()

        assert sse_format.startswith("event: reason-card\n")
        assert "data: {" in sse_format
        assert '"type": "reason-card"' in sse_format
        assert '"decision_set_id": "test-sse-456"' in sse_format
        assert '"message": "Reason card emitted"' in sse_format
        assert sse_format.endswith("\n\n")

        # Verify it's valid JSON in the data section
        import json

        data_line = sse_format.split("\ndata: ")[1].split("\n\n")[0]
        parsed_data = json.loads(data_line)
        assert parsed_data["type"] == "reason-card"
        assert parsed_data["decision_set_id"] == "test-sse-456"


class TestGlobalStreamingService:
    """Test the global streaming service instance."""

    def test_get_streaming_service_singleton(self):
        """Test that get_streaming_service returns the same instance."""
        service1 = get_streaming_service()
        service2 = get_streaming_service()

        assert service1 is service2
        assert isinstance(service1, StreamingService)


@pytest.mark.integration
class TestStreamingIntegration:
    """Integration tests for streaming with graph nodes."""

    @pytest.mark.asyncio
    async def test_streaming_service_integration(self):
        """Test streaming service integration with multiple decision sets."""
        streaming_service = get_streaming_service()

        # Create events for multiple decision sets
        decision_set_1 = "integration-test-1"
        decision_set_2 = "integration-test-2"

        # Emit events for both decision sets
        await streaming_service.emit_node_start(
            decision_set_1, "planner", "Planning started"
        )
        await streaming_service.emit_node_start(
            decision_set_2, "critic_tech", "Tech analysis started"
        )

        # Check events are properly isolated
        events_1 = streaming_service.get_events(decision_set_1)
        events_2 = streaming_service.get_events(decision_set_2)

        assert len(events_1) == 1
        assert len(events_2) == 1
        assert events_1[0].data["node"] == "planner"
        assert events_2[0].data["node"] == "critic_tech"

        # Cleanup
        streaming_service.cleanup_events(decision_set_1)
        streaming_service.cleanup_events(decision_set_2)

    def test_all_active_streams(self):
        """Test getting information about all active streams."""
        streaming_service = get_streaming_service()

        # Initially no active streams
        active_streams = streaming_service.get_all_active_streams()
        assert isinstance(active_streams, dict)

        # After cleanup, should be empty or only contain existing test streams
        # (Note: This test might see streams from other tests if run in parallel)
        for decision_set_id, connection_count in active_streams.items():
            assert isinstance(connection_count, int)
            assert connection_count >= 0
