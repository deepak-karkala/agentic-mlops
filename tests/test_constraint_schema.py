"""
Tests for constraint schema and validation logic

Validates the formal constraint schema, coverage calculations,
and data validation rules.
"""

import pytest
from pydantic import ValidationError

from libs.constraint_schema import (
    MLOpsConstraints,
    BudgetBand,
    DeploymentPreference,
    DataClassification,
    ThroughputLevel,
    WorkloadType,
    ConstraintExtractionResult,
    CoverageAnalysisResult,
    AdaptiveQuestion,
    AdaptiveQuestioningResult,
)


class TestMLOpsConstraints:
    """Test the core MLOpsConstraints schema."""

    def test_minimal_valid_constraints(self):
        """Test minimal valid constraint creation."""
        constraints = MLOpsConstraints(project_description="Test ML project")

        # Test defaults are applied
        assert constraints.budget_band == BudgetBand.STARTUP
        assert constraints.deployment_preference == DeploymentPreference.SERVERLESS
        assert constraints.data_classification == DataClassification.INTERNAL
        assert len(constraints.workload_types) >= 1

    def test_comprehensive_constraints(self):
        """Test comprehensive constraint specification."""
        constraints = MLOpsConstraints(
            project_description="Real-time fraud detection system",
            project_name="FraudGuard ML",
            budget_band=BudgetBand.ENTERPRISE,
            deployment_preference=DeploymentPreference.CONTAINERS,
            workload_types=[
                WorkloadType.ONLINE_INFERENCE,
                WorkloadType.FEATURE_ENGINEERING,
            ],
            expected_throughput=ThroughputLevel.HIGH,
            latency_requirements_ms=200,
            data_classification=DataClassification.RESTRICTED,
            data_sources=["transaction_db", "user_profiles", "merchant_data"],
            compliance_requirements=["PCI-DSS", "GDPR"],
            regions=["us-east-1", "us-west-2"],
            availability_target=99.95,
            disaster_recovery_required=True,
            model_types=["classification", "anomaly_detection"],
            model_size_category="large",
            training_frequency="daily",
            team_size=12,
            team_expertise=["python", "aws", "kubernetes", "ml_ops"],
            extracted_confidence=0.85,
            missing_fields=["integration_requirements"],
            ambiguous_fields=["operational_preferences"],
        )

        # Validate all fields are set correctly
        assert constraints.project_description == "Real-time fraud detection system"
        assert constraints.budget_band == BudgetBand.ENTERPRISE
        assert constraints.latency_requirements_ms == 200
        assert "PCI-DSS" in constraints.compliance_requirements
        assert constraints.availability_target == 99.95
        assert constraints.extracted_confidence == 0.85

    def test_validation_rules(self):
        """Test constraint validation rules."""
        # Test latency bounds
        with pytest.raises(ValidationError):
            MLOpsConstraints(
                project_description="Test",
                latency_requirements_ms=0,  # Too low
            )

        with pytest.raises(ValidationError):
            MLOpsConstraints(
                project_description="Test",
                latency_requirements_ms=70000,  # Too high
            )

        # Test availability bounds
        with pytest.raises(ValidationError):
            MLOpsConstraints(
                project_description="Test",
                availability_target=90.0,  # Too low
            )

        with pytest.raises(ValidationError):
            MLOpsConstraints(
                project_description="Test",
                availability_target=100.0,  # Too high (impossible)
            )

    def test_region_validation(self):
        """Test AWS region validation."""
        # Valid regions
        valid_constraints = MLOpsConstraints(
            project_description="Test",
            regions=["us-east-1", "eu-west-1", "ap-southeast-1", "global"],
        )
        assert len(valid_constraints.regions) == 4

        # Invalid region format
        with pytest.raises(ValidationError):
            MLOpsConstraints(project_description="Test", regions=["invalid-region"])

    def test_workload_type_validation(self):
        """Test workload type validation and defaults."""
        # Test default workload types applied
        constraints = MLOpsConstraints(project_description="Test")
        assert WorkloadType.BATCH_TRAINING in constraints.workload_types
        assert WorkloadType.ONLINE_INFERENCE in constraints.workload_types

        # Test empty workload types get defaults
        constraints = MLOpsConstraints(project_description="Test", workload_types=[])
        assert len(constraints.workload_types) >= 1

    def test_consistency_validation(self):
        """Test cross-field consistency validation."""
        # Test sensitive data without compliance requirements
        constraints = MLOpsConstraints(
            project_description="Test sensitive data system",
            data_classification=DataClassification.SENSITIVE,
            compliance_requirements=[],
        )

        # Should flag missing compliance requirements
        assert "compliance_requirements" in constraints.missing_fields

        # Test high throughput with very low latency (potentially inconsistent)
        constraints = MLOpsConstraints(
            project_description="Test high-performance system",
            expected_throughput=ThroughputLevel.VERY_HIGH,
            latency_requirements_ms=50,
        )

        # Should flag potential inconsistency
        assert "latency_throughput_consistency" in constraints.ambiguous_fields

    def test_coverage_score_calculation(self):
        """Test coverage score calculation logic."""
        # Minimal constraints - just project description, defaults for others
        minimal = MLOpsConstraints(project_description="Test")
        coverage = minimal.calculate_coverage_score()
        # Due to defaults (budget_band, deployment_preference, etc.), coverage will be moderate
        assert 0.5 <= coverage <= 0.9  # Should have moderate coverage due to defaults

        # Comprehensive constraints (high coverage)
        comprehensive = MLOpsConstraints(
            project_description="Complete ML system description",
            budget_band=BudgetBand.GROWTH,
            deployment_preference=DeploymentPreference.KUBERNETES,
            workload_types=[WorkloadType.ONLINE_INFERENCE],
            expected_throughput=ThroughputLevel.MEDIUM,
            data_classification=DataClassification.INTERNAL,
            regions=["us-east-1"],
            latency_requirements_ms=500,
            availability_target=99.9,
            team_expertise=["python", "kubernetes"],
            model_types=["classification"],
        )
        coverage = comprehensive.calculate_coverage_score()
        assert coverage >= 0.9  # Should be very high coverage

    def test_missing_critical_fields(self):
        """Test missing critical field detection."""
        # Empty description should be critical
        empty_desc = MLOpsConstraints(project_description="")
        missing = empty_desc.get_missing_critical_fields()
        assert "project_description" in missing

        # Valid constraints should have no missing critical fields
        valid = MLOpsConstraints(
            project_description="Valid ML project",
            budget_band=BudgetBand.GROWTH,
            workload_types=[WorkloadType.BATCH_TRAINING],
        )
        missing = valid.get_missing_critical_fields()
        assert len(missing) == 0

    def test_context_string_generation(self):
        """Test human-readable context string generation."""
        constraints = MLOpsConstraints(
            project_description="Fraud detection ML system",
            budget_band=BudgetBand.ENTERPRISE,
            workload_types=[WorkloadType.ONLINE_INFERENCE],
            compliance_requirements=["PCI-DSS"],
            latency_requirements_ms=200,
        )

        context = constraints.to_context_string()

        # Verify key information is present
        assert "Fraud detection ML system" in context
        assert "enterprise" in context.lower()
        assert "online_inference" in context
        assert "PCI-DSS" in context
        assert "200ms" in context


class TestConstraintExtractionResult:
    """Test constraint extraction result schema."""

    def test_extraction_result_creation(self):
        """Test extraction result creation and validation."""
        constraints = MLOpsConstraints(project_description="Test system")

        result = ConstraintExtractionResult(
            constraints=constraints,
            extraction_confidence=0.75,
            uncertain_fields=["team_expertise", "availability_target"],
            extraction_rationale="Extracted based on limited information provided",
            follow_up_needed=True,
        )

        assert result.extraction_confidence == 0.75
        assert len(result.uncertain_fields) == 2
        assert result.follow_up_needed

    def test_confidence_bounds(self):
        """Test confidence score validation."""
        constraints = MLOpsConstraints(project_description="Test")

        # Valid confidence
        ConstraintExtractionResult(
            constraints=constraints,
            extraction_confidence=0.8,
            extraction_rationale="Test",
            follow_up_needed=False,
        )

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            ConstraintExtractionResult(
                constraints=constraints,
                extraction_confidence=1.5,
                extraction_rationale="Test",
                follow_up_needed=False,
            )


class TestCoverageAnalysisResult:
    """Test coverage analysis result schema."""

    def test_coverage_analysis_creation(self):
        """Test coverage analysis result creation."""
        result = CoverageAnalysisResult(
            coverage_score=0.65,
            missing_critical_fields=["availability_target"],
            missing_optional_fields=["team_size", "model_types"],
            ambiguous_fields=["deployment_preference"],
            coverage_threshold_met=False,
            recommendations=[
                "Clarify availability requirements",
                "Specify deployment preference",
            ],
        )

        assert result.coverage_score == 0.65
        assert not result.coverage_threshold_met
        assert len(result.recommendations) == 2

    def test_coverage_score_bounds(self):
        """Test coverage score validation bounds."""
        # Valid coverage score
        CoverageAnalysisResult(
            coverage_score=0.75,
            coverage_threshold_met=True,
            missing_critical_fields=[],
            missing_optional_fields=[],
            ambiguous_fields=[],
            recommendations=[],
        )

        # Invalid coverage score
        with pytest.raises(ValidationError):
            CoverageAnalysisResult(
                coverage_score=1.2,  # Too high
                coverage_threshold_met=True,
                missing_critical_fields=[],
                missing_optional_fields=[],
                ambiguous_fields=[],
                recommendations=[],
            )


class TestAdaptiveQuestioningSystem:
    """Test adaptive questioning schema and logic."""

    def test_adaptive_question_creation(self):
        """Test adaptive question creation and validation."""
        question = AdaptiveQuestion(
            question_id="budget_clarification",
            question_text="What's your monthly budget range for this ML system?",
            field_targets=["budget_band"],
            priority="high",
            question_type="choice",
            choices=["Under $500", "$500-$1000", "Over $1000"],
        )

        assert question.question_id == "budget_clarification"
        assert question.priority == "high"
        assert len(question.choices) == 3

    def test_question_types(self):
        """Test different question types."""
        # Choice question
        choice_q = AdaptiveQuestion(
            question_id="deploy_pref",
            question_text="Preferred deployment?",
            field_targets=["deployment_preference"],
            priority="medium",
            question_type="choice",
            choices=["Serverless", "Containers", "Kubernetes"],
        )
        assert choice_q.question_type == "choice"
        assert len(choice_q.choices) > 0

        # Numeric question
        numeric_q = AdaptiveQuestion(
            question_id="latency_req",
            question_text="Maximum acceptable latency in milliseconds?",
            field_targets=["latency_requirements_ms"],
            priority="high",
            question_type="numeric",
        )
        assert numeric_q.question_type == "numeric"
        assert numeric_q.choices is None

        # Text question
        text_q = AdaptiveQuestion(
            question_id="project_desc",
            question_text="Please describe your ML use case in detail.",
            field_targets=["project_description"],
            priority="high",
            question_type="text",
        )
        assert text_q.question_type == "text"

    def test_questioning_result(self):
        """Test adaptive questioning result."""
        questions = [
            AdaptiveQuestion(
                question_id="budget_q",
                question_text="What's your budget?",
                field_targets=["budget_band"],
                priority="high",
                question_type="choice",
                choices=["Low", "Medium", "High"],
            ),
            AdaptiveQuestion(
                question_id="latency_q",
                question_text="Latency requirement?",
                field_targets=["latency_requirements_ms"],
                priority="medium",
                question_type="numeric",
            ),
        ]

        result = AdaptiveQuestioningResult(
            questions=questions,
            questioning_complete=False,
            current_coverage=0.6,
            target_coverage=0.75,
            questioning_rationale="Need clarification on budget and performance requirements",
        )

        assert len(result.questions) == 2
        assert result.current_coverage < result.target_coverage
        assert not result.questioning_complete

    def test_questioning_completion_logic(self):
        """Test questioning completion scenarios."""
        # High coverage should complete questioning
        high_coverage = AdaptiveQuestioningResult(
            questions=[],
            questioning_complete=True,
            current_coverage=0.85,
            target_coverage=0.75,
            questioning_rationale="Coverage threshold met",
        )
        assert high_coverage.questioning_complete
        assert high_coverage.current_coverage >= high_coverage.target_coverage

        # Low coverage should continue questioning
        low_coverage = AdaptiveQuestioningResult(
            questions=[
                AdaptiveQuestion(
                    question_id="test",
                    question_text="Test question?",
                    field_targets=["test_field"],
                    priority="high",
                    question_type="text",
                )
            ],
            questioning_complete=False,
            current_coverage=0.5,
            target_coverage=0.75,
            questioning_rationale="Need more information",
        )
        assert not low_coverage.questioning_complete
        assert len(low_coverage.questions) > 0


class TestSchemaEvolution:
    """Test schema evolution and backward compatibility."""

    def test_optional_field_addition(self):
        """Test that new optional fields don't break existing constraints."""
        # Simulate old constraint data without new fields
        old_data = {
            "project_description": "Legacy ML project",
            "budget_band": "startup",
            "deployment_preference": "serverless",
        }

        # Should still validate successfully
        constraints = MLOpsConstraints.model_validate(old_data)
        assert constraints.project_description == "Legacy ML project"

        # New optional fields should have defaults
        assert constraints.extracted_confidence == 0.0  # Default value
        assert isinstance(constraints.missing_fields, list)

    def test_enum_expansion_compatibility(self):
        """Test enum expansion doesn't break existing data."""
        # Test all current enum values are valid
        assert BudgetBand.STARTUP.value == "startup"
        assert DeploymentPreference.SERVERLESS.value == "serverless"
        assert DataClassification.INTERNAL.value == "internal"
        assert ThroughputLevel.LOW.value == "low"

        # Test enum can be used in constraints
        constraints = MLOpsConstraints(
            project_description="Test",
            budget_band=BudgetBand.ENTERPRISE,
            deployment_preference=DeploymentPreference.KUBERNETES,
            data_classification=DataClassification.RESTRICTED,
            expected_throughput=ThroughputLevel.VERY_HIGH,
        )

        assert constraints.budget_band == BudgetBand.ENTERPRISE
        assert constraints.expected_throughput == ThroughputLevel.VERY_HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
