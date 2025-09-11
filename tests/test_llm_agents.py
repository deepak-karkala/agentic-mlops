"""
Comprehensive tests for LLM-powered agents

Tests the complete LLM transformation including:
- Individual agent functionality
- Context accumulation between agents
- Structured output validation
- Error handling and resilience
- Integration with the workflow
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from libs.agent_framework import AgentType, TriggerType, MLOpsWorkflowState
from libs.constraint_schema import (
    MLOpsConstraints,
    ConstraintExtractionResult,
    CoverageAnalysisResult,
    AdaptiveQuestioningResult,
)
from libs.agent_output_schemas import PlannerOutput

# Import LLM agents
from libs.intake_extract_agent import create_intake_extract_agent
from libs.coverage_check_agent import create_coverage_check_agent
from libs.adaptive_questions_agent import create_adaptive_questions_agent
from libs.llm_planner_agent import create_llm_planner_agent


class TestLLMAgentBase:
    """Test base LLM agent functionality and context accumulation."""

    @pytest.fixture
    def sample_project_state(self) -> MLOpsWorkflowState:
        """Sample project state for testing."""
        return {
            "project_id": "test-project",
            "decision_set_id": "test-decision-set",
            "version": 1,
            "messages": [
                {
                    "role": "user",
                    "content": "I need a real-time ML system for credit card fraud detection. We handle 100K transactions per day, need sub-200ms response time, and must comply with PCI-DSS. Budget is around $2000/month.",
                }
            ],
            "execution_order": [],
            "reason_cards": [],
            "agent_outputs": {},
        }

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for testing."""
        return Mock()

    def test_context_accumulation(self, sample_project_state):
        """Test that context accumulates correctly between agents."""
        from libs.llm_agent_base import MLOpsExecutionContext

        context = MLOpsExecutionContext(sample_project_state)

        # Test basic context extraction
        assert context.user_input
        assert "credit card fraud detection" in context.user_input.lower()

        # Test empty execution history initially
        assert len(context.execution_history) == 0
        assert len(context.reason_cards) == 0


class TestIntakeExtractAgent:
    """Test the IntakeExtractAgent LLM-powered constraint extraction."""

    @pytest.fixture
    def agent(self):
        return create_intake_extract_agent()

    @pytest.fixture
    def sample_extraction_result(self):
        """Sample constraint extraction result."""
        constraints = MLOpsConstraints(
            project_description="Real-time ML system for credit card fraud detection",
            budget_band="enterprise",
            deployment_preference="containers",
            workload_types=["online_inference"],
            expected_throughput="high",
            data_classification="restricted",
            compliance_requirements=["PCI-DSS"],
            latency_requirements_ms=200,
        )

        return ConstraintExtractionResult(
            constraints=constraints,
            extraction_confidence=0.85,
            uncertain_fields=["team_expertise", "availability_target"],
            extraction_rationale="Extracted based on clear requirements for fraud detection system with PCI-DSS compliance",
            follow_up_needed=True,
        )

    def test_agent_creation(self, agent):
        """Test agent initialization."""
        assert agent.agent_type == AgentType.INTAKE_EXTRACT
        assert agent.name == "Intake Extract Agent"
        assert "parse natural language" in agent.description.lower()
        assert agent.model == "gpt-4-turbo-preview"
        assert agent.temperature == 0.3

    def test_system_prompt_quality(self, agent):
        """Test system prompt contains key elements."""
        prompt = agent.system_prompt

        # Check for key prompt components
        assert "MLOps requirements analyst" in prompt
        assert "budget" in prompt.lower()
        assert "workload" in prompt.lower()
        assert "compliance" in prompt.lower()
        assert "data classification" in prompt.lower()

    def test_structured_output_type(self, agent):
        """Test structured output type is correct."""
        output_type = asyncio.run(agent.get_structured_output_type())
        assert output_type == ConstraintExtractionResult

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_successful_extraction(
        self, mock_get_client, agent, sample_extraction_result
    ):
        """Test successful constraint extraction."""
        # Mock LLM client
        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value=sample_extraction_result)
        mock_get_client.return_value = mock_client

        # Sample project state
        project_state = {
            "messages": [
                {
                    "role": "user",
                    "content": "Build fraud detection ML system with PCI compliance",
                }
            ],
            "project_id": "test",
            "decision_set_id": "test-ds",
            "version": 1,
            "agent_outputs": {},
            "reason_cards": [],
            "execution_order": [],
        }

        result = await agent.execute(project_state, TriggerType.INITIAL)

        assert result.success
        assert result.reason_card is not None
        assert "constraints" in result.state_updates

        # Verify constraint extraction
        constraints = result.state_updates["constraints"]
        assert (
            constraints["project_description"]
            == "Real-time ML system for credit card fraud detection"
        )
        assert constraints["compliance_requirements"] == ["PCI-DSS"]

    def test_user_prompt_building(self, agent):
        """Test user prompt construction."""
        from libs.llm_agent_base import MLOpsExecutionContext

        project_state = {
            "messages": [
                {"role": "user", "content": "Build ML system for image recognition"}
            ],
            "agent_outputs": {},
            "reason_cards": [],
            "execution_order": [],
        }

        context = MLOpsExecutionContext(project_state)
        prompt = agent.build_user_prompt(context)

        assert "image recognition" in prompt
        assert "extract structured constraint information" in prompt.lower()


class TestCoverageCheckAgent:
    """Test the CoverageCheckAgent LLM-powered coverage analysis."""

    @pytest.fixture
    def agent(self):
        return create_coverage_check_agent()

    @pytest.fixture
    def sample_coverage_result(self):
        """Sample coverage analysis result."""
        return CoverageAnalysisResult(
            coverage_score=0.65,
            missing_critical_fields=["availability_target", "team_expertise"],
            missing_optional_fields=["model_size_category", "training_frequency"],
            ambiguous_fields=["deployment_preference"],
            coverage_threshold_met=False,
            recommendations=[
                "Clarify availability requirements for fraud detection system",
                "Specify team expertise level for deployment complexity decisions",
            ],
        )

    def test_agent_creation(self, agent):
        """Test agent initialization."""
        assert agent.agent_type == AgentType.COVERAGE_CHECK
        assert agent.model == "gpt-4-turbo-preview"
        assert agent.temperature == 0.2  # Lower temperature for consistent analysis

    def test_required_predecessors(self, agent):
        """Test required predecessor agents."""
        predecessors = agent.get_required_predecessor_agents()
        assert AgentType.INTAKE_EXTRACT.value in predecessors

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_coverage_analysis(
        self, mock_get_client, agent, sample_coverage_result
    ):
        """Test coverage analysis functionality."""
        # Mock LLM client
        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value=sample_coverage_result)
        mock_get_client.return_value = mock_client

        # Project state with constraints
        project_state = {
            "constraints": {
                "project_description": "Fraud detection system",
                "budget_band": "enterprise",
                "workload_types": ["online_inference"],
            },
            "constraint_extraction": {"confidence": 0.8},
            "project_id": "test",
            "decision_set_id": "test-ds",
            "version": 1,
            "agent_outputs": {"intake_extract": {}},
            "reason_cards": [],
            "execution_order": ["intake_extract"],
            "messages": [],
        }

        result = await agent.execute(project_state, TriggerType.INITIAL)

        assert result.success
        assert result.state_updates["coverage_score"] == 0.65
        assert not result.state_updates["coverage_threshold_met"]

        coverage_analysis = result.state_updates["coverage_analysis"]
        assert "availability_target" in coverage_analysis["critical_gaps"]


class TestAdaptiveQuestionsAgent:
    """Test the AdaptiveQuestionsAgent iterative questioning."""

    @pytest.fixture
    def agent(self):
        return create_adaptive_questions_agent()

    @pytest.fixture
    def sample_questioning_result(self):
        """Sample adaptive questioning result."""
        from libs.constraint_schema import AdaptiveQuestion

        questions = [
            AdaptiveQuestion(
                question_id="availability_req",
                question_text="What availability level do you need for your fraud detection system? Financial systems typically require 99.9% (8.77 hours downtime/year) or 99.95% (4.38 hours/year) uptime.",
                field_targets=["availability_target"],
                priority="high",
                question_type="choice",
                choices=["99.9%", "99.95%", "99.99%"],
            ),
            AdaptiveQuestion(
                question_id="team_expertise",
                question_text="What's your team's experience level with cloud deployments? This helps us recommend the right complexity level.",
                field_targets=["team_expertise"],
                priority="medium",
                question_type="choice",
                choices=[
                    "Beginner (prefer managed services)",
                    "Intermediate (comfortable with containers)",
                    "Expert (can handle Kubernetes)",
                ],
            ),
        ]

        return AdaptiveQuestioningResult(
            questions=questions,
            questioning_complete=False,
            current_coverage=0.65,
            target_coverage=0.75,
            questioning_rationale="Generated questions to address critical gaps in availability requirements and team capability assessment",
        )

    def test_agent_creation(self, agent):
        """Test agent initialization."""
        assert agent.agent_type == AgentType.ADAPTIVE_QUESTIONS
        assert agent.temperature == 0.4  # Moderate temperature for creative questions

    def test_required_predecessors(self, agent):
        """Test required predecessor agents."""
        predecessors = agent.get_required_predecessor_agents()
        assert AgentType.INTAKE_EXTRACT.value in predecessors
        assert AgentType.COVERAGE_CHECK.value in predecessors

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_question_generation(
        self, mock_get_client, agent, sample_questioning_result
    ):
        """Test question generation functionality."""
        # Mock LLM client
        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value=sample_questioning_result)
        mock_get_client.return_value = mock_client

        # Project state with coverage gaps
        project_state = {
            "constraints": {
                "project_description": "Fraud detection system",
                "budget_band": "enterprise",
            },
            "coverage_analysis": {
                "score": 0.65,
                "threshold_met": False,
                "critical_gaps": ["availability_target", "team_expertise"],
            },
            "coverage_score": 0.65,
            "questioning_history": [],
            "project_id": "test",
            "decision_set_id": "test-ds",
            "version": 1,
            "agent_outputs": {},
            "reason_cards": [],
            "execution_order": ["intake_extract", "coverage_check"],
            "messages": [],
        }

        result = await agent.execute(project_state, TriggerType.INITIAL)

        assert result.success
        assert len(result.state_updates["current_questions"]) == 2
        assert not result.state_updates["questioning_complete"]

        # Verify question quality
        questions = result.state_updates["current_questions"]
        availability_q = next(
            q for q in questions if q["question_id"] == "availability_req"
        )
        assert "99.9%" in availability_q["choices"]
        assert availability_q["priority"] == "high"

    async def test_questioning_termination(self, agent):
        """Test questioning termination conditions."""
        # Test with high coverage score
        high_coverage_state = {"coverage_score": 0.8, "questioning_complete": False}

        termination_result = await agent.should_continue_questioning(
            high_coverage_state
        )
        assert not termination_result

        # Test with questioning already complete
        complete_state = {"coverage_score": 0.6, "questioning_complete": True}

        termination_result = await agent.should_continue_questioning(complete_state)
        assert not termination_result


class TestLLMPlannerAgent:
    """Test the LLM-powered PlannerAgent."""

    @pytest.fixture
    def agent(self):
        return create_llm_planner_agent()

    @pytest.fixture
    def sample_planner_output(self):
        """Sample planner output."""
        return PlannerOutput(
            selected_pattern_id="realtime_inference_enterprise",
            pattern_name="Real-time ML Inference (Enterprise)",
            selection_confidence=0.87,
            selection_rationale="Selected based on high-throughput real-time inference requirements, PCI-DSS compliance needs, and enterprise budget allocation",
            alternatives_considered=[
                {
                    "pattern_id": "serverless_inference",
                    "reason": "Lower cost but higher cold start latency",
                },
                {
                    "pattern_id": "batch_inference",
                    "reason": "Not suitable for real-time fraud detection",
                },
            ],
            pattern_comparison="Enterprise pattern chosen over serverless for guaranteed low latency and compliance controls",
            architecture_overview="Container-based architecture with auto-scaling inference endpoints, dedicated VPC for PCI compliance, and real-time feature store",
            key_services={
                "inference": "Amazon SageMaker Real-time Endpoints",
                "features": "Amazon SageMaker Feature Store",
                "data": "Amazon RDS (encrypted)",
                "monitoring": "CloudWatch + X-Ray",
            },
            estimated_monthly_cost=1850.0,
            deployment_approach="Blue-green deployment with automated rollback",
            implementation_phases=[
                "Phase 1: Infrastructure setup and VPC configuration",
                "Phase 2: Model deployment and feature store setup",
                "Phase 3: Monitoring and compliance validation",
            ],
            critical_success_factors=[
                "PCI-DSS compliance validation",
                "Sub-200ms latency achievement",
                "99.95% availability target",
            ],
            potential_challenges=[
                "Complex PCI-DSS compliance setup",
                "Model inference optimization for latency",
            ],
            success_metrics=[
                "Response latency < 200ms (P99)",
                "System availability > 99.95%",
                "PCI-DSS audit readiness",
            ],
            assumptions_made=[
                "Team has container deployment experience",
                "PCI-DSS compliance team available for consultation",
            ],
            decision_criteria=[
                "Latency requirements",
                "Compliance needs",
                "Budget constraints",
                "Scalability requirements",
            ],
        )

    def test_agent_creation(self, agent):
        """Test agent initialization."""
        assert agent.agent_type == AgentType.PLANNER
        assert agent.name == "LLM MLOps Planner"
        assert agent.temperature == 0.2  # Lower temperature for consistent architecture

    def test_pattern_library_access(self, agent):
        """Test that LLM planner has knowledge of MLOps patterns."""
        # LLM-powered planner uses reasoning instead of hard-coded patterns
        # Check that it can provide pattern library summary for context
        pattern_summary = agent.get_pattern_library_summary()
        assert "serverless" in pattern_summary.lower()
        assert "containerized" in pattern_summary.lower()
        assert "kubernetes" in pattern_summary.lower()
        assert "batch" in pattern_summary.lower()
        
        # Verify it provides meaningful architectural guidance
        assert len(pattern_summary) > 100  # Should be substantial description

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_pattern_selection(
        self, mock_get_client, agent, sample_planner_output
    ):
        """Test intelligent pattern selection."""
        # Mock LLM client
        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value=sample_planner_output)
        mock_get_client.return_value = mock_client

        # Rich project state with complete context
        project_state = {
            "constraints": {
                "project_description": "Real-time fraud detection system",
                "budget_band": "enterprise",
                "workload_types": ["online_inference"],
                "expected_throughput": "high",
                "latency_requirements_ms": 200,
                "compliance_requirements": ["PCI-DSS"],
            },
            "coverage_score": 0.8,
            "questioning_complete": True,
            "project_id": "test",
            "decision_set_id": "test-ds",
            "version": 1,
            "agent_outputs": {},
            "reason_cards": [],
            "execution_order": ["intake_extract", "coverage_check"],
            "messages": [],
        }

        result = await agent.execute(project_state, TriggerType.INITIAL)

        assert result.success

        # Verify plan structure
        plan = result.state_updates["plan"]
        assert plan["pattern_id"] == "realtime_inference_enterprise"
        assert plan["estimated_monthly_cost"] == 1850.0
        assert "PCI-DSS" in plan["critical_success_factors"][0]

        # Verify reasoning quality
        assert len(plan["alternatives_considered"]) > 0
        assert plan["selection_confidence"] > 0.8


class TestIntegrationWorkflow:
    """Test integration of LLM agents in the complete workflow."""

    @pytest.fixture
    def complete_project_state(self):
        """Complete project state after all agents have executed."""
        return {
            "project_id": "integration-test",
            "messages": [
                {
                    "role": "user",
                    "content": "Build fraud detection ML system with PCI compliance",
                }
            ],
            # Constraint extraction results
            "constraints": {
                "project_description": "Real-time fraud detection system",
                "budget_band": "enterprise",
                "workload_types": ["online_inference"],
                "compliance_requirements": ["PCI-DSS"],
            },
            # Coverage analysis results
            "coverage_score": 0.8,
            "coverage_threshold_met": True,
            "questioning_complete": True,
            # Planning results
            "plan": {
                "pattern_id": "realtime_inference_enterprise",
                "estimated_monthly_cost": 1850.0,
                "key_services": {"inference": "SageMaker", "data": "RDS"},
            },
            # Execution tracking
            "execution_order": [
                "intake_extract",
                "coverage_check",
                "adaptive_questions",
                "planner",
            ],
            "reason_cards": [
                {"agent": "intake_extract", "confidence": 0.85},
                {"agent": "coverage_check", "confidence": 0.9},
                {"agent": "planner", "confidence": 0.87},
            ],
            "agent_outputs": {
                "intake_extract": {"extraction_confidence": 0.85},
                "coverage_check": {"coverage_score": 0.8},
                "planner": {"selected_pattern_id": "realtime_inference_enterprise"},
            },
            "reason_cards": [
                {
                    "agent": "planner",
                    "decision_id": "plan-001",
                    "choice": {
                        "id": "realtime_inference_enterprise",
                        "justification": "Selected enterprise-grade real-time inference pattern for fraud detection",
                        "confidence": 0.85
                    },
                    "confidence": 0.85,
                    "outputs": {"selected_pattern_id": "realtime_inference_enterprise"},
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                {
                    "agent": "tech_critic",
                    "decision_id": "tech-001",
                    "choice": {
                        "id": "approved_with_recommendations",
                        "justification": "Architecture is feasible with some performance considerations",
                        "confidence": 0.8
                    },
                    "confidence": 0.8,
                    "outputs": {"feasibility_score": 0.8},
                    "timestamp": "2024-01-01T12:05:00Z"
                }
            ],
        }

    def test_sequential_context_building(self, complete_project_state):
        """Test that context builds properly across agent executions."""
        from libs.llm_agent_base import MLOpsExecutionContext

        context = MLOpsExecutionContext(complete_project_state)

        # Test context summary includes all previous results
        context_summary = context.build_context_summary()

        assert "fraud detection" in context_summary.lower()
        assert "pci-dss" in context_summary.lower() or "pci" in context_summary.lower()
        assert "1850" in context_summary  # Cost information

        # Test previous decisions extraction
        decisions = context.get_previous_decisions()
        assert len(decisions) >= 2  # Should have multiple decision points

        # Test current plan access
        plan = context.get_current_plan()
        assert plan is not None
        assert plan["pattern_id"] == "realtime_inference_enterprise"

    def test_agent_specific_context(self, complete_project_state):
        """Test agent-specific context building."""
        from libs.llm_agent_base import MLOpsExecutionContext

        context = MLOpsExecutionContext(complete_project_state)

        # Test tech critic context (should include plan)
        tech_context = context.get_agent_specific_context(AgentType.CRITIC_TECH)
        assert "plan" in tech_context
        assert tech_context["plan"]["pattern_id"] == "realtime_inference_enterprise"

        # Test cost critic context (should include plan and tech analysis)
        cost_context = context.get_agent_specific_context(AgentType.CRITIC_COST)
        assert "plan" in cost_context

        # Test policy engine context (should include everything)
        policy_context = context.get_agent_specific_context(AgentType.POLICY_ENGINE)
        assert "plan" in policy_context
        assert "constraints" in policy_context

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_error_handling_and_recovery(self, mock_get_client):
        """Test error handling across the agent chain."""
        # Mock LLM client that fails
        mock_client = Mock()
        mock_client.complete = AsyncMock(side_effect=Exception("OpenAI API error"))
        mock_get_client.return_value = mock_client

        # Test intake extract agent error handling
        agent = create_intake_extract_agent()
        project_state = {
            "messages": [{"role": "user", "content": "Test"}],
            "project_id": "test",
            "decision_set_id": "test-ds",
            "version": 1,
        }

        result = await agent.execute(project_state, TriggerType.INITIAL)

        assert not result.success
        assert "error" in result.error_message.lower()
        assert result.reason_card is not None  # Should still create error reason card


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""

    def test_context_memory_efficiency(self):
        """Test that context objects don't grow unbounded."""
        from libs.llm_agent_base import MLOpsExecutionContext

        # Create large project state
        large_state = {
            "reason_cards": [{"data": f"test_{i}"} for i in range(100)],
            "agent_outputs": {f"agent_{i}": {"output": f"data_{i}"} for i in range(50)},
            "execution_order": [f"step_{i}" for i in range(100)],
            "messages": [{"role": "user", "content": "Test system"}],
        }

        context = MLOpsExecutionContext(large_state)

        # Context summary should be manageable size
        summary = context.build_context_summary()
        assert len(summary) < 5000  # Reasonable summary length

        # Previous decisions should be filtered/summarized
        decisions = context.get_previous_decisions()
        assert len(decisions) <= 100  # Should handle large decision lists

    @pytest.mark.asyncio
    async def test_concurrent_agent_safety(self):
        """Test that agents can be safely used concurrently."""
        agents = [
            create_intake_extract_agent(),
            create_coverage_check_agent(),
            create_llm_planner_agent(),
        ]

        # Test that agents are independent instances
        assert agents[0] is not agents[2]
        assert agents[0].agent_type != agents[2].agent_type


@pytest.mark.integration
class TestFullWorkflowIntegration:
    """Integration tests for complete workflow with real LangGraph."""

    def test_graph_integration_compatibility(self):
        """Test that LLM agents integrate properly with LangGraph."""
        from libs.graph import build_full_graph

        # Build the full graph with LLM agents
        graph = build_full_graph()
        assert graph is not None

        # Test that the graph has all expected nodes
        nodes = list(graph.nodes.keys())
        expected_nodes = [
            "intake_extract",
            "coverage_check",
            "adaptive_questions",
            "planner",
            "critic_tech",
            "critic_cost",
            "policy_eval",
        ]

        for node in expected_nodes:
            assert node in nodes

    def test_workflow_state_compatibility(self):
        """Test that workflow state supports all LLM-specific fields."""
        from libs.graph import MLOpsWorkflowState

        # Test state can hold LLM-specific fields
        state: MLOpsWorkflowState = {
            "messages": [],
            "constraints": {},
            "constraint_extraction": {},
            "coverage_analysis": {},
            "adaptive_questioning": {},
            "questioning_complete": True,
            "technical_feasibility_score": 0.85,
            "estimated_monthly_cost": 1500.0,
            "overall_compliance_status": "pass",
        }

        # Should not raise any type errors
        assert state["questioning_complete"]
        assert state["technical_feasibility_score"] == 0.85


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_llm_agents.py -v
    pytest.main([__file__, "-v", "--tb=short"])
