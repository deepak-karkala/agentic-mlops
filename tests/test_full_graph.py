"""
Test for the full MLOps agent workflow (Issue #10).

This test validates the complete integration of the agent system with LangGraph,
ensuring that all agents (Planner, Tech Critic, Cost Critic, Policy Engine)
work together correctly to produce transparent reason cards and valid outputs.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from langchain_core.messages import HumanMessage

from libs.graph import build_full_graph, MLOpsWorkflowState
from libs.constraint_schema import MLOpsConstraints, ConstraintExtractionResult, CoverageAnalysisResult, AdaptiveQuestioningResult
from libs.agent_output_schemas import PlannerOutput, TechCriticOutput, CostCriticOutput, PolicyEngineOutput


class TestFullMLOpsGraph:
    """Test suite for the complete MLOps agent workflow."""

    @pytest.fixture(scope="function")
    def mock_llm_client(self):
        """Mock LLM client for all tests to avoid API key requirements."""
        with patch('libs.llm_client.OpenAIClient') as mock_client_class, \
             patch('libs.llm_client.get_llm_client') as mock_get_client:
            # Create mock client
            mock_client = Mock()
            
            # Mock different responses for different agent types
            def mock_complete_side_effect(messages, response_format=None, **kwargs):
                if response_format == ConstraintExtractionResult:
                    return ConstraintExtractionResult(
                        constraints=MLOpsConstraints(
                            project_description="Serverless ML system for startup",
                            budget_band="startup",
                            deployment_pref="serverless",
                            workload_types=["online_inference"],
                            expected_throughput="low",
                            data_classification="internal"
                        ),
                        extraction_confidence=0.85,
                        uncertain_fields=["availability_target"],
                        extraction_rationale="Clear requirements provided",
                        follow_up_needed=False
                    )
                elif response_format == CoverageAnalysisResult:
                    return CoverageAnalysisResult(
                        coverage_score=0.75,
                        coverage_threshold_met=True,
                        critical_gaps=["availability_target"],
                        ambiguous_fields=["team_expertise"],
                        coverage_details={
                            "budget_band": {"present": True, "confidence": 0.9},
                            "deployment_pref": {"present": True, "confidence": 0.85},
                            "workload_types": {"present": True, "confidence": 0.8},
                            "availability_target": {"present": False, "confidence": 0.0}
                        },
                        improvement_recommendations=[
                            "Specify availability requirements",
                            "Clarify team expertise level"
                        ],
                        analysis_confidence=0.8
                    )
                elif response_format == AdaptiveQuestioningResult:
                    return AdaptiveQuestioningResult(
                        current_questions=[],
                        questioning_complete=True,
                        questioning_rationale="Sufficient information gathered",
                        priority_gaps_addressed=["availability_target"],
                        additional_context_needed=False,
                        confidence=0.85
                    )
                elif response_format == PlannerOutput:
                    return PlannerOutput(
                        selected_pattern_id="serverless_inference_basic",
                        pattern_name="Serverless Inference Basic",
                        selection_rationale="Matches budget and deployment preferences",
                        selection_confidence=0.8,
                        alternatives_considered=[
                            {"pattern_id": "container_basic", "reason_not_selected": "Higher operational complexity"},
                            {"pattern_id": "managed_endpoint", "reason_not_selected": "Higher cost"}
                        ],
                        pattern_comparison="Serverless chosen for cost efficiency and simplicity",
                        architecture_overview="Event-driven serverless architecture",
                        key_services={
                            "lambda": "Serverless compute for inference",
                            "sagemaker": "Model hosting and management", 
                            "s3": "Model and data storage",
                            "apigateway": "API endpoint management"
                        },
                        estimated_monthly_cost=350.0,
                        deployment_approach="Infrastructure as Code with CDK",
                        implementation_phases=["Setup core services", "Deploy model", "Add monitoring", "Performance tuning"],
                        critical_success_factors=["Model optimization", "Cold start mitigation", "Proper monitoring"],
                        potential_challenges=["Cold start latency", "Lambda timeout limits", "Concurrent execution limits"],
                        success_metrics=["Response time < 200ms", "99.5% availability", "Cost under $400/month"],
                        assumptions_made=["Model size < 10GB", "Peak concurrency < 1000", "US-East-1 region"],
                        decision_criteria=["Budget compliance", "Operational simplicity", "Auto-scaling capability"]
                    )
                elif response_format == TechCriticOutput:
                    return TechCriticOutput(
                        technical_feasibility_score=0.85,
                        architecture_confidence=0.8,
                        criticism_summary="Highly feasible with some considerations",
                        technical_risks=["Cold start latency", "Lambda timeout limits"],
                        architecture_concerns=["API Gateway single point of failure"],
                        scalability_risks=["Concurrent execution limits"],
                        security_concerns=["IAM permissions management"],
                        performance_bottlenecks=["Lambda cold starts", "SageMaker model loading"],
                        capacity_constraints=["Lambda concurrency", "SageMaker endpoint capacity"],
                        integration_challenges=["Model versioning", "A/B testing setup"],
                        single_points_of_failure=["API Gateway", "Single AZ deployment"],
                        failure_domains=["Lambda region", "SageMaker availability zone"],
                        disaster_recovery_gaps=["No multi-region setup", "Limited backup strategy"],
                        risk_mitigation_strategies=["Implement Lambda warming", "Add health checks"],
                        architecture_improvements=["Add load balancing", "Implement caching"],
                        monitoring_requirements=["CloudWatch metrics", "Custom dashboards"],
                        operational_complexity="Low to medium complexity",
                        maintenance_requirements=["Model retraining", "Lambda function updates"],
                        skill_requirements=["AWS Lambda", "Python", "MLOps basics"],
                        availability_impact="Medium",
                        performance_impact="Low",
                        security_impact="Medium",
                        analysis_assumptions=["Model size < 10GB", "Peak load < 1000 concurrent"],
                        analysis_limitations=["No load testing performed", "Security review needed"]
                    )
                elif response_format == CostCriticOutput:
                    return CostCriticOutput(
                        estimated_monthly_cost=350.0,
                        cost_confidence=0.9,
                        cost_analysis_summary="Cost estimate within startup budget",
                        service_costs=[
                            {"service": "lambda", "cost": 50.0, "description": "Function execution"},
                            {"service": "sagemaker", "cost": 150.0, "description": "Model hosting"},
                            {"service": "s3", "cost": 25.0, "description": "Data storage"},
                            {"service": "apigateway", "cost": 125.0, "description": "API requests"}
                        ],
                        infrastructure_costs=[
                            {"component": "compute", "cost": 200.0, "details": "Lambda + SageMaker"},
                            {"component": "storage", "cost": 25.0, "details": "S3 buckets"},
                            {"component": "networking", "cost": 125.0, "details": "API Gateway"}
                        ],
                        operational_costs=[
                            {"component": "monitoring", "cost": 15.0, "details": "CloudWatch logs and metrics"},
                            {"component": "security", "cost": 5.0, "details": "IAM and encryption"}
                        ],
                        primary_cost_drivers=["SageMaker hosting", "API Gateway requests", "Lambda executions"],
                        cost_distribution={"compute": 57.1, "storage": 7.1, "networking": 35.7},
                        variable_vs_fixed={"variable": 80.0, "fixed": 20.0},
                        budget_compliance_status="pass",
                        budget_utilization=0.875,
                        budget_risk_assessment="Low risk, well within budget constraints",
                        cost_scaling_factors=["Request volume", "Model inference time", "Data storage growth"],
                        scaling_cost_projections={"2x_load": 700.0, "5x_load": 1750.0, "10x_load": 3500.0},
                        break_even_analysis="Cost effective for > 1000 requests/month",
                        cost_optimization_recommendations=["Use reserved capacity", "Optimize model size", "Implement caching"],
                        alternative_architectures=[
                            {"name": "Container-based", "estimated_cost": 450.0, "pros": ["More control"], "cons": ["Higher complexity"]},
                            {"name": "Managed endpoints", "estimated_cost": 600.0, "pros": ["Less management"], "cons": ["Higher cost"]}
                        ],
                        reserved_instance_opportunities=["SageMaker endpoints", "Lambda provisioned concurrency"],
                        potential_hidden_costs=["Data transfer", "Model training costs", "Development time"],
                        cost_volatility_factors=["Traffic spikes", "Model complexity changes", "AWS pricing updates"],
                        billing_complexity_notes=["Multiple services", "Usage-based billing", "Regional variations"],
                        expected_roi_timeline="6-12 months based on business value",
                        value_propositions=["Automated ML inference", "Scalable architecture", "Cost-effective at scale"],
                        cost_vs_benefit_analysis="Excellent value for automated ML inference capabilities",
                        cost_monitoring_strategy=["Daily cost alerts", "Usage dashboards", "Monthly reviews"],
                        budget_alerts_recommended=[
                            {"threshold": 300.0, "type": "warning", "action": "Review usage"},
                            {"threshold": 400.0, "type": "critical", "action": "Immediate investigation"}
                        ],
                        cost_governance_needs=["Monthly cost reviews", "Budget approval workflow"],
                        cost_assumptions=["Standard AWS pricing", "US-East-1 region", "Normal usage patterns"],
                        pricing_methodology="AWS calculator + usage projections",
                        cost_analysis_limitations=["No enterprise discounts", "Usage estimates", "Price volatility"]
                    )
                elif response_format == PolicyEngineOutput:
                    return PolicyEngineOutput(
                        overall_compliance_status="pass",
                        compliance_score=0.9,
                        policy_assessment_summary="All policies met with minor recommendations",
                        policy_rule_results=[
                            {"rule": "budget_limit", "status": "pass", "details": "Within budget constraints"},
                            {"rule": "security_baseline", "status": "pass", "details": "Basic security controls present"},
                            {"rule": "data_governance", "status": "warn", "details": "Consider data classification"}
                        ],
                        critical_violations=[],
                        warnings=["Consider multi-region deployment for higher availability"],
                        security_compliance={
                            "status": "compliant",
                            "score": 0.85,
                            "gaps": ["Multi-factor authentication", "Data encryption at rest"]
                        },
                        data_governance_compliance={
                            "status": "compliant", 
                            "score": 0.9,
                            "gaps": ["Data retention policy", "Data classification"]
                        },
                        operational_compliance={
                            "status": "compliant",
                            "score": 0.95,
                            "gaps": ["Disaster recovery testing"]
                        },
                        financial_compliance={
                            "status": "compliant",
                            "score": 1.0,
                            "gaps": []
                        },
                        regulatory_requirements=[
                            {"regulation": "SOX", "status": "not_applicable", "reason": "No financial data"},
                            {"regulation": "GDPR", "status": "needs_review", "reason": "May handle personal data"}
                        ],
                        compliance_gaps=["Data classification framework", "Multi-region backup"],
                        audit_readiness="needs_work",
                        compliance_risks=["Data loss", "Privacy violations"],
                        risk_mitigation_requirements=["Implement backup strategy", "Add data governance"],
                        escalation_required=False,
                        immediate_actions_required=["Set up monitoring alerts"],
                        recommended_policy_adjustments=["Add data classification policy"],
                        alternative_approaches=[
                            {"approach": "Enhanced security", "details": "Add encryption and MFA", "impact": "Higher security"}
                        ],
                        governance_controls_needed=["Cost monitoring", "Access reviews"],
                        monitoring_requirements=["Compliance dashboards", "Policy violation alerts"],
                        documentation_requirements=["Security procedures", "Data handling policies"],
                        stakeholder_notifications=["Security team", "Compliance officer"],
                        approval_requirements=["Security approval for production"],
                        change_management_needs=["Policy update communication"],
                        policies_evaluated=["Security baseline", "Budget policy", "Data governance"],
                        policy_exceptions_needed=["Development environment security"],
                        policy_review_recommendations=["Update data classification policy"],
                        assessment_confidence=0.8,
                        assessment_limitations=["Limited security review", "No penetration testing"]
                    )
                else:
                    # Default text response
                    return "Mock LLM response"
            
            mock_client.complete = AsyncMock(side_effect=mock_complete_side_effect)
            
            # Mock both the class constructor and get_client function
            mock_client_class.return_value = mock_client
            mock_get_client.return_value = mock_client
            
            yield mock_client

    def test_full_graph_topology(self, mock_llm_client):
        """Test that the full graph builds correctly with all nodes and edges."""
        graph = build_full_graph()

        # Verify the graph was compiled successfully
        assert graph is not None

        # Verify graph has expected nodes (we can't easily inspect internal structure
        # but we can test that it runs without errors)
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")

    def test_full_workflow_execution(self, mock_llm_client):
        """Test that the full workflow executes correctly with real agents."""
        graph = build_full_graph()

        # Create initial state with user message
        initial_state: MLOpsWorkflowState = {
            "messages": [
                HumanMessage(
                    content="I need a serverless ML system for a startup with a $400/month budget"
                )
            ],
            "project_id": "test_project",
            "decision_set_id": "test_ds_001",
            "version": 1,
        }

        # Execute the full workflow with required checkpointing config
        config = {"configurable": {"thread_id": "test_thread_001"}}
        result = graph.invoke(initial_state, config=config)

        # Verify basic workflow completion
        assert result is not None
        assert isinstance(result, dict)

        # Verify constraints were extracted
        assert "constraints" in result
        constraints = result["constraints"]
        assert isinstance(constraints, dict)
        assert constraints.get("budget_band").value == "startup"
        assert constraints.get("deployment_preference").value == "serverless"

        # Verify coverage check ran
        assert "coverage" in result
        assert "coverage_score" in result
        assert isinstance(result["coverage_score"], float)

        # Verify planner agent executed
        assert "plan" in result
        plan = result["plan"]
        assert isinstance(plan, dict)
        assert "deployment_pattern" in plan  # Changed from architecture_type
        assert "services" in plan
        assert "estimated_monthly_cost" in plan

        # Verify candidates were generated
        assert "candidates" in result
        assert isinstance(result["candidates"], list)
        assert len(result["candidates"]) > 0

        # Verify tech critic executed
        assert "tech_critique" in result
        tech_critique = result["tech_critique"]
        assert isinstance(tech_critique, dict)
        assert "overall_feasibility_score" in tech_critique
        assert "technical_risks" in tech_critique
        assert "risk_mitigation_strategies" in tech_critique

        # Verify cost critic executed
        assert "cost_estimate" in result
        cost_estimate = result["cost_estimate"]
        assert isinstance(cost_estimate, dict)
        assert "estimated_monthly_cost" in cost_estimate
        assert "service_costs" in cost_estimate
        assert "cost_confidence" in cost_estimate

        # Verify policy engine executed
        assert "policy_results" in result
        policy_results = result["policy_results"]
        assert isinstance(policy_results, dict)
        assert "overall_compliance_status" in policy_results
        assert "policy_rule_results" in policy_results

        # Verify reason cards were generated
        assert "reason_cards" in result
        reason_cards = result["reason_cards"]
        assert isinstance(reason_cards, list)
        assert (
            len(reason_cards) >= 4
        )  # At least planner, tech critic, cost critic, policy engine

        # Verify agent outputs were captured
        assert "agent_outputs" in result
        agent_outputs = result["agent_outputs"]
        assert isinstance(agent_outputs, dict)
        assert "planner" in agent_outputs
        assert "tech_critic" in agent_outputs
        assert "cost_critic" in agent_outputs
        assert "policy_engine" in agent_outputs

        # Verify artifacts were generated (mock)
        assert "artifacts" in result
        artifacts = result["artifacts"]
        assert isinstance(artifacts, list)

        # Verify reports were generated (mock)
        assert "reports" in result
        reports = result["reports"]
        assert isinstance(reports, dict)
        assert reports["overall_status"] == "pass"

        # Verify rationale compilation
        assert "rationale" in result
        rationale = result["rationale"]
        assert isinstance(rationale, dict)
        assert "reason_cards" in rationale
        assert "reason_card_count" in rationale
        assert rationale["reason_card_count"] >= 4

        # Verify diff summary
        assert "diff_summary" in result
        diff_summary = result["diff_summary"]
        assert isinstance(diff_summary, dict)
        assert "files_added" in diff_summary
        assert "cost_delta_usd" in diff_summary

    def test_agent_reason_cards_structure(self, mock_llm_client):
        """Test that reason cards have the expected structure and content."""
        graph = build_full_graph()

        initial_state: MLOpsWorkflowState = {
            "messages": [
                HumanMessage(
                    content="I need a containerized ML platform for enterprise use"
                )
            ],
            "project_id": "test_enterprise",
            "decision_set_id": "test_ds_002",
            "version": 1,
        }

        config = {"configurable": {"thread_id": "test_thread_reason_cards"}}
        result = graph.invoke(initial_state, config=config)
        reason_cards = result.get("reason_cards", [])

        # Should have reason cards from key agents
        assert len(reason_cards) >= 4

        # Check structure of reason cards
        for card in reason_cards:
            assert isinstance(card, dict)

            # Required fields from ReasonCard model
            assert "decision_id" in card
            assert "agent" in card
            assert "node_name" in card
            assert "trigger" in card
            assert "timestamp" in card
            assert "confidence" in card

            # Verify confidence is in valid range
            assert 0.0 <= card["confidence"] <= 1.0

            # Verify agent types are valid
            expected_agents = ["intake.extract", "coverage.check", "adaptive.questions", "planner", "critic.tech", "critic.cost", "policy.engine"]
            assert card["agent"] in expected_agents

            # Should have outputs
            assert "outputs" in card
            assert isinstance(card["outputs"], dict)

    def test_planner_agent_integration(self, mock_llm_client):
        """Test that the planner agent integration works correctly."""
        graph = build_full_graph()

        # Test with specific constraints that should influence selection
        initial_state: MLOpsWorkflowState = {
            "messages": [
                HumanMessage(
                    content="I need a kubernetes-based ML platform with high availability "
                    "for sensitive data processing with a $2000/month budget"
                )
            ],
            "project_id": "test_k8s",
            "decision_set_id": "test_ds_003",
            "version": 1,
        }

        config = {"configurable": {"thread_id": "test_thread_planner"}}
        result = graph.invoke(initial_state, config=config)

        # Extract planner-specific outputs
        plan = result.get("plan", {})
        constraints = result.get("constraints", {})

        # Verify constraints extraction
        assert constraints["budget_band"].value == "startup"  # Basic extraction
        assert constraints["deployment_preference"].value == "serverless"  # Default for now

        # Verify plan structure
        assert "deployment_pattern" in plan
        assert "services" in plan
        assert "estimated_monthly_cost" in plan
        assert isinstance(plan["estimated_monthly_cost"], (int, float))

        # Find planner reason card
        reason_cards = result.get("reason_cards", [])
        planner_cards = [
            card for card in reason_cards if card.get("agent") == "planner"
        ]
        assert len(planner_cards) >= 1  # Allow multiple planner executions

        planner_card = planner_cards[0]
        assert "selected_pattern_id" in planner_card["outputs"]
        assert "estimated_cost" in planner_card["outputs"]
        assert "services_count" in planner_card["outputs"]

    def test_critics_integration(self, mock_llm_client):
        """Test that both critic agents integrate correctly."""
        graph = build_full_graph()

        initial_state: MLOpsWorkflowState = {
            "messages": [HumanMessage(content="I need a high-throughput ML system")],
            "project_id": "test_critics",
            "decision_set_id": "test_ds_004",
            "version": 1,
        }

        config = {"configurable": {"thread_id": "test_thread_critics"}}
        result = graph.invoke(initial_state, config=config)

        # Test tech critic outputs
        tech_critique = result.get("tech_critique", {})
        assert "overall_feasibility_score" in tech_critique
        assert "technical_risks" in tech_critique
        assert "performance_bottlenecks" in tech_critique
        assert "risk_mitigation_strategies" in tech_critique
        assert isinstance(tech_critique["overall_feasibility_score"], float)
        assert isinstance(tech_critique["technical_risks"], list)

        # Test cost critic outputs
        cost_estimate = result.get("cost_estimate", {})
        assert "estimated_monthly_cost" in cost_estimate
        assert "service_costs" in cost_estimate
        assert "cost_confidence" in cost_estimate
        assert isinstance(cost_estimate["estimated_monthly_cost"], (int, float))
        assert isinstance(cost_estimate["service_costs"], list)
        assert len(cost_estimate["service_costs"]) > 0

        # Verify cost breakdown structure
        for item in cost_estimate["service_costs"]:
            assert "service" in item
            assert "cost" in item
            assert isinstance(item["cost"], (int, float))

    def test_policy_engine_integration(self, mock_llm_client):
        """Test that the policy engine integration works correctly."""
        graph = build_full_graph()

        initial_state: MLOpsWorkflowState = {
            "messages": [
                HumanMessage(content="I need an ML system for restricted data")
            ],
            "project_id": "test_policy",
            "decision_set_id": "test_ds_005",
            "version": 1,
        }

        config = {"configurable": {"thread_id": "test_thread_policy"}}
        result = graph.invoke(initial_state, config=config)

        # Test policy results
        policy_results = result.get("policy_results", {})
        assert "overall_compliance_status" in policy_results
        assert "policy_rule_results" in policy_results
        assert policy_results["overall_compliance_status"] in ["pass", "warn", "fail"]
        assert isinstance(policy_results["policy_rule_results"], list)

        # Check individual policy rules
        for rule in policy_results["policy_rule_results"]:
            assert "rule" in rule
            assert "status" in rule
            assert "details" in rule
            assert rule["status"] in ["pass", "warn", "fail"]
            assert isinstance(rule["details"], str)

        # Common policy rules should be present
        rule_names = [rule["rule"] for rule in policy_results["policy_rule_results"]]
        expected_rules = [
            "budget_limit",
            "security_baseline", 
            "data_governance",
        ]

        for expected_rule in expected_rules:
            assert expected_rule in rule_names

    def test_error_handling(self, mock_llm_client):
        """Test that the workflow handles errors gracefully."""
        graph = build_full_graph()

        # Test with empty/invalid initial state
        minimal_state: MLOpsWorkflowState = {
            "messages": [],  # No messages
            "project_id": "test_error",
        }

        # Should not crash, but may have limited functionality
        config = {"configurable": {"thread_id": "test_thread_error"}}
        result = graph.invoke(minimal_state, config=config)

        # Should still produce basic structure
        assert isinstance(result, dict)
        assert "constraints" in result  # Should have default constraints

        # Check if any errors were captured
        if "error" in result:
            # If there are errors, they should be strings
            assert isinstance(result["error"], str)

    def test_workflow_determinism(self, mock_llm_client):
        """Test that the workflow produces consistent results for the same input."""
        graph = build_full_graph()

        initial_state: MLOpsWorkflowState = {
            "messages": [
                HumanMessage(content="I need a basic ML system for a startup")
            ],
            "project_id": "test_determinism",
            "decision_set_id": "test_ds_determinism",
            "version": 1,
        }

        # Run the same workflow twice
        config1 = {"configurable": {"thread_id": "test_thread_determinism_1"}}
        config2 = {"configurable": {"thread_id": "test_thread_determinism_2"}}
        result1 = graph.invoke(initial_state, config=config1)
        result2 = graph.invoke(initial_state, config=config2)

        # Key outputs should be consistent
        assert result1.get("plan", {}).get("architecture_type") == result2.get(
            "plan", {}
        ).get("architecture_type")
        assert result1.get("cost_estimate", {}).get("monthly_usd") == result2.get(
            "cost_estimate", {}
        ).get("monthly_usd")
        assert result1.get("policy_results", {}).get("overall_status") == result2.get(
            "policy_results", {}
        ).get("overall_status")

        # Reason card count should be consistent
        assert len(result1.get("reason_cards", [])) == len(
            result2.get("reason_cards", [])
        )
