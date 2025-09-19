"""
Test cases for Human-in-the-Loop (HITL) Gate functionality.

Tests the interrupt/resume pattern for plan approval in the MLOps workflow.
"""

import pytest
from unittest.mock import patch, Mock
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from libs.graph import build_full_graph, gate_hitl
from libs.agent_framework import MLOpsWorkflowState


@pytest.mark.skip(reason="HITL tests have event loop and OpenAI quota issues")
class TestHITLGate:
    """Test suite for Human-in-the-Loop gate functionality."""

    @pytest.fixture
    def sample_state_for_hitl(self):
        """Create a sample state ready for HITL gate."""
        return MLOpsWorkflowState(
            messages=[
                HumanMessage(content="I need a serverless ML system for startup")
            ],
            project_id="test_project_001",
            decision_set_id="decision_test_001",
            version=1,
            plan={
                "pattern_name": "Serverless ML Stack",
                "architecture_type": "serverless",
                "estimated_monthly_cost": 420,
                "key_services": {
                    "lambda": "Serverless compute",
                    "sagemaker": "Model hosting",
                },
                "implementation_phases": [
                    "Setup infrastructure",
                    "Deploy models",
                    "Add monitoring",
                ],
            },
            cost_estimate={
                "estimated_monthly_cost": 420,
                "primary_cost_drivers": ["SageMaker", "Lambda", "S3"],
                "budget_compliance_status": "pass",
            },
            tech_critique={
                "overall_feasibility_score": 0.85,
                "technical_risks": ["Cold start latency", "Lambda timeout limits"],
                "recommendations": ["Use provisioned concurrency", "Implement caching"],
            },
            policy_validation={
                "overall_compliance_status": "pass",
                "critical_violations": [],
                "warnings": ["Consider multi-region deployment"],
            },
        )

    def test_hitl_gate_interrupt_payload(self, sample_state_for_hitl):
        """Test that the HITL gate creates proper interrupt payload."""
        # Since gate_hitl uses interrupt(), we need to mock it to test the payload
        with patch("libs.graph.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "decision": "approved",
                "comment": "Looks good",
                "approved_by": "test_user",
            }

            result = gate_hitl(sample_state_for_hitl)

            # Verify interrupt was called
            assert mock_interrupt.called

            # Verify the interrupt payload structure
            interrupt_payload = mock_interrupt.call_args[0][0]
            assert interrupt_payload["status"] == "pending_approval"
            assert "plan_summary" in interrupt_payload
            assert "technical_analysis" in interrupt_payload
            assert "cost_analysis" in interrupt_payload
            assert "policy_analysis" in interrupt_payload
            assert "message" in interrupt_payload

            # Verify plan summary content
            plan_summary = interrupt_payload["plan_summary"]
            assert plan_summary["pattern_name"] == "Serverless ML Stack"
            assert plan_summary["estimated_cost"] == 420
            assert "lambda" in plan_summary["key_services"]

            # Verify result processing
            assert result["hitl"]["status"] == "approved"
            assert result["hitl"]["comment"] == "Looks good"
            assert result["hitl"]["approved_by"] == "test_user"

    def test_hitl_gate_rejection(self, sample_state_for_hitl):
        """Test HITL gate handling rejection."""
        with patch("libs.graph.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "decision": "rejected",
                "comment": "Budget too high, needs revision",
                "approved_by": "budget_manager",
            }

            result = gate_hitl(sample_state_for_hitl)

            assert result["hitl"]["status"] == "rejected"
            assert "Budget too high" in result["hitl"]["comment"]
            assert result["hitl"]["approved_by"] == "budget_manager"

    def test_hitl_gate_auto_approve_fallback(self, sample_state_for_hitl):
        """Test HITL gate auto-approval when no human input."""
        with patch("libs.graph.interrupt") as mock_interrupt:
            mock_interrupt.return_value = None  # No human input

            result = gate_hitl(sample_state_for_hitl)

            assert result["hitl"]["status"] == "approved"
            assert "Auto-approved" in result["hitl"]["comment"]

    def test_hitl_gate_skips_if_already_decided(self, sample_state_for_hitl):
        """Test that HITL gate skips if decision already made."""
        # Add existing HITL decision
        sample_state_for_hitl["hitl"] = {
            "status": "approved",
            "comment": "Previously approved",
            "approved_by": "manager",
        }

        with patch("libs.graph.interrupt") as mock_interrupt:
            result = gate_hitl(sample_state_for_hitl)

            # Should not call interrupt
            assert not mock_interrupt.called

            # Should return empty update (no change)
            assert result == {}

    @patch("libs.graph._get_llm_agents")
    def test_full_graph_with_hitl_interrupt(self, mock_get_agents):
        """Test full graph execution stopping at HITL gate."""
        # Mock all LLM agents to avoid external API calls
        mock_agents = tuple(Mock() for _ in range(7))
        for i, agent in enumerate(mock_agents):
            agent_result = Mock()
            agent_result.success = True
            agent_result.state_updates = {}
            agent_result.reason_card = Mock()
            agent_result.reason_card.model_dump.return_value = {"agent": f"agent_{i}"}
            agent_result.reason_card.outputs = {}
            agent.execute.return_value = agent_result
        mock_get_agents.return_value = mock_agents

        # Build graph and create initial state
        graph = build_full_graph()
        initial_state = {
            "messages": [HumanMessage(content="I need a serverless ML system")],
            "project_id": "test_hitl",
            "decision_set_id": "decision_hitl_001",
            "version": 1,
        }

        config = {"configurable": {"thread_id": "hitl_test_thread"}}

        # Execute graph - should stop at HITL gate with interrupt
        try:
            result = graph.invoke(initial_state, config=config)

            # The graph should complete all nodes through policy_eval
            # and then interrupt at gate_hitl
            assert "reason_cards" in result
            assert "plan" in result
            assert "hitl" in result

            # If we get here, the HITL gate either auto-approved or didn't interrupt
            # In a real scenario with checkpointer, it would interrupt and pause

        except Exception as e:
            # In some test environments, the interrupt might raise an exception
            # This is expected behavior when checkpointer is not properly configured
            assert "interrupt" in str(e).lower() or "checkpointer" in str(e).lower()

    def test_hitl_gate_with_missing_plan_data(self):
        """Test HITL gate gracefully handles missing plan data."""
        minimal_state = MLOpsWorkflowState(
            messages=[HumanMessage(content="Test")],
            project_id="test",
            decision_set_id="decision_001",
            version=1,
            # Missing plan, cost_estimate, tech_critique, policy_validation
        )

        with patch("libs.graph.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "decision": "approved",
                "comment": "Minimal approval",
                "approved_by": "tester",
            }

            result = gate_hitl(minimal_state)

            # Should still work with defaults
            assert mock_interrupt.called
            interrupt_payload = mock_interrupt.call_args[0][0]

            # Should have default values
            assert (
                interrupt_payload["plan_summary"]["pattern_name"] == "Unknown Pattern"
            )
            assert interrupt_payload["plan_summary"]["estimated_cost"] == 0
            assert interrupt_payload["technical_analysis"]["feasibility_score"] == 0.0

            assert result["hitl"]["status"] == "approved"


class TestApprovalAPIIntegration:
    """Test approval API endpoint integration."""

    def test_approval_request_model_validation(self):
        """Test that approval request models validate correctly."""
        from api.main import ApprovalRequest

        # Valid approval request
        valid_request = ApprovalRequest(
            decision="approved", comment="Plan looks good", approved_by="manager"
        )
        assert valid_request.decision == "approved"
        assert valid_request.comment == "Plan looks good"

        # Valid rejection request
        rejection_request = ApprovalRequest(
            decision="rejected", comment="Budget too high"
        )
        assert rejection_request.decision == "rejected"

        # Invalid decision should fail validation
        with pytest.raises(ValueError):
            ApprovalRequest(decision="maybe")

    @patch("api.main._graph")
    def test_approval_endpoint_success(self, mock_graph):
        """Test successful plan approval via API."""
        from fastapi.testclient import TestClient
        from api.main import app
        from unittest.mock import Mock

        # Create a mock database
        def mock_get_db():
            mock_db = Mock()

            # Mock decision set lookup
            mock_decision_set = Mock()
            mock_decision_set.id = "decision_123"
            mock_decision_set.thread_id = "thread_123"

            # Mock the query chain
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_decision_set
            )

            return mock_db

        # Replace the dependency
        from api.main import get_db

        app.dependency_overrides[get_db] = mock_get_db

        # Mock graph execution result
        mock_graph.invoke.return_value = {
            "hitl": {
                "status": "approved",
                "comment": "Plan approved via API",
                "approved_by": "api_user",
            }
        }

        try:
            client = TestClient(app)
            response = client.post(
                "/api/decision-sets/decision_123/approve",
                json={
                    "decision": "approved",
                    "comment": "Looks good to me",
                    "approved_by": "test_manager",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["decision_set_id"] == "decision_123"
            assert data["thread_id"] == "thread_123"
            assert data["approval_status"] == "approved"

            # Verify graph was called with Command(resume=...)
            assert mock_graph.invoke.called
            call_args = mock_graph.invoke.call_args
            command = call_args[0][0]
            assert isinstance(command, Command)

        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_approval_endpoint_decision_set_not_found(self):
        """Test approval endpoint with non-existent decision set."""
        from fastapi.testclient import TestClient
        from api.main import app

        with patch("api.main.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Mock decision set not found
            mock_db.query.return_value.filter.return_value.first.return_value = None

            client = TestClient(app)
            response = client.post(
                "/api/decision-sets/nonexistent/approve", json={"decision": "approved"}
            )

            assert response.status_code == 404
            assert "Decision set not found" in response.json()["detail"]
