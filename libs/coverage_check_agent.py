"""
CoverageCheckAgent - LLM-powered constraint coverage analysis

Analyzes extracted constraints for completeness and quality, identifying
gaps and computing coverage scores to guide the adaptive questioning process.
"""

from __future__ import annotations

from typing import Type, Dict, Any
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .constraint_schema import CoverageAnalysisResult

logger = logging.getLogger(__name__)


class CoverageCheckAgent(BaseLLMAgent):
    """
    LLM-powered agent for analyzing constraint coverage and completeness.

    This agent evaluates how complete the extracted constraints are and identifies
    critical gaps that need to be addressed before proceeding with planning.
    """

    SYSTEM_PROMPT = """
You are an expert MLOps requirements completeness analyzer with deep expertise in cloud architecture, machine learning operations, and enterprise system design.

Your role is to evaluate extracted constraint information and determine:
1. How complete the requirements are for making sound architecture decisions
2. Which critical fields are missing that would significantly impact system design
3. Which optional fields would improve the quality of recommendations
4. Whether the current information is sufficient to proceed with planning

## Evaluation Framework

### Coverage Scoring (0.0 to 1.0)
Assess completeness across these weighted dimensions:

**Critical Fields (High Impact on Architecture - Weight 3.0)**
- project_description: Clear understanding of what needs to be built
- budget_band: Determines service selection and architecture complexity
- workload_types: Fundamental for choosing the right architecture pattern
- data_classification: Critical for security and compliance decisions

**Important Fields (Medium Impact - Weight 2.0)**  
- deployment_preference: Influences technology stack selection
- expected_throughput: Affects capacity planning and service sizing
- regions: Impacts latency, compliance, and disaster recovery

**Valuable Fields (Lower Impact - Weight 1.0)**
- latency_requirements_ms: Fine-tunes performance optimization
- availability_target: Guides redundancy and reliability design
- team_expertise: Influences complexity and operational decisions
- model_types: Helps with compute and storage planning

### Coverage Thresholds
- **0.0-0.4**: Insufficient - Cannot proceed with reliable planning
- **0.4-0.7**: Marginal - Basic planning possible but risky
- **0.7-0.85**: Good - Adequate for solid architecture recommendations  
- **0.85-1.0**: Excellent - Comprehensive requirements for optimal design

### Gap Analysis

**Critical Gaps** (Must Address):
- Missing information that could lead to fundamentally wrong architecture choices
- Ambiguous requirements that create high-risk assumptions
- Conflicting constraints that need resolution

**Optional Gaps** (Should Address):
- Missing details that would improve recommendation quality
- Additional context that would enable optimization opportunities
- Clarifications that would increase confidence

## Analysis Guidelines

1. **Be Pragmatic**: Focus on gaps that meaningfully impact architecture decisions
2. **Consider Dependencies**: Some fields become critical only in specific contexts
3. **Assess Risk**: Evaluate the risk of proceeding with incomplete information
4. **Prioritize Impact**: Focus on gaps with highest architectural impact
5. **Provide Guidance**: Suggest specific questions or clarifications needed

## Coverage Threshold Logic

The minimum coverage threshold for proceeding to planning is typically **0.7** (70%), but this can vary based on:
- Complexity of the stated requirements
- Confidence in the extracted information  
- Presence of critical vs. optional gaps
- Risk tolerance for the project type

## Response Format

You must respond with a valid JSON object matching the CoverageAnalysisResult schema:
- Overall coverage score (0.0-1.0) with detailed calculation rationale
- List of missing critical fields that must be addressed
- List of missing optional fields that would improve quality
- List of ambiguous fields that need clarification
- Boolean indicating whether minimum threshold is met
- Specific recommendations for improving coverage

## Context Awareness

Consider the extraction context:
- Extraction confidence levels from the previous agent
- Uncertain fields that were flagged during extraction
- The complexity and clarity of the original user input
- Any domain-specific requirements that might be implied

Focus on practical completeness rather than theoretical perfection. The goal is to have sufficient information for sound architecture decisions, not exhaustive documentation.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.COVERAGE_CHECK,
            name="Coverage Check Agent",
            description="Analyze constraint coverage and identify critical gaps",
            system_prompt=self.SYSTEM_PROMPT,
            # model will be read from OPENAI_MODEL environment variable
        )

    async def get_structured_output_type(self) -> Type[CoverageAnalysisResult]:
        """Return the expected output schema for this agent."""
        return CoverageAnalysisResult

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build user prompt with extracted constraints and extraction metadata.
        """
        # Get the extracted constraints
        if not context.constraints:
            return "ERROR: No constraints found in context. The IntakeExtractAgent must be executed first."

        # Get extraction metadata
        extraction_info = context.state.get("constraint_extraction", {})
        context.get_previous_agent_outputs()

        # Build detailed analysis prompt
        constraints_summary = context.constraints.to_context_string()

        prompt_parts = [
            "Please analyze the completeness of these extracted MLOps constraints:",
            "",
            "## Extracted Constraints",
            constraints_summary,
            "",
            "## Extraction Context",
        ]

        if extraction_info:
            prompt_parts.extend(
                [
                    f"- Extraction Confidence: {extraction_info.get('confidence', 'Unknown'):.1%}",
                    f"- Uncertain Fields: {', '.join(extraction_info.get('uncertain_fields', [])) or 'None'}",
                    f"- Follow-up Recommended: {extraction_info.get('follow_up_needed', False)}",
                    f"- Rationale: {extraction_info.get('rationale', 'Not provided')}",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "## Original User Input",
                f'"{context.user_input[:500]}{"..." if len(context.user_input) > 500 else ""}"',
                "",
                "## Analysis Request",
                "",
                "Please perform a comprehensive coverage analysis focusing on:",
                "",
                "1. **Coverage Score Calculation**: Evaluate completeness across critical, important, and valuable constraint dimensions",
                "2. **Critical Gap Identification**: Which missing fields would lead to poor architecture decisions?",
                "3. **Optional Gap Assessment**: Which additional details would improve recommendation quality?",
                "4. **Ambiguity Resolution**: Which fields need clarification to reduce risk?",
                "5. **Threshold Assessment**: Is there sufficient information to proceed with planning (typically 70%+ coverage)?",
                "6. **Improvement Recommendations**: Specific suggestions for addressing the most important gaps",
                "",
                "Consider both the explicit constraints and any implicit requirements suggested by the user's domain, use case, and stated preferences.",
                "",
                "Focus on practical completeness that enables sound architecture decisions rather than exhaustive documentation.",
            ]
        )

        return "\n".join(prompt_parts)

    async def extract_state_updates(
        self, llm_response: CoverageAnalysisResult, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from coverage analysis result.
        """
        return {
            # Store coverage analysis results
            "coverage_analysis": {
                "score": llm_response.coverage_score,
                "threshold_met": llm_response.coverage_threshold_met,
                "critical_gaps": llm_response.missing_critical_fields,
                "optional_gaps": llm_response.missing_optional_fields,
                "ambiguous_fields": llm_response.ambiguous_fields,
                "recommendations": llm_response.recommendations,
                "agent_version": "1.0",
            },
            # Update coverage score for easy access by other agents
            "coverage_score": llm_response.coverage_score,
            "coverage_threshold_met": llm_response.coverage_threshold_met,
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> list[str]:
        """Requires IntakeExtractAgent to have run first."""
        return [AgentType.INTAKE_EXTRACT.value]

    async def build_next_agent_context(
        self, llm_response: CoverageAnalysisResult
    ) -> Dict[str, Any]:
        """Build context for the next agent (AdaptiveQuestionsAgent)."""
        return {
            "from_agent": self.agent_type.value,
            "coverage_score": llm_response.coverage_score,
            "threshold_met": llm_response.coverage_threshold_met,
            "critical_gaps_count": len(llm_response.missing_critical_fields),
            "needs_questioning": not llm_response.coverage_threshold_met
            or len(llm_response.missing_critical_fields) > 0,
            "summary": f"Coverage analysis: {llm_response.coverage_score:.1%} complete, {'meets' if llm_response.coverage_threshold_met else 'fails'} threshold, {len(llm_response.missing_critical_fields)} critical gaps",
        }


def create_coverage_check_agent() -> CoverageCheckAgent:
    """Factory function to create a configured CoverageCheckAgent."""
    return CoverageCheckAgent()
