"""
End-to-End Integration Test for Human-in-the-Loop (HITL) functionality.

Demonstrates the complete workflow from chat request to approval and completion.
"""

from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from langgraph.types import interrupt


class TestHITLEndToEnd:
    """End-to-End test scenarios for HITL workflow."""

    @patch("libs.graph._get_llm_agents")  # Mock LLM agents to avoid API calls
    def test_complete_hitl_workflow_with_approval(self, mock_get_agents):
        """Test complete HITL workflow: chat -> interrupt -> approval -> completion."""

        # Mock all LLM agents to return success
        mock_agents = tuple(Mock() for _ in range(7))
        for i, agent in enumerate(mock_agents):
            agent_result = Mock()
            agent_result.success = True
            agent_result.state_updates = {
                "plan" if i == 3 else f"agent_{i}_result": {
                    "pattern_name": "Test Pattern",
                    "estimated_monthly_cost": 400,
                    "key_services": {"lambda": "serverless compute"},
                }
            }
            agent_result.reason_card = Mock()
            agent_result.reason_card.model_dump.return_value = {
                "agent": f"agent_{i}",
                "confidence": 0.85,
            }
            agent_result.reason_card.outputs = {}
            agent.execute.return_value = agent_result
        mock_get_agents.return_value = mock_agents

        # Create TestClient for API
        from api.main import app

        # Mock database for decision sets
        def mock_get_db():
            mock_db = Mock()
            mock_decision_set = Mock()
            mock_decision_set.id = "ds_123"
            mock_decision_set.thread_id = "thread_123"
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_decision_set
            )
            return mock_db

        from api.main import get_db

        app.dependency_overrides[get_db] = mock_get_db

        client = TestClient(app)

        try:
            # Step 1: Start a chat session that should reach HITL gate
            with patch.dict("os.environ", {"USE_FULL_GRAPH": "true"}):
                # This would normally interrupt at gate_hitl, but since we're using
                # the sync endpoint with auto-approve fallback, it should complete
                response = client.post(
                    "/api/chat",
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": "I need a serverless ML system for startup",
                            }
                        ],
                        "thread_id": "thread_123",
                    },
                )

                # Should succeed (auto-approved in sync mode)
                assert response.status_code == 200
                data = response.json()
                assert "messages" in data
                assert data["thread_id"] == "thread_123"

                # Verify the conversation includes planning results
                messages = data["messages"]
                assert len(messages) >= 2  # At least user + assistant

            # Step 2: Test manual approval workflow
            # Create a mock graph that will interrupt
            def mock_hitl_with_interrupt(state):
                """Mock HITL function that actually interrupts."""
                payload = {
                    "status": "pending_approval",
                    "plan_summary": {
                        "pattern_name": "Test Pattern",
                        "estimated_cost": 400,
                    },
                    "message": "Please approve this plan",
                }
                # This will raise an interrupt that needs to be handled
                return interrupt(payload)

            with patch("libs.graph.gate_hitl", side_effect=mock_hitl_with_interrupt):
                # Step 3: Test approval endpoint
                approval_response = client.post(
                    "/api/decision-sets/ds_123/approve",
                    json={
                        "decision": "approved",
                        "comment": "Plan looks good for MVP",
                        "approved_by": "product_manager",
                    },
                )

                # The approval endpoint should handle the interrupt and resume
                # In a real scenario, this would resume the graph execution
                assert approval_response.status_code == 200
                approval_data = approval_response.json()
                assert approval_data["success"] is True
                assert approval_data["decision_set_id"] == "ds_123"
                assert approval_data["thread_id"] == "thread_123"

        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @patch("libs.graph._get_llm_agents")
    def test_hitl_workflow_with_rejection(self, mock_get_agents):
        """Test HITL workflow with plan rejection."""

        # Mock LLM agents
        mock_agents = tuple(Mock() for _ in range(7))
        for agent in mock_agents:
            agent_result = Mock()
            agent_result.success = True
            agent_result.state_updates = {
                "plan": {
                    "pattern_name": "Expensive Pattern",
                    "estimated_monthly_cost": 2000,
                }
            }
            agent_result.reason_card = Mock()
            agent_result.reason_card.model_dump.return_value = {
                "agent": "mock",
                "confidence": 0.8,
            }
            agent_result.reason_card.outputs = {}
            agent.execute.return_value = agent_result
        mock_get_agents.return_value = mock_agents

        from api.main import app

        # Mock database
        def mock_get_db():
            mock_db = Mock()
            mock_decision_set = Mock()
            mock_decision_set.id = "ds_reject_123"
            mock_decision_set.thread_id = "thread_reject_123"
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_decision_set
            )
            return mock_db

        from api.main import get_db

        app.dependency_overrides[get_db] = mock_get_db

        client = TestClient(app)

        try:
            # Test rejection workflow
            rejection_response = client.post(
                "/api/decision-sets/ds_reject_123/approve",
                json={
                    "decision": "rejected",
                    "comment": "Budget too high - need to reduce costs",
                    "approved_by": "budget_manager",
                },
            )

            assert rejection_response.status_code == 200
            rejection_data = rejection_response.json()
            assert rejection_data["success"] is True
            assert rejection_data["decision_set_id"] == "ds_reject_123"
            # In real implementation, rejection would trigger workflow revision

        finally:
            app.dependency_overrides.clear()

    def test_hitl_error_handling(self):
        """Test HITL error handling scenarios."""
        from api.main import app

        # Mock database to return no decision set
        def mock_get_db_not_found():
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            return mock_db

        from api.main import get_db

        app.dependency_overrides[get_db] = mock_get_db_not_found

        client = TestClient(app)

        try:
            # Test approval for non-existent decision set
            response = client.post(
                "/api/decision-sets/nonexistent/approve", json={"decision": "approved"}
            )

            assert response.status_code == 404
            assert "Decision set not found" in response.json()["detail"]

        finally:
            app.dependency_overrides.clear()

    def test_approval_model_validation(self):
        """Test API model validation for approval requests."""
        from api.main import app

        client = TestClient(app)

        # Test invalid decision value
        response = client.post(
            "/api/decision-sets/test/approve",
            json={"decision": "maybe"},  # Invalid - must be "approved" or "rejected"
        )

        assert response.status_code == 422  # Validation error
        assert "literal_error" in response.json()["detail"][0]["type"]

    def test_hitl_payload_structure(self):
        """Test that HITL interrupt payload has correct structure."""
        from libs.graph import gate_hitl
        from libs.agent_framework import MLOpsWorkflowState

        # Create a realistic state for testing
        test_state = MLOpsWorkflowState(
            project_id="test_proj",
            decision_set_id="test_ds",
            version=1,
            plan={
                "pattern_name": "Test ML Pattern",
                "architecture_type": "hybrid",
                "estimated_monthly_cost": 750,
                "key_services": {"sagemaker": "ML platform", "lambda": "processing"},
                "implementation_phases": ["Setup", "Deploy", "Test"],
            },
            cost_estimate={
                "estimated_monthly_cost": 750,
                "primary_cost_drivers": ["SageMaker", "EC2", "S3"],
                "budget_compliance_status": "warning",
            },
            tech_critique={
                "overall_feasibility_score": 0.88,
                "technical_risks": ["Scaling complexity", "Data consistency"],
                "recommendations": ["Implement caching", "Add monitoring"],
            },
            policy_validation={
                "overall_compliance_status": "conditional_pass",
                "critical_violations": [],
                "warnings": ["Multi-region backup recommended"],
            },
        )

        # Mock interrupt to capture the payload
        with patch("libs.graph.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "decision": "approved",
                "comment": "Test approval",
                "approved_by": "tester",
            }

            result = gate_hitl(test_state)

            # Verify interrupt was called with proper payload
            assert mock_interrupt.called
            payload = mock_interrupt.call_args[0][0]

            # Verify payload structure
            assert payload["status"] == "pending_approval"
            assert "plan_summary" in payload
            assert "technical_analysis" in payload
            assert "cost_analysis" in payload
            assert "policy_analysis" in payload
            assert "message" in payload
            assert "timestamp" in payload

            # Verify plan summary details
            plan_summary = payload["plan_summary"]
            assert plan_summary["pattern_name"] == "Test ML Pattern"
            assert plan_summary["estimated_cost"] == 750
            assert "sagemaker" in plan_summary["key_services"]
            assert len(plan_summary["implementation_phases"]) == 3

            # Verify technical analysis
            tech_analysis = payload["technical_analysis"]
            assert tech_analysis["feasibility_score"] == 0.88
            assert len(tech_analysis["key_risks"]) <= 3  # Truncated to top 3
            assert "Scaling complexity" in tech_analysis["key_risks"]

            # Verify cost analysis
            cost_analysis = payload["cost_analysis"]
            assert cost_analysis["monthly_cost"] == 750
            assert cost_analysis["budget_status"] == "warning"
            assert len(cost_analysis["primary_drivers"]) <= 3

            # Verify policy analysis
            policy_analysis = payload["policy_analysis"]
            assert policy_analysis["overall_status"] == "conditional_pass"
            assert len(policy_analysis["critical_violations"]) == 0
            assert len(policy_analysis["warnings"]) == 1

            # Verify result processing
            assert result["hitl"]["status"] == "approved"
            assert result["hitl"]["comment"] == "Test approval"
            assert result["hitl"]["approved_by"] == "tester"
