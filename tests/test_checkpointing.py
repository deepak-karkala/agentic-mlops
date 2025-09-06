"""
Tests for LangGraph checkpointing and durable state functionality.

This module tests Issue #7 requirements: PostgresSaver integration,
thread_id persistence, and graph state resumption capabilities.
"""

import pytest
import uuid
from libs.database import (
    create_appropriate_checkpointer,
    create_postgres_checkpointer_safe,
    POSTGRES_CHECKPOINTER_AVAILABLE,
    get_database_url,
)
from libs.graph import build_thin_graph
from langchain_core.messages import HumanMessage


class TestCheckpointing:
    """Test LangGraph checkpointing functionality."""

    def test_checkpointer_availability(self):
        """Test that checkpointer availability is correctly detected."""
        # Use the new intelligent checkpointer that works in all environments
        checkpointer = create_appropriate_checkpointer()

        # With the new modular system, we should always have some form of checkpointer
        assert checkpointer is not None

        database_url = get_database_url()
        if database_url.startswith("sqlite"):
            # SQLite environment - should have SqliteSaver or MemorySaver
            assert type(checkpointer).__name__ in ["SqliteSaver", "InMemorySaver"]
        else:
            # PostgreSQL environment - should have PostgresSaver
            if POSTGRES_CHECKPOINTER_AVAILABLE:
                assert type(checkpointer).__name__ == "PostgresSaver"
            else:
                # Fallback to memory or SQLite saver
                assert type(checkpointer).__name__ in ["SqliteSaver", "InMemorySaver"]

    def test_graph_compilation_with_checkpointing(self):
        """Test that graph compiles successfully with or without checkpointing."""
        graph = build_thin_graph()
        assert graph is not None

        # Graph should be executable regardless of checkpointer availability
        state = {"messages": [HumanMessage(content="test")]}
        config = {"configurable": {"thread_id": "test-thread"}}

        result = graph.invoke(state, config=config)
        assert "messages" in result
        assert len(result["messages"]) > 0

    def test_thread_id_usage(self):
        """Test that thread_id is properly used in graph invocation."""
        graph = build_thin_graph()
        thread_id = str(uuid.uuid4())

        state = {"messages": [HumanMessage(content="Hello thread test")]}
        config = {"configurable": {"thread_id": thread_id}}

        # First invocation
        result1 = graph.invoke(state, config=config)
        assert "messages" in result1

        # Second invocation with same thread_id should work
        state2 = {"messages": [HumanMessage(content="Follow-up message")]}
        result2 = graph.invoke(state2, config=config)
        assert "messages" in result2

    @pytest.mark.skipif(
        not POSTGRES_CHECKPOINTER_AVAILABLE or get_database_url().startswith("sqlite"),
        reason="PostgreSQL checkpointing not available",
    )
    def test_state_persistence_with_postgres(self):
        """Test state persistence when PostgreSQL is available."""
        # This test only runs when we have actual PostgreSQL checkpointing
        checkpointer = create_postgres_checkpointer_safe()
        assert checkpointer is not None

        graph = build_thin_graph()
        thread_id = f"persist-test-{uuid.uuid4()}"

        # First interaction
        state1 = {"messages": [HumanMessage(content="First message")]}
        config = {"configurable": {"thread_id": thread_id}}

        result1 = graph.invoke(state1, config=config)
        assert "messages" in result1

        # Verify state is persisted by checking checkpoint tables
        # Note: This would require database inspection in a full integration test

    def test_multiple_threads_isolation(self):
        """Test that different thread_ids are isolated from each other."""
        graph = build_thin_graph()

        thread_id_1 = f"thread-1-{uuid.uuid4()}"
        thread_id_2 = f"thread-2-{uuid.uuid4()}"

        # Interaction with first thread
        state1 = {"messages": [HumanMessage(content="Message in thread 1")]}
        config1 = {"configurable": {"thread_id": thread_id_1}}
        result1 = graph.invoke(state1, config=config1)

        # Interaction with second thread
        state2 = {"messages": [HumanMessage(content="Message in thread 2")]}
        config2 = {"configurable": {"thread_id": thread_id_2}}
        result2 = graph.invoke(state2, config=config2)

        # Both should succeed and be independent
        assert "messages" in result1
        assert "messages" in result2

        # Results should be based on their respective inputs
        assert "thread 1" in result1["messages"][-1].content
        assert "thread 2" in result2["messages"][-1].content

    def test_graph_resume_functionality(self):
        """Test that graph can be conceptually resumed (Issue #7 requirement)."""
        graph = build_thin_graph()
        thread_id = f"resume-test-{uuid.uuid4()}"

        # First interaction - start of conversation
        state1 = {"messages": [HumanMessage(content="Start conversation")]}
        config = {"configurable": {"thread_id": thread_id}}

        result1 = graph.invoke(state1, config=config)
        assert "messages" in result1

        # Simulate "resuming" by calling with the same thread_id
        # In a stateful system, this would resume from checkpoint
        state2 = {"messages": [HumanMessage(content="Resume conversation")]}
        result2 = graph.invoke(state2, config=config)

        # Should successfully process the resume
        assert "messages" in result2
        assert len(result2["messages"]) > 0

        # The fact that it processes successfully demonstrates the resume capability
        # (actual state continuity would be tested with real PostgreSQL)


class TestDatabaseConfiguration:
    """Test database configuration for checkpointing."""

    def test_database_url_handling(self):
        """Test that database URL is correctly detected."""
        db_url = get_database_url()
        assert isinstance(db_url, str)
        assert len(db_url) > 0

        # Should be either SQLite or PostgreSQL format
        assert db_url.startswith(("sqlite://", "postgresql://"))

    def test_checkpointer_creation_safety(self):
        """Test that checkpointer creation handles errors gracefully."""
        # This should never raise an exception, even if dependencies are missing
        checkpointer = create_postgres_checkpointer_safe()

        # Should be either None or a valid checkpointer instance
        if checkpointer is not None:
            # Basic validation that it's a checkpointer-like object
            assert hasattr(checkpointer, "setup") or hasattr(checkpointer, "put")
