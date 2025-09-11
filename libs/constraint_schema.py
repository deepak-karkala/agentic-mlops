"""
MLOps Constraint Schema

Formal Pydantic models for MLOps project constraints and requirements.
Used for structured data flow between agents and validation.
"""

from __future__ import annotations

from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


class BudgetBand(str, Enum):
    """Budget bands for organizational sizing."""

    STARTUP = "startup"  # $0-500/month
    GROWTH = "growth"  # $500-1000/month
    ENTERPRISE = "enterprise"  # $1000+/month


class DeploymentPreference(str, Enum):
    """Deployment pattern preferences."""

    SERVERLESS = "serverless"
    CONTAINERS = "containers"
    KUBERNETES = "kubernetes"
    MANAGED = "managed"


class DataClassification(str, Enum):
    """Data sensitivity levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class ThroughputLevel(str, Enum):
    """Expected system throughput levels."""

    LOW = "low"  # <1K requests/day
    MEDIUM = "medium"  # 1K-100K requests/day
    HIGH = "high"  # 100K-1M requests/day
    VERY_HIGH = "very_high"  # >1M requests/day


class WorkloadType(str, Enum):
    """Types of ML workloads."""

    BATCH_TRAINING = "batch_training"
    ONLINE_INFERENCE = "online_inference"
    STREAMING_INFERENCE = "streaming_inference"
    FEATURE_ENGINEERING = "feature_engineering"
    DATA_PROCESSING = "data_processing"
    MODEL_EXPERIMENTATION = "model_experimentation"
    BATCH_INFERENCE = "batch_inference"


class MLOpsConstraints(BaseModel):
    """
    Comprehensive constraint schema for MLOps project requirements.

    This is the canonical data structure that all agents read from and write to.
    Represents the complete set of user requirements and preferences.
    """

    # Project metadata
    project_description: str = Field(
        description="Natural language description of the ML project"
    )
    project_name: Optional[str] = Field(None, description="Optional project name")

    # Core requirements
    budget_band: BudgetBand = Field(
        BudgetBand.STARTUP, description="Budget category for the organization"
    )
    deployment_preference: DeploymentPreference = Field(
        DeploymentPreference.SERVERLESS, description="Preferred deployment pattern"
    )

    # Workload characteristics
    workload_types: List[WorkloadType] = Field(
        default_factory=lambda: [
            WorkloadType.BATCH_TRAINING,
            WorkloadType.ONLINE_INFERENCE,
        ],
        description="Types of ML workloads to support",
    )
    expected_throughput: ThroughputLevel = Field(
        ThroughputLevel.LOW, description="Expected system throughput"
    )
    latency_requirements_ms: Optional[int] = Field(
        None, ge=1, le=60000, description="Maximum acceptable latency in milliseconds"
    )

    # Data and compliance
    data_classification: DataClassification = Field(
        DataClassification.INTERNAL, description="Data sensitivity classification"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Types of data sources (databases, APIs, files, etc.)",
    )
    compliance_requirements: List[str] = Field(
        default_factory=list,
        description="Compliance standards (GDPR, HIPAA, SOX, etc.)",
    )

    # Infrastructure preferences
    regions: List[str] = Field(
        default_factory=lambda: ["us-east-1"], description="AWS regions for deployment"
    )
    availability_target: Optional[float] = Field(
        None,
        ge=95.0,
        le=99.999,
        description="Target availability percentage (e.g., 99.9)",
    )
    disaster_recovery_required: bool = Field(
        False, description="Whether disaster recovery is required"
    )

    # Technical requirements
    model_types: List[str] = Field(
        default_factory=list,
        description="Types of ML models (regression, classification, NLP, etc.)",
    )
    model_size_category: Optional[Literal["small", "medium", "large", "very_large"]] = (
        Field(None, description="Expected model size category")
    )
    training_frequency: Optional[
        Literal["one_time", "weekly", "daily", "real_time"]
    ] = Field(None, description="How often models need to be retrained")

    # Integration requirements
    integration_requirements: List[str] = Field(
        default_factory=list,
        description="Required integrations (APIs, databases, services)",
    )
    authentication_methods: List[str] = Field(
        default_factory=list, description="Required authentication methods"
    )

    # Team and operational
    team_size: Optional[int] = Field(
        None, ge=1, le=1000, description="Size of the development team"
    )
    team_expertise: List[str] = Field(
        default_factory=list, description="Team's technical expertise areas"
    )
    operational_preferences: List[str] = Field(
        default_factory=list, description="Operational preferences and constraints"
    )
    maintenance_window: Optional[str] = Field(
        None, description="Acceptable maintenance window"
    )

    # Quality attributes
    monitoring_requirements: List[str] = Field(
        default_factory=list, description="Specific monitoring and alerting needs"
    )
    logging_requirements: List[str] = Field(
        default_factory=list, description="Logging and audit requirements"
    )
    testing_requirements: List[str] = Field(
        default_factory=list, description="Testing strategy requirements"
    )

    # Meta information for tracking
    extracted_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in the constraint extraction"
    )
    missing_fields: List[str] = Field(
        default_factory=list, description="Fields identified as missing or unclear"
    )
    ambiguous_fields: List[str] = Field(
        default_factory=list, description="Fields that need clarification"
    )
    extraction_method: str = Field(
        "llm_extraction", description="Method used to extract constraints"
    )
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator("regions")
    @classmethod
    def validate_regions(cls, v):
        """Validate AWS region format."""
        valid_prefixes = ["us-", "eu-", "ap-", "sa-", "ca-", "af-", "me-"]
        for region in v:
            if not any(region.startswith(prefix) for prefix in valid_prefixes):
                # Allow 'global' and other special cases
                if region not in ["global", "multi-region"]:
                    raise ValueError(f"Invalid AWS region format: {region}")
        return v

    @field_validator("workload_types")
    @classmethod
    def validate_workload_types(cls, v):
        """Ensure at least one workload type is specified."""
        if not v:
            return [WorkloadType.BATCH_TRAINING, WorkloadType.ONLINE_INFERENCE]
        return v

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate cross-field consistency."""
        # Check for consistency between data classification and compliance
        if self.data_classification in [
            DataClassification.SENSITIVE,
            DataClassification.RESTRICTED,
        ]:
            if not self.compliance_requirements:
                self.missing_fields = self.missing_fields + ["compliance_requirements"]

        # Check throughput vs latency consistency
        if (
            self.expected_throughput == ThroughputLevel.VERY_HIGH
            and self.latency_requirements_ms
            and self.latency_requirements_ms < 100
        ):
            self.ambiguous_fields = self.ambiguous_fields + [
                "latency_throughput_consistency"
            ]

        return self

    def calculate_coverage_score(self) -> float:
        """
        Calculate how complete the constraints are (0.0 to 1.0).

        Returns:
            Coverage score based on filled fields and importance weights
        """
        total_weight = 0.0
        filled_weight = 0.0

        # Critical fields (high weight)
        critical_fields = {
            "project_description": 3.0,
            "budget_band": 2.0,
            "workload_types": 2.0,
            "data_classification": 2.0,
        }

        # Important fields (medium weight)
        important_fields = {
            "deployment_preference": 1.5,
            "expected_throughput": 1.5,
            "regions": 1.0,
        }

        # Optional fields (low weight)
        optional_fields = {
            "latency_requirements_ms": 1.0,
            "availability_target": 1.0,
            "team_expertise": 0.5,
            "model_types": 0.5,
        }

        all_fields = {**critical_fields, **important_fields, **optional_fields}

        for field, weight in all_fields.items():
            total_weight += weight
            value = getattr(self, field, None)

            if value is not None:
                if isinstance(value, list) and len(value) > 0:
                    filled_weight += weight
                elif isinstance(value, str) and value.strip():
                    filled_weight += weight
                elif not isinstance(value, (list, str)):
                    filled_weight += weight

        return min(1.0, filled_weight / total_weight) if total_weight > 0 else 0.0

    def get_missing_critical_fields(self) -> List[str]:
        """Get list of missing critical fields."""
        critical_fields = ["project_description", "budget_band", "workload_types"]
        missing = []

        for field in critical_fields:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        return missing

    def to_context_string(self) -> str:
        """Convert constraints to human-readable context string for LLM consumption."""
        context_parts = []

        context_parts.append(f"Project: {self.project_description}")
        context_parts.append(f"Budget: {self.budget_band.value} category")
        context_parts.append(
            f"Deployment preference: {self.deployment_preference.value}"
        )
        context_parts.append(
            f"Workloads: {', '.join([wt.value for wt in self.workload_types])}"
        )
        context_parts.append(f"Expected throughput: {self.expected_throughput.value}")
        context_parts.append(f"Data classification: {self.data_classification.value}")
        context_parts.append(f"Regions: {', '.join(self.regions)}")

        if self.latency_requirements_ms:
            context_parts.append(
                f"Latency requirement: {self.latency_requirements_ms}ms"
            )

        if self.availability_target:
            context_parts.append(f"Availability target: {self.availability_target}%")

        if self.compliance_requirements:
            context_parts.append(
                f"Compliance: {', '.join(self.compliance_requirements)}"
            )

        if self.team_expertise:
            context_parts.append(f"Team expertise: {', '.join(self.team_expertise)}")

        return "\n".join(context_parts)


class ConstraintExtractionResult(BaseModel):
    """Result of constraint extraction from natural language input."""

    constraints: MLOpsConstraints = Field(
        description="Extracted constraint information"
    )
    extraction_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the extraction quality"
    )
    uncertain_fields: List[str] = Field(
        default_factory=list, description="Fields where extraction confidence is low"
    )
    extraction_rationale: str = Field(description="Explanation of extraction decisions")
    follow_up_needed: bool = Field(
        description="Whether follow-up questions are recommended"
    )


class CoverageAnalysisResult(BaseModel):
    """Result of constraint coverage analysis."""

    coverage_score: float = Field(ge=0.0, le=1.0, description="Overall coverage score")
    missing_critical_fields: List[str] = Field(
        default_factory=list, description="Critical fields that are missing"
    )
    missing_optional_fields: List[str] = Field(
        default_factory=list, description="Optional fields that would improve coverage"
    )
    ambiguous_fields: List[str] = Field(
        default_factory=list, description="Fields that need clarification"
    )
    coverage_threshold_met: bool = Field(
        description="Whether minimum coverage threshold is met"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improving coverage"
    )


class AdaptiveQuestion(BaseModel):
    """A single adaptive question for constraint clarification."""

    question_id: str = Field(description="Unique identifier for the question")
    question_text: str = Field(description="Human-readable question")
    field_targets: List[str] = Field(
        description="Constraint fields this question aims to fill"
    )
    priority: Literal["high", "medium", "low"] = Field(
        description="Priority level of this question"
    )
    question_type: Literal["choice", "numeric", "text", "boolean"] = Field(
        description="Type of expected answer"
    )
    choices: Optional[List[str]] = Field(
        None, description="Predefined choices for choice-type questions"
    )


class AdaptiveQuestioningResult(BaseModel):
    """Result of adaptive questioning analysis."""

    questions: List[AdaptiveQuestion] = Field(
        description="Generated follow-up questions"
    )
    questioning_complete: bool = Field(
        description="Whether questioning phase should end"
    )
    current_coverage: float = Field(
        ge=0.0, le=1.0, description="Current constraint coverage score"
    )
    target_coverage: float = Field(
        ge=0.0, le=1.0, description="Target coverage to achieve"
    )
    questioning_rationale: str = Field(description="Explanation of question selection")
