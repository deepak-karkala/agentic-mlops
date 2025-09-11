"""
Agent Output Schemas

Structured Pydantic models defining the exact JSON output format
for each LLM-powered agent. These schemas ensure reliable parsing
and validation of agent responses.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field

from .constraint_schema import (
    ConstraintExtractionResult,
    CoverageAnalysisResult,
    AdaptiveQuestioningResult,
)


class PlannerOutput(BaseModel):
    """Structured output for the Planner Agent."""

    # Pattern selection
    selected_pattern_id: str = Field(
        description="ID of the selected MLOps capability pattern"
    )
    pattern_name: str = Field(description="Human-readable name of selected pattern")
    selection_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in pattern selection"
    )
    selection_rationale: str = Field(
        description="Detailed explanation of why this pattern was selected"
    )

    # Alternative analysis
    alternatives_considered: List[Dict[str, Any]] = Field(
        description="Alternative patterns that were evaluated"
    )
    pattern_comparison: str = Field(description="Brief comparison of top alternatives")

    # Plan details
    architecture_overview: str = Field(
        description="High-level architecture description"
    )
    key_services: Dict[str, str] = Field(description="Primary services and their roles")
    estimated_monthly_cost: float = Field(
        ge=0.0, description="Estimated monthly cost in USD"
    )
    deployment_approach: str = Field(description="Recommended deployment strategy")

    # Implementation roadmap
    implementation_phases: List[str] = Field(
        description="Recommended implementation phases"
    )
    critical_success_factors: List[str] = Field(
        description="Key factors for successful implementation"
    )

    # Risks and considerations
    potential_challenges: List[str] = Field(
        description="Anticipated implementation challenges"
    )
    success_metrics: List[str] = Field(description="Metrics to measure success")

    # Meta information
    assumptions_made: List[str] = Field(
        description="Key assumptions in the planning process"
    )
    decision_criteria: List[str] = Field(
        description="Primary criteria used for pattern selection"
    )


class TechCriticOutput(BaseModel):
    """Structured output for the Tech Critic Agent."""

    # Overall assessment
    technical_feasibility_score: float = Field(
        ge=0.0, le=1.0, description="Overall technical feasibility score"
    )
    architecture_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in architectural soundness"
    )
    criticism_summary: str = Field(
        description="High-level summary of technical assessment"
    )

    # Risk analysis
    technical_risks: List[str] = Field(
        description="Identified technical risks with impact assessment"
    )
    architecture_concerns: List[str] = Field(
        description="Specific architectural concerns"
    )
    scalability_risks: List[str] = Field(
        description="Potential scalability limitations"
    )
    security_concerns: List[str] = Field(
        description="Security vulnerabilities and concerns"
    )

    # Bottleneck analysis
    performance_bottlenecks: List[str] = Field(
        description="Potential performance bottlenecks"
    )
    capacity_constraints: List[str] = Field(
        description="Resource and capacity limitations"
    )
    integration_challenges: List[str] = Field(
        description="Challenges with system integration"
    )

    # Failure analysis
    single_points_of_failure: List[str] = Field(
        description="Identified single points of failure"
    )
    failure_domains: List[str] = Field(description="Analysis of failure domains")
    disaster_recovery_gaps: List[str] = Field(
        description="Gaps in disaster recovery planning"
    )

    # Recommendations
    risk_mitigation_strategies: List[str] = Field(
        description="Strategies to mitigate identified risks"
    )
    architecture_improvements: List[str] = Field(
        description="Suggested architectural improvements"
    )
    monitoring_requirements: List[str] = Field(
        description="Required monitoring and observability"
    )

    # Technical debt and maintenance
    operational_complexity: str = Field(
        description="Assessment of operational complexity"
    )
    maintenance_requirements: List[str] = Field(
        description="Ongoing maintenance requirements"
    )
    skill_requirements: List[str] = Field(
        description="Required technical skills for the team"
    )

    # Impact assessments
    availability_impact: Literal["Low", "Medium", "High", "Very High"] = Field(
        description="Impact on system availability"
    )
    performance_impact: Literal["Low", "Medium", "High", "Very High"] = Field(
        description="Impact on system performance"
    )
    security_impact: Literal["Low", "Medium", "High", "Very High"] = Field(
        description="Impact on system security"
    )

    # Confidence and caveats
    analysis_assumptions: List[str] = Field(
        description="Assumptions made during technical analysis"
    )
    analysis_limitations: List[str] = Field(
        description="Limitations of the current analysis"
    )


class CostCriticOutput(BaseModel):
    """Structured output for the Cost Critic Agent."""

    # Cost summary
    estimated_monthly_cost: float = Field(
        ge=0.0, description="Total estimated monthly cost in USD"
    )
    cost_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in cost estimates"
    )
    cost_analysis_summary: str = Field(
        description="High-level summary of cost analysis"
    )

    # Detailed breakdown
    service_costs: List[Dict[str, Any]] = Field(
        description="Detailed cost breakdown by service"
    )
    infrastructure_costs: List[Dict[str, Any]] = Field(
        description="Infrastructure-specific cost items"
    )
    operational_costs: List[Dict[str, Any]] = Field(
        description="Operational and maintenance costs"
    )

    # Cost drivers
    primary_cost_drivers: List[str] = Field(
        description="Top 3-5 cost drivers by impact"
    )
    cost_distribution: Dict[str, float] = Field(
        description="Percentage breakdown of costs by category"
    )
    variable_vs_fixed: Dict[str, float] = Field(
        description="Breakdown of variable vs fixed costs"
    )

    # Budget analysis
    budget_compliance_status: Literal["pass", "warn", "fail"] = Field(
        description="Compliance with stated budget constraints"
    )
    budget_utilization: float = Field(
        ge=0.0, le=2.0, description="Percentage of budget utilized (can exceed 100%)"
    )
    budget_risk_assessment: str = Field(description="Assessment of budget risks")

    # Scaling cost analysis
    cost_scaling_factors: List[str] = Field(
        description="Factors that will drive cost scaling"
    )
    scaling_cost_projections: Dict[str, float] = Field(
        description="Cost projections at different usage levels"
    )
    break_even_analysis: Optional[str] = Field(
        None, description="Break-even analysis if applicable"
    )

    # Optimization opportunities
    cost_optimization_recommendations: List[str] = Field(
        description="Specific recommendations to reduce costs"
    )
    alternative_architectures: List[Dict[str, Any]] = Field(
        description="Lower-cost alternative architectures"
    )
    reserved_instance_opportunities: List[str] = Field(
        description="Opportunities for reserved instance savings"
    )

    # Hidden costs and surprises
    potential_hidden_costs: List[str] = Field(
        description="Potential costs not immediately obvious"
    )
    cost_volatility_factors: List[str] = Field(
        description="Factors that could cause cost volatility"
    )
    billing_complexity_notes: List[str] = Field(
        description="Notes on billing complexity and monitoring"
    )

    # ROI and value analysis
    expected_roi_timeline: Optional[str] = Field(
        None, description="Expected timeline for return on investment"
    )
    value_propositions: List[str] = Field(
        description="Key value propositions justifying the cost"
    )
    cost_vs_benefit_analysis: str = Field(
        description="Analysis of costs versus expected benefits"
    )

    # Cost management recommendations
    cost_monitoring_strategy: List[str] = Field(
        description="Recommended cost monitoring approaches"
    )
    budget_alerts_recommended: List[Dict[str, Any]] = Field(
        description="Recommended budget alerts and thresholds"
    )
    cost_governance_needs: List[str] = Field(description="Cost governance requirements")

    # Assumptions and methodology
    cost_assumptions: List[str] = Field(
        description="Key assumptions used in cost analysis"
    )
    pricing_methodology: str = Field(description="Methodology used for cost estimation")
    cost_analysis_limitations: List[str] = Field(
        description="Limitations and caveats of cost analysis"
    )


class PolicyEngineOutput(BaseModel):
    """Structured output for the Policy Engine Agent."""

    # Overall compliance status
    overall_compliance_status: Literal["pass", "warn", "fail"] = Field(
        description="Overall policy compliance status"
    )
    compliance_score: float = Field(
        ge=0.0, le=1.0, description="Overall compliance score"
    )
    policy_assessment_summary: str = Field(
        description="High-level summary of policy assessment"
    )

    # Rule-by-rule evaluation
    policy_rule_results: List[Dict[str, Any]] = Field(
        description="Detailed results for each policy rule"
    )
    critical_violations: List[str] = Field(
        description="Critical policy violations that must be addressed"
    )
    warnings: List[str] = Field(description="Policy warnings that should be considered")

    # Compliance categories
    security_compliance: Dict[str, Any] = Field(
        description="Security policy compliance assessment"
    )
    data_governance_compliance: Dict[str, Any] = Field(
        description="Data governance compliance assessment"
    )
    operational_compliance: Dict[str, Any] = Field(
        description="Operational policy compliance"
    )
    financial_compliance: Dict[str, Any] = Field(
        description="Financial and budget compliance"
    )

    # Regulatory compliance
    regulatory_requirements: List[Dict[str, Any]] = Field(
        description="Assessment against regulatory requirements"
    )
    compliance_gaps: List[str] = Field(description="Identified compliance gaps")
    audit_readiness: Literal["ready", "needs_work", "not_ready"] = Field(
        description="Assessment of audit readiness"
    )

    # Risk assessment
    compliance_risks: List[str] = Field(
        description="Risks related to policy compliance"
    )
    risk_mitigation_requirements: List[str] = Field(
        description="Required actions to mitigate compliance risks"
    )
    escalation_required: bool = Field(
        description="Whether management escalation is required"
    )

    # Remediation guidance
    immediate_actions_required: List[str] = Field(
        description="Immediate actions required for compliance"
    )
    recommended_policy_adjustments: List[str] = Field(
        description="Recommended adjustments to achieve compliance"
    )
    alternative_approaches: List[Dict[str, Any]] = Field(
        description="Alternative approaches that would be compliant"
    )

    # Governance framework
    governance_controls_needed: List[str] = Field(
        description="Additional governance controls needed"
    )
    monitoring_requirements: List[str] = Field(
        description="Ongoing monitoring requirements for compliance"
    )
    documentation_requirements: List[str] = Field(
        description="Required documentation for compliance"
    )

    # Stakeholder impact
    stakeholder_notifications: List[str] = Field(
        description="Stakeholders who need to be notified"
    )
    approval_requirements: List[str] = Field(
        description="Approvals required for implementation"
    )
    change_management_needs: List[str] = Field(
        description="Change management requirements"
    )

    # Policy metadata
    policies_evaluated: List[str] = Field(
        description="List of policies that were evaluated"
    )
    policy_exceptions_needed: List[str] = Field(
        description="Policy exceptions that may be needed"
    )
    policy_review_recommendations: List[str] = Field(
        description="Recommendations for policy updates"
    )

    # Assessment confidence
    assessment_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the policy assessment"
    )
    assessment_limitations: List[str] = Field(
        description="Limitations of the current assessment"
    )


# Union type for all agent outputs
AgentStructuredOutput = (
    ConstraintExtractionResult
    | CoverageAnalysisResult
    | AdaptiveQuestioningResult
    | PlannerOutput
    | TechCriticOutput
    | CostCriticOutput
    | PolicyEngineOutput
)


# Mapping of agent types to their output schemas
AGENT_OUTPUT_SCHEMAS = {
    "intake_extract": ConstraintExtractionResult,
    "coverage_check": CoverageAnalysisResult,
    "adaptive_questions": AdaptiveQuestioningResult,
    "planner": PlannerOutput,
    "critic_tech": TechCriticOutput,
    "critic_cost": CostCriticOutput,
    "policy_engine": PolicyEngineOutput,
}


def get_agent_output_schema(agent_type: str) -> type[BaseModel]:
    """
    Get the structured output schema for a given agent type.

    Args:
        agent_type: The agent type identifier

    Returns:
        Pydantic model class for the agent's output schema

    Raises:
        ValueError: If agent type is not recognized
    """
    if agent_type not in AGENT_OUTPUT_SCHEMAS:
        available_types = ", ".join(AGENT_OUTPUT_SCHEMAS.keys())
        raise ValueError(
            f"Unknown agent type: {agent_type}. Available types: {available_types}"
        )

    return AGENT_OUTPUT_SCHEMAS[agent_type]


def validate_agent_output(agent_type: str, output_data: Dict[str, Any]) -> BaseModel:
    """
    Validate agent output data against the expected schema.

    Args:
        agent_type: The agent type identifier
        output_data: Raw output data to validate

    Returns:
        Validated Pydantic model instance

    Raises:
        ValueError: If agent type is not recognized
        ValidationError: If output data doesn't match schema
    """
    schema_class = get_agent_output_schema(agent_type)
    return schema_class.model_validate(output_data)
