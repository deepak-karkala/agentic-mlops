"""
Integration tests for complete LLM-powered workflow

Tests the end-to-end transformation from natural language to complete MLOps plan
using the LLM-powered agent chain with realistic scenarios.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from libs.graph import MLOpsWorkflowState
from libs.constraint_schema import (
    MLOpsConstraints,
    ConstraintExtractionResult,
    CoverageAnalysisResult,
    AdaptiveQuestioningResult,
    AdaptiveQuestion,
)
from libs.agent_output_schemas import PlannerOutput, TechCriticOutput


@pytest.mark.integration
class TestCompleteWorkflowTransformation:
    """Test complete workflow transformation scenarios."""

    @pytest.fixture
    def fraud_detection_input(self):
        """Fraud detection system user input."""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": "I need to build a real-time fraud detection system for credit card transactions. We process about 100,000 transactions per day with peaks up to 200,000. Response time must be under 200ms. We need PCI-DSS compliance and 99.95% availability. Budget is around $2000 per month.",
                }
            ],
            "project_id": "fraud-detection-test",
            "decision_set_id": "fraud-test-001",
            "version": 1,
        }

    @pytest.fixture
    def recommendation_system_input(self):
        """E-commerce recommendation system input."""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": "Build a product recommendation engine for our e-commerce platform. We have 50K daily active users, need personalized recommendations in under 500ms, and want to start with a $500/month budget. Data includes user behavior, product catalogs, and purchase history.",
                }
            ],
            "project_id": "recommendation-test",
            "decision_set_id": "rec-test-001",
            "version": 1,
        }

    @pytest.fixture
    def batch_analytics_input(self):
        """Batch analytics pipeline input."""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": "We need a daily batch analytics pipeline to process customer data for insights. Process about 10GB of data daily, generate reports for business teams, and handle sensitive customer information. Looking for a cost-effective solution under $300/month.",
                }
            ],
            "project_id": "analytics-test",
            "decision_set_id": "analytics-test-001",
            "version": 1,
        }

    def create_mock_extraction_result(self, project_type: str):
        """Create mock constraint extraction result."""
        if project_type == "fraud_detection":
            constraints = MLOpsConstraints(
                project_description="Real-time fraud detection system for credit card transactions",
                budget_band="enterprise",
                deployment_preference="containers",
                workload_types=["online_inference"],
                expected_throughput="high",
                latency_requirements_ms=200,
                data_classification="restricted",
                compliance_requirements=["PCI-DSS"],
                availability_target=99.95,
                regions=["us-east-1"],
                model_types=["classification", "anomaly_detection"],
            )
            return ConstraintExtractionResult(
                constraints=constraints,
                extraction_confidence=0.89,
                uncertain_fields=["team_expertise"],
                extraction_rationale="Clear requirements for high-throughput fraud detection with compliance",
                follow_up_needed=False,
            )
        elif project_type == "recommendation":
            constraints = MLOpsConstraints(
                project_description="Product recommendation engine for e-commerce platform",
                budget_band="startup",
                deployment_preference="serverless",
                workload_types=["online_inference"],
                expected_throughput="medium",
                latency_requirements_ms=500,
                data_classification="internal",
                regions=["us-east-1"],
                model_types=["recommendation", "collaborative_filtering"],
            )
            return ConstraintExtractionResult(
                constraints=constraints,
                extraction_confidence=0.82,
                uncertain_fields=["availability_target", "compliance_requirements"],
                extraction_rationale="E-commerce recommendation system with moderate traffic",
                follow_up_needed=True,
            )
        else:  # batch_analytics
            constraints = MLOpsConstraints(
                project_description="Daily batch analytics pipeline for customer insights",
                budget_band="startup",
                deployment_preference="serverless",
                workload_types=["batch_training", "data_processing"],
                expected_throughput="low",
                data_classification="sensitive",
                regions=["us-east-1"],
                model_types=["analytics", "insights"],
            )
            return ConstraintExtractionResult(
                constraints=constraints,
                extraction_confidence=0.75,
                uncertain_fields=["compliance_requirements", "availability_target"],
                extraction_rationale="Batch analytics with sensitive data handling needs",
                follow_up_needed=True,
            )

    def create_mock_coverage_result(self, coverage_score: float):
        """Create mock coverage analysis result."""
        if coverage_score >= 0.75:
            return CoverageAnalysisResult(
                coverage_score=coverage_score,
                missing_critical_fields=[],
                missing_optional_fields=["team_size", "operational_preferences"],
                ambiguous_fields=[],
                coverage_threshold_met=True,
                recommendations=[
                    "Consider specifying team size for deployment complexity guidance"
                ],
            )
        else:
            return CoverageAnalysisResult(
                coverage_score=coverage_score,
                missing_critical_fields=["availability_target"],
                missing_optional_fields=["team_expertise", "integration_requirements"],
                ambiguous_fields=["deployment_preference"],
                coverage_threshold_met=False,
                recommendations=[
                    "Clarify availability requirements",
                    "Specify deployment complexity preferences",
                ],
            )

    def create_mock_questioning_result(self, needs_questions: bool):
        """Create mock adaptive questioning result."""
        if needs_questions:
            questions = [
                AdaptiveQuestion(
                    question_id="availability_req",
                    question_text="What availability level do you need? Financial systems typically require 99.9% or higher.",
                    field_targets=["availability_target"],
                    priority="high",
                    question_type="choice",
                    choices=["99.9%", "99.95%", "99.99%"],
                ),
                AdaptiveQuestion(
                    question_id="deployment_complexity",
                    question_text="What's your team's comfort level with deployment complexity?",
                    field_targets=["team_expertise"],
                    priority="medium",
                    question_type="choice",
                    choices=[
                        "Simple (managed services)",
                        "Moderate (containers)",
                        "Advanced (Kubernetes)",
                    ],
                ),
            ]
            return AdaptiveQuestioningResult(
                questions=questions,
                questioning_complete=False,
                current_coverage=0.65,
                target_coverage=0.75,
                questioning_rationale="Need clarification on availability and deployment preferences",
            )
        else:
            return AdaptiveQuestioningResult(
                questions=[],
                questioning_complete=True,
                current_coverage=0.85,
                target_coverage=0.75,
                questioning_rationale="Coverage threshold met, proceeding with planning",
            )

    def create_mock_planner_result(self, project_type: str):
        """Create mock planner output."""
        if project_type == "fraud_detection":
            return PlannerOutput(
                selected_pattern_id="realtime_inference_enterprise",
                pattern_name="Real-time ML Inference (Enterprise)",
                selection_confidence=0.91,
                selection_rationale="High-performance real-time inference with PCI compliance and enterprise-grade availability",
                alternatives_considered=[
                    {
                        "pattern_id": "serverless_inference",
                        "reason": "Lower cost but potential cold start latency issues",
                    },
                    {
                        "pattern_id": "batch_processing",
                        "reason": "Not suitable for real-time requirements",
                    },
                ],
                pattern_comparison="Enterprise pattern selected over serverless for guaranteed low latency and compliance controls",
                architecture_overview="Container-based inference endpoints with dedicated VPC, auto-scaling, and comprehensive monitoring",
                key_services={
                    "inference": "Amazon SageMaker Real-time Endpoints",
                    "data": "Amazon RDS (encrypted)",
                    "cache": "Amazon ElastiCache",
                    "monitoring": "CloudWatch + X-Ray",
                },
                estimated_monthly_cost=1850.0,
                deployment_approach="Blue-green deployment with automated rollback",
                implementation_phases=[
                    "Infrastructure and VPC setup",
                    "Model deployment and testing",
                    "Compliance validation and monitoring",
                ],
                critical_success_factors=[
                    "PCI-DSS compliance validation",
                    "Sub-200ms P99 latency",
                    "99.95% availability target",
                ],
                potential_challenges=[
                    "Complex compliance setup",
                    "Latency optimization under high load",
                ],
                success_metrics=[
                    "Response latency < 200ms (P99)",
                    "System availability > 99.95%",
                    "PCI audit readiness",
                ],
                assumptions_made=[
                    "Team has containerization experience",
                    "Compliance team available for consultation",
                ],
                decision_criteria=[
                    "Latency requirements",
                    "Compliance mandates",
                    "Availability targets",
                ],
            )
        elif project_type == "recommendation":
            return PlannerOutput(
                selected_pattern_id="serverless_inference_startup",
                pattern_name="Serverless ML Inference (Startup)",
                selection_confidence=0.83,
                selection_rationale="Cost-effective serverless approach suitable for startup budget and moderate traffic",
                alternatives_considered=[
                    {
                        "pattern_id": "container_inference",
                        "reason": "Higher operational overhead for startup team",
                    },
                    {
                        "pattern_id": "batch_recommendations",
                        "reason": "Not suitable for real-time personalization",
                    },
                ],
                pattern_comparison="Serverless chosen for cost optimization and automatic scaling",
                architecture_overview="Lambda-based inference with API Gateway, DynamoDB for features, and S3 for model storage",
                key_services={
                    "inference": "AWS Lambda",
                    "api": "API Gateway",
                    "data": "DynamoDB",
                    "storage": "Amazon S3",
                },
                estimated_monthly_cost=450.0,
                deployment_approach="Serverless framework with CI/CD pipeline",
                implementation_phases=[
                    "Serverless infrastructure setup",
                    "Model deployment and API development",
                    "Performance testing and optimization",
                ],
                critical_success_factors=[
                    "Cold start optimization",
                    "Cost management within budget",
                    "API response time < 500ms",
                ],
                potential_challenges=[
                    "Lambda cold start latency",
                    "Managing state in serverless",
                ],
                success_metrics=[
                    "API response time < 500ms",
                    "Monthly cost < $500",
                    "99% API availability",
                ],
                assumptions_made=[
                    "Moderate traffic patterns",
                    "Basic serverless experience",
                ],
                decision_criteria=[
                    "Cost constraints",
                    "Operational simplicity",
                    "Scalability needs",
                ],
            )
        else:  # batch_analytics
            return PlannerOutput(
                selected_pattern_id="batch_processing_startup",
                pattern_name="Batch Processing Pipeline (Startup)",
                selection_confidence=0.79,
                selection_rationale="Cost-effective batch processing for daily analytics with sensitive data handling",
                alternatives_considered=[
                    {
                        "pattern_id": "real_time_streaming",
                        "reason": "Unnecessary complexity for daily batch requirements",
                    },
                    {
                        "pattern_id": "managed_analytics",
                        "reason": "Higher cost than budget allows",
                    },
                ],
                pattern_comparison="Batch processing selected for cost efficiency and simplicity",
                architecture_overview="S3-based data lake with Lambda triggers, Glue for ETL, and Athena for querying",
                key_services={
                    "storage": "Amazon S3",
                    "processing": "AWS Glue",
                    "query": "Amazon Athena",
                    "orchestration": "AWS Lambda",
                },
                estimated_monthly_cost=280.0,
                deployment_approach="Infrastructure as Code with CloudFormation",
                implementation_phases=[
                    "Data lake setup and security configuration",
                    "ETL pipeline development and testing",
                    "Reporting and dashboard integration",
                ],
                critical_success_factors=[
                    "Data security and encryption",
                    "Processing completion within daily window",
                    "Cost optimization",
                ],
                potential_challenges=[
                    "Data quality and validation",
                    "Sensitive data handling compliance",
                ],
                success_metrics=[
                    "Daily processing completion < 4 hours",
                    "Data accuracy > 99.5%",
                    "Monthly cost < $300",
                ],
                assumptions_made=[
                    "Consistent daily data volume",
                    "Standard business reporting needs",
                ],
                decision_criteria=[
                    "Cost efficiency",
                    "Data security",
                    "Processing reliability",
                ],
            )

    def create_mock_tech_critic_result(self, project_type: str):
        """Create mock technical critic result."""
        if project_type == "fraud_detection":
            return TechCriticOutput(
                technical_feasibility_score=0.78,
                architecture_confidence=0.82,
                criticism_summary="Solid architecture for fraud detection with some scalability and compliance considerations",
                technical_risks=[
                    "High traffic spikes may exceed container capacity",
                    "PCI compliance configuration complexity",
                ],
                architecture_concerns=[
                    "Single region deployment creates availability risk",
                    "Database connection pooling under high load",
                ],
                scalability_risks=[
                    "Container auto-scaling lag during traffic spikes",
                    "Database performance at 200K+ TPS",
                ],
                security_concerns=[
                    "Network segmentation for PCI compliance",
                    "Encryption key management complexity",
                ],
                performance_bottlenecks=[
                    "Database query latency under high load",
                    "Model inference optimization needed",
                ],
                capacity_constraints=[
                    "Container memory limits for ML models",
                    "Database connection limits",
                ],
                integration_challenges=[
                    "Payment processor API integration",
                    "Compliance monitoring tool integration",
                ],
                single_points_of_failure=[
                    "Single RDS instance",
                    "Single availability zone deployment",
                ],
                failure_domains=[
                    "Database failure affects all inference",
                    "Container orchestration layer",
                ],
                disaster_recovery_gaps=[
                    "No multi-region failover",
                    "Backup and recovery testing needed",
                ],
                risk_mitigation_strategies=[
                    "Implement database clustering",
                    "Add multi-AZ deployment",
                    "Set up comprehensive monitoring",
                ],
                architecture_improvements=[
                    "Multi-region deployment for DR",
                    "Implement caching layer for performance",
                    "Add circuit breakers for resilience",
                ],
                monitoring_requirements=[
                    "Real-time performance metrics",
                    "PCI compliance monitoring",
                    "Fraud detection accuracy tracking",
                ],
                operational_complexity="High due to compliance requirements and performance demands",
                maintenance_requirements=[
                    "Regular security patching",
                    "Model retraining and deployment",
                    "Compliance audit preparation",
                ],
                skill_requirements=[
                    "Container orchestration expertise",
                    "PCI compliance knowledge",
                    "High-performance system optimization",
                ],
                availability_impact="High",
                performance_impact="Medium",
                security_impact="High",
                analysis_assumptions=[
                    "Team has DevOps expertise",
                    "Compliance team support available",
                ],
                analysis_limitations=[
                    "Specific traffic patterns not analyzed",
                    "Fraud model performance characteristics unknown",
                ],
            )
        else:
            return TechCriticOutput(
                technical_feasibility_score=0.85,
                architecture_confidence=0.87,
                criticism_summary="Well-suited serverless architecture with manageable complexity",
                technical_risks=["Cold start latency during traffic spikes"],
                architecture_concerns=[
                    "Lambda timeout limits for complex recommendations"
                ],
                scalability_risks=["DynamoDB read/write capacity management"],
                security_concerns=["API Gateway security configuration"],
                performance_bottlenecks=[
                    "Lambda cold starts",
                    "DynamoDB query performance",
                ],
                capacity_constraints=[
                    "Lambda concurrency limits",
                    "API Gateway rate limits",
                ],
                integration_challenges=["E-commerce platform API integration"],
                single_points_of_failure=["Single region deployment"],
                failure_domains=[
                    "Lambda function failures",
                    "DynamoDB service interruptions",
                ],
                disaster_recovery_gaps=["Cross-region replication not configured"],
                risk_mitigation_strategies=[
                    "Implement provisioned concurrency",
                    "Set up DynamoDB auto-scaling",
                ],
                architecture_improvements=[
                    "Add CloudFront for global performance",
                    "Implement recommendation caching",
                ],
                monitoring_requirements=[
                    "Lambda performance metrics",
                    "API response time monitoring",
                ],
                operational_complexity="Low to Medium - serverless reduces operational overhead",
                maintenance_requirements=[
                    "Model updates and deployment",
                    "Performance monitoring and optimization",
                ],
                skill_requirements=[
                    "Serverless development experience",
                    "NoSQL database optimization",
                ],
                availability_impact="Medium",
                performance_impact="Medium",
                security_impact="Low",
                analysis_assumptions=[
                    "Moderate traffic patterns",
                    "Standard e-commerce integration needs",
                ],
                analysis_limitations=[
                    "Specific recommendation algorithm not evaluated"
                ],
            )

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_fraud_detection_complete_workflow(
        self, mock_get_client, fraud_detection_input
    ):
        """Test complete workflow for fraud detection system."""
        # Set up mock LLM client responses for each agent (skip AdaptiveQuestions due to high coverage)
        mock_responses = [
            self.create_mock_extraction_result("fraud_detection"),  # IntakeExtractAgent
            self.create_mock_coverage_result(
                0.85
            ),  # CoverageCheckAgent (high coverage)
            self.create_mock_planner_result("fraud_detection"),  # PlannerAgent
            self.create_mock_tech_critic_result("fraud_detection"),  # TechCriticAgent
        ]

        mock_client = Mock()
        mock_client.complete = AsyncMock(side_effect=mock_responses)
        mock_get_client.return_value = mock_client

        # Execute workflow steps individually to test integration
        from libs.intake_extract_agent import create_intake_extract_agent
        from libs.coverage_check_agent import create_coverage_check_agent
        from libs.llm_planner_agent import create_llm_planner_agent
        from libs.llm_tech_critic_agent import create_llm_tech_critic_agent

        # Step 1: Constraint extraction
        intake_agent = create_intake_extract_agent()
        result1 = await intake_agent.execute(fraud_detection_input)

        assert result1.success
        assert "constraints" in result1.state_updates
        constraints = result1.state_updates["constraints"]
        assert (
            constraints["project_description"]
            == "Real-time fraud detection system for credit card transactions"
        )
        assert constraints["budget_band"] == "enterprise"
        assert "PCI-DSS" in constraints["compliance_requirements"]

        # Step 2: Coverage analysis
        coverage_state = {**fraud_detection_input, **result1.state_updates}
        coverage_agent = create_coverage_check_agent()
        result2 = await coverage_agent.execute(coverage_state)

        assert result2.success
        assert result2.state_updates["coverage_score"] == 0.85
        assert result2.state_updates["coverage_threshold_met"]

        # Step 3: Planning (skip questioning due to high coverage)
        planning_state = {
            **coverage_state,
            **result2.state_updates,
            "questioning_complete": True,
        }
        planner_agent = create_llm_planner_agent()
        result3 = await planner_agent.execute(planning_state)

        assert result3.success
        plan = result3.state_updates["plan"]
        assert plan["pattern_id"] == "realtime_inference_enterprise"
        assert plan["estimated_monthly_cost"] == 1850.0
        assert "PCI-DSS compliance validation" in plan["critical_success_factors"]

        # Step 4: Technical analysis
        tech_state = {**planning_state, **result3.state_updates}
        tech_critic = create_llm_tech_critic_agent()
        result4 = await tech_critic.execute(tech_state)

        assert result4.success
        tech_analysis = result4.state_updates["tech_critique"]
        assert tech_analysis["overall_feasibility_score"] == 0.78
        assert (
            "PCI compliance configuration complexity"
            in tech_analysis["technical_risks"]
        )

        # Verify context accumulation
        final_state = {**tech_state, **result4.state_updates}
        assert len(final_state.get("execution_order", [])) == 4
        assert len(final_state.get("reason_cards", [])) == 4

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_recommendation_system_with_questioning(
        self, mock_get_client, recommendation_system_input
    ):
        """Test recommendation system workflow with adaptive questioning."""
        # Set up mock responses including questioning round
        mock_responses = [
            self.create_mock_extraction_result("recommendation"),  # IntakeExtractAgent
            self.create_mock_coverage_result(0.65),  # CoverageCheckAgent (low coverage)
            self.create_mock_questioning_result(
                True
            ),  # AdaptiveQuestionsAgent (questions needed)
            # Simulated user responses would update constraints here
            self.create_mock_coverage_result(
                0.78
            ),  # CoverageCheckAgent (after user answers)
            self.create_mock_questioning_result(
                False
            ),  # AdaptiveQuestionsAgent (questioning complete)
            self.create_mock_planner_result("recommendation"),  # PlannerAgent
        ]

        mock_client = Mock()
        mock_client.complete = AsyncMock(side_effect=mock_responses)
        mock_get_client.return_value = mock_client

        from libs.intake_extract_agent import create_intake_extract_agent
        from libs.coverage_check_agent import create_coverage_check_agent
        from libs.adaptive_questions_agent import create_adaptive_questions_agent

        # Step 1: Constraint extraction
        intake_agent = create_intake_extract_agent()
        result1 = await intake_agent.execute(recommendation_system_input)

        assert result1.success
        constraints = result1.state_updates["constraints"]
        assert constraints["budget_band"] == "startup"
        assert constraints["deployment_preference"] == "serverless"

        # Step 2: Coverage analysis (low coverage)
        coverage_state = {**recommendation_system_input, **result1.state_updates}
        coverage_agent = create_coverage_check_agent()
        result2 = await coverage_agent.execute(coverage_state)

        assert result2.success
        assert result2.state_updates["coverage_score"] == 0.65
        assert not result2.state_updates["coverage_threshold_met"]

        # Step 3: Adaptive questioning (questions generated)
        questioning_state = {**coverage_state, **result2.state_updates}
        questions_agent = create_adaptive_questions_agent()
        result3 = await questions_agent.execute(questioning_state)

        assert result3.success
        assert len(result3.state_updates["current_questions"]) == 2
        assert not result3.state_updates["questioning_complete"]

        # Verify question quality
        questions = result3.state_updates["current_questions"]
        availability_q = next(
            q for q in questions if q["question_id"] == "availability_req"
        )
        assert availability_q["priority"] == "high"
        assert len(availability_q["choices"]) == 3

    @patch("libs.llm_agent_base.get_llm_client")
    async def test_batch_analytics_cost_optimization(
        self, mock_get_client, batch_analytics_input
    ):
        """Test batch analytics workflow focusing on cost optimization."""
        mock_responses = [
            self.create_mock_extraction_result("batch_analytics"),
            self.create_mock_planner_result("batch_analytics"),  # Only IntakeExtract and Planner are executed
        ]

        mock_client = Mock()
        mock_client.complete = AsyncMock(side_effect=mock_responses)
        mock_get_client.return_value = mock_client

        from libs.intake_extract_agent import create_intake_extract_agent
        from libs.llm_planner_agent import create_llm_planner_agent

        # Execute constraint extraction and planning
        intake_agent = create_intake_extract_agent()
        result1 = await intake_agent.execute(batch_analytics_input)

        planning_state = {
            **batch_analytics_input,
            **result1.state_updates,
            "coverage_score": 0.75,
            "questioning_complete": True,
        }

        planner_agent = create_llm_planner_agent()
        result2 = await planner_agent.execute(planning_state)

        assert result2.success
        plan = result2.state_updates["plan"]

        # Verify cost-optimized batch solution
        assert plan["pattern_id"] == "batch_processing_startup"
        assert plan["estimated_monthly_cost"] == 280.0  # Under $300 budget
        assert "Amazon S3" in plan["key_services"]["storage"]
        assert "AWS Glue" in plan["key_services"]["processing"]

        # Verify batch-specific considerations
        assert "Daily processing completion < 4 hours" in plan["success_metrics"]
        assert "Data security and encryption" in plan["critical_success_factors"]

    def test_workflow_state_compatibility(self):
        """Test that workflow state supports all LLM transformations."""
        # Test comprehensive state with all LLM fields
        complete_state: MLOpsWorkflowState = {
            "messages": [{"role": "user", "content": "Test ML system"}],
            "project_id": "test-project",
            "decision_set_id": "test-decision",
            "version": 1,
            # Constraint extraction fields
            "constraints": {"project_description": "Test system"},
            "constraint_extraction": {"confidence": 0.8},
            # Coverage analysis fields
            "coverage_score": 0.75,
            "coverage_analysis": {"threshold_met": True},
            # Adaptive questioning fields
            "questioning_complete": True,
            "questioning_history": [{"round": 1, "questions": 2}],
            "current_questions": [],
            # Planning fields
            "plan": {"pattern_id": "test_pattern", "cost": 1000.0},
            "planning_analysis": {"confidence": 0.85},
            # Technical analysis fields
            "tech_critique": {"feasibility_score": 0.8},
            "technical_feasibility_score": 0.8,
            "architecture_confidence": 0.85,
            # Cost analysis fields
            "cost_estimate": {"monthly_cost": 1000.0},
            "estimated_monthly_cost": 1000.0,
            "cost_confidence": 0.9,
            "budget_compliance_status": "pass",
            # Policy analysis fields
            "policy_validation": {"compliance_status": "pass"},
            "overall_compliance_status": "pass",
            "compliance_score": 0.95,
            "escalation_required": False,
            # Execution tracking
            "execution_order": ["intake_extract", "coverage_check", "planner"],
            "reason_cards": [{"agent": "test", "confidence": 0.8}],
            "agent_outputs": {"test_agent": {"result": "success"}},
        }

        # Verify all fields are accessible
        assert complete_state["coverage_score"] == 0.75
        assert complete_state["questioning_complete"]
        assert complete_state["technical_feasibility_score"] == 0.8
        assert complete_state["budget_compliance_status"] == "pass"
        assert not complete_state["escalation_required"]

    def test_context_accumulation_across_agents(self):
        """Test context accumulation mechanism across agent executions."""
        from libs.llm_agent_base import MLOpsExecutionContext

        # Simulate state after multiple agent executions
        accumulated_state = {
            "messages": [
                {"role": "user", "content": "Build fraud detection ML system"}
            ],
            "constraints": {
                "project_description": "Fraud detection system",
                "budget_band": "enterprise",
                "compliance_requirements": ["PCI-DSS"],
            },
            "coverage_score": 0.85,
            "plan": {
                "pattern_id": "realtime_inference_enterprise",
                "estimated_monthly_cost": 1850.0,
            },
            "tech_critique": {
                "overall_feasibility_score": 0.78,
                "technical_risks": ["PCI compliance complexity"],
            },
            "execution_order": [
                "intake_extract",
                "coverage_check",
                "planner",
                "critic_tech",
            ],
            "reason_cards": [
                {
                    "agent": "intake_extract", 
                    "confidence": 0.89,
                    "choice": {"id": "constraint_extraction", "justification": "Successfully extracted constraints"},
                    "decision_id": "decision_001",
                    "outputs": {"extraction_confidence": 0.89}
                },
                {
                    "agent": "coverage_check", 
                    "confidence": 0.90,
                    "choice": {"id": "coverage_analysis", "justification": "Coverage threshold met"},
                    "decision_id": "decision_002", 
                    "outputs": {"coverage_score": 0.85}
                },
                {
                    "agent": "planner", 
                    "confidence": 0.91,
                    "choice": {"id": "realtime_inference_enterprise", "justification": "Best fit for fraud detection requirements"},
                    "decision_id": "decision_003",
                    "outputs": {"pattern_selected": "realtime_inference_enterprise"}
                },
                {
                    "agent": "critic_tech", 
                    "confidence": 0.82,
                    "choice": {"id": "technical_feasibility", "justification": "Feasible with security considerations"},
                    "decision_id": "decision_004",
                    "outputs": {"feasibility_score": 0.78}
                },
            ],
            "agent_outputs": {
                "intake_extract": {"extraction_confidence": 0.89},
                "coverage_check": {"coverage_score": 0.85},
                "planner": {"pattern_selected": "realtime_inference_enterprise"},
                "critic_tech": {"feasibility_score": 0.78},
            },
        }

        context = MLOpsExecutionContext(accumulated_state)

        # Test comprehensive context building
        context_summary = context.build_context_summary()
        assert "fraud detection" in context_summary.lower()
        assert "pci-dss" in context_summary.lower() or "pci" in context_summary.lower()
        assert "1850" in context_summary  # Cost information
        assert "0.78" in context_summary  # Technical feasibility

        # Test previous decisions extraction
        decisions = context.get_previous_decisions()
        assert len(decisions) == 4
        assert all(d["confidence"] > 0.75 for d in decisions)

        # Test agent-specific context  
        from libs.agent_framework import AgentType
        cost_context = context.get_agent_specific_context(AgentType.CRITIC_COST)
        assert "plan" in cost_context
        assert "tech_analysis" in cost_context
        assert cost_context["plan"]["estimated_monthly_cost"] == 1850.0

    async def test_error_propagation_and_recovery(self):
        """Test error handling propagation through the workflow."""
        from libs.intake_extract_agent import create_intake_extract_agent

        # Test agent failure scenario
        with patch("libs.llm_agent_base.get_llm_client") as mock_get_client:
            mock_client = Mock()
            mock_client.complete = AsyncMock(
                side_effect=Exception("LLM service unavailable")
            )
            mock_get_client.return_value = mock_client

            intake_agent = create_intake_extract_agent()
            project_state = {
                "messages": [{"role": "user", "content": "Test"}],
                "project_id": "error-test",
                "decision_set_id": "error-test-001",
                "version": 1,
            }

            result = await intake_agent.execute(project_state)

            # Verify error handling
            assert not result.success
            assert "failed" in result.error_message.lower() or "unavailable" in result.error_message.lower()
            assert result.reason_card is not None
            assert len(result.reason_card.risks) > 0

    def test_performance_characteristics(self):
        """Test performance characteristics of the LLM transformation."""
        from libs.llm_agent_base import MLOpsExecutionContext

        # Test with large state to ensure scalability
        large_state = {
            "messages": [{"role": "user", "content": "Complex ML system"}],
            "reason_cards": [
                {"agent": f"test_{i}", "data": f"data_{i}"} for i in range(100)
            ],
            "agent_outputs": {
                f"agent_{i}": {"output": f"result_{i}"} for i in range(50)
            },
            "execution_order": [f"step_{i}" for i in range(200)],
            "constraints": {"project_description": "Large complex system"},
            "coverage_analysis": {"score": 0.8},
            "plan": {"pattern_id": "complex_pattern", "cost": 5000.0},
        }

        # Context building should be efficient even with large state
        context = MLOpsExecutionContext(large_state)
        summary = context.build_context_summary()

        # Summary should be manageable size despite large input
        assert len(summary) < 10000  # Reasonable summary length
        assert "complex ml system" in summary.lower()

        # Decision extraction should handle large lists
        decisions = context.get_previous_decisions()
        assert isinstance(decisions, list)  # Should not fail with large data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not integration or integration"])
