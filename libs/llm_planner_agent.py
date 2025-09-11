"""
LLM-Powered PlannerAgent - Intelligent MLOps architecture selection

Transforms constraint-based planning from hard-coded scoring to LLM reasoning.
Uses GPT-4 to analyze requirements and select optimal MLOps patterns.
"""

from __future__ import annotations

from typing import Type, Dict, Any, List
import json
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .agent_output_schemas import PlannerOutput

logger = logging.getLogger(__name__)


class LLMPlannerAgent(BaseLLMAgent):
    """
    LLM-powered MLOps architecture planning agent.

    Uses GPT-4 reasoning to analyze user constraints and select the optimal
    MLOps capability pattern from the available pattern library.
    """

    SYSTEM_PROMPT = """
You are a senior MLOps architect and cloud systems expert with deep expertise in designing production-quality machine learning platforms.

Your role is to analyze user requirements and constraints, then select the optimal MLOps architecture pattern from a curated library of proven patterns.

## Expertise Areas

### Cloud Platforms & Services
- Deep knowledge of AWS ML services (SageMaker, Lambda, ECS, EKS, Bedrock)
- Understanding of service limits, pricing models, and integration patterns
- Experience with multi-region deployments and disaster recovery

### MLOps Architecture Patterns
- Serverless ML patterns for cost optimization and auto-scaling
- Container-based architectures for complex workloads
- Managed service patterns for operational simplicity
- Hybrid approaches balancing cost, complexity, and performance

### Requirements Analysis
- Ability to map business requirements to technical architecture decisions
- Understanding of trade-offs between cost, performance, and operational complexity
- Experience with compliance requirements (GDPR, HIPAA, SOX, PCI-DSS)
- Knowledge of team capability assessment and technology adoption challenges

## Decision Framework

### Pattern Selection Criteria

**Primary Factors (High Weight)**:
1. **Budget Constraints** - Must fit within specified budget band
2. **Workload Types** - Architecture must support required ML workloads
3. **Scale Requirements** - Pattern must handle expected throughput
4. **Team Expertise** - Complexity level must match team capabilities

**Secondary Factors (Medium Weight)**:
5. **Performance Requirements** - Latency and throughput optimization  
6. **Operational Complexity** - Maintenance and operational overhead
7. **Deployment Preferences** - Serverless vs containers vs managed services
8. **Regional Requirements** - Data locality and compliance needs

**Tertiary Factors (Lower Weight)**:
9. **Integration Requirements** - Existing system compatibility
10. **Future Scalability** - Growth and evolution considerations
11. **Security Posture** - Data classification and protection needs
12. **Monitoring and Observability** - Operational visibility requirements

### Architecture Reasoning Process

1. **Analyze Core Requirements**
   - Extract critical constraints that eliminate pattern options
   - Identify must-have vs nice-to-have capabilities
   - Assess complexity tolerance based on team expertise

2. **Evaluate Pattern Fit**
   - Score each pattern against requirements systematically
   - Consider both immediate needs and future evolution
   - Assess risk factors and potential limitations

3. **Compare Trade-offs**
   - Cost vs performance optimization opportunities
   - Operational complexity vs feature richness
   - Vendor lock-in vs managed service benefits
   - Time-to-market vs long-term maintainability

4. **Select Optimal Pattern**
   - Choose pattern with best overall fit score
   - Ensure critical requirements are met
   - Validate assumptions and highlight key risks

## Response Guidelines

### Selection Rationale
- Provide clear reasoning for pattern selection
- Explain why alternatives were not chosen
- Highlight key trade-offs and decision factors
- Reference specific user requirements that influenced the decision

### Architecture Overview
- Describe the overall system architecture and data flow
- Identify key services and their roles
- Explain deployment and scaling characteristics
- Highlight integration points and dependencies

### Implementation Guidance
- Suggest implementation phases and priorities
- Identify critical success factors
- Highlight potential challenges and mitigation strategies
- Recommend success metrics and monitoring approaches

### Risk Assessment
- Call out architectural risks and limitations
- Suggest risk mitigation strategies
- Identify assumptions that should be validated
- Highlight areas requiring careful implementation

### Cost Analysis
- Explain cost drivers and optimization opportunities
- Validate fit within budget constraints
- Suggest cost monitoring and control strategies
- Identify potential cost scaling surprises

Be thorough but decisive. Provide practical architecture recommendations that teams can actually implement successfully.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="LLM MLOps Planner",
            description="LLM-powered MLOps architecture pattern selection and planning",
            system_prompt=self.SYSTEM_PROMPT,
            model="gpt-4-turbo-preview",
            temperature=0.2,  # Lower temperature for consistent architectural reasoning
        )

        # LLM-powered planner uses reasoning instead of hard-coded patterns

    async def get_structured_output_type(self) -> Type[PlannerOutput]:
        """Return the expected output schema for this agent."""
        return PlannerOutput

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build comprehensive user prompt with all available context.
        """
        if not context.constraints:
            return "ERROR: No constraints found in context. Early-stage agents must be executed first."

        # Get full execution context
        context_summary = context.build_context_summary()

        # Check for previous planning attempts
        previous_outputs = context.get_previous_agent_outputs()
        refinement_context = ""
        if self.agent_type.value in previous_outputs:
            refinement_context = f"""
## Previous Planning Attempt
A previous planning attempt was made. Please consider refining or validating that selection:
{json.dumps(previous_outputs[self.agent_type.value], indent=2)}
"""

        return f"""
Please analyze the following MLOps requirements and select the optimal architecture pattern.

## Project Context
{context_summary}

{refinement_context}

## Planning Request

Based on the extracted constraints and available patterns, please:

1. **Analyze Requirements**: Evaluate the core constraints and their architectural implications
2. **Score Patterns**: Assess how well each pattern fits the requirements 
3. **Select Optimal Pattern**: Choose the best-fit pattern with clear justification
4. **Plan Architecture**: Provide detailed architecture overview and implementation guidance
5. **Assess Risks**: Identify potential challenges and mitigation strategies

## Selection Criteria Priority

Focus on these factors in order of importance:
1. **Budget Compliance** - Must fit within the specified budget band
2. **Workload Support** - Must support the required ML workload types
3. **Scale Capability** - Must handle the expected throughput level
4. **Team Alignment** - Complexity must match team expertise level
5. **Performance Requirements** - Must meet latency and availability needs
6. **Operational Fit** - Must align with preferred deployment patterns

## Response Requirements

Provide a comprehensive PlannerOutput with:
- Selected pattern ID and name with confidence score
- Detailed selection rationale explaining your reasoning
- Analysis of alternatives that were considered
- Complete architecture overview with key services
- Estimated monthly cost breakdown and validation
- Implementation phases and critical success factors
- Potential challenges and success metrics
- Key assumptions made during the planning process

Consider both immediate requirements and future evolution needs. Be practical and implementable.
"""

    async def extract_state_updates(
        self, llm_response: PlannerOutput, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from planner output.
        """
        # LLM-powered planner provides pattern details directly in response

        # Build comprehensive plan object
        plan = {
            "pattern_id": llm_response.selected_pattern_id,
            "pattern_name": llm_response.pattern_name,
            "description": llm_response.architecture_overview,
            "estimated_monthly_cost": llm_response.estimated_monthly_cost,
            "deployment_pattern": llm_response.deployment_approach,
            "services": llm_response.key_services,
            "key_services": llm_response.key_services,
            "deployment_approach": llm_response.deployment_approach,
            "implementation_phases": llm_response.implementation_phases,
            "critical_success_factors": llm_response.critical_success_factors,
            "potential_challenges": llm_response.potential_challenges,
            "success_metrics": llm_response.success_metrics,
            "assumptions": llm_response.assumptions_made,
            "selection_confidence": llm_response.selection_confidence,
            "selection_rationale": llm_response.selection_rationale,
            "alternatives_considered": llm_response.alternatives_considered,
            "decision_criteria": llm_response.decision_criteria,
            "agent_version": "llm_1.0",
        }

        return {
            # Store the complete plan
            "plan": plan,
            # Store planning metadata
            "planning_analysis": {
                "pattern_selected": llm_response.selected_pattern_id,
                "selection_confidence": llm_response.selection_confidence,
                "alternatives_count": len(llm_response.alternatives_considered),
                "estimated_cost": llm_response.estimated_monthly_cost,
                "implementation_phases": len(llm_response.implementation_phases),
            },
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> List[str]:
        """Planning requires constraint extraction and coverage analysis."""
        return [
            AgentType.INTAKE_EXTRACT.value,
            AgentType.COVERAGE_CHECK.value,
            # Note: AdaptiveQuestionsAgent is optional - may or may not have run
        ]

    async def build_next_agent_context(
        self, llm_response: PlannerOutput
    ) -> Dict[str, Any]:
        """Build context for critic agents."""
        return {
            "from_agent": self.agent_type.value,
            "plan_created": True,
            "pattern_selected": llm_response.selected_pattern_id,
            "pattern_name": llm_response.pattern_name,
            "estimated_cost": llm_response.estimated_monthly_cost,
            "selection_confidence": llm_response.selection_confidence,
            "implementation_complexity": len(llm_response.implementation_phases),
            "summary": f"Selected {llm_response.pattern_name} pattern (${llm_response.estimated_monthly_cost}/month, {llm_response.selection_confidence:.1%} confidence)",
        }

    def get_pattern_library_summary(self) -> str:
        """Get a concise summary of MLOps architecture approaches."""
        return """Available MLOps Architecture Patterns:
- Serverless ML Stack: Fully managed AWS services for low-ops overhead
- Containerized ML Platform: Docker-based with ECS/Fargate for flexibility
- Kubernetes ML Platform: Full K8s with Kubeflow for maximum control
- Batch Analytics Stack: Traditional batch processing for analytics workloads

Each pattern is optimized for different workload types, budget constraints, and operational preferences."""


def create_llm_planner_agent() -> LLMPlannerAgent:
    """Factory function to create a configured LLMPlannerAgent."""
    return LLMPlannerAgent()
