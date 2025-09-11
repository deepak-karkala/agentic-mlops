"""
LLM-Powered TechCriticAgent - Intelligent technical architecture analysis

Transforms technical criticism from hard-coded rules to LLM reasoning.
Uses GPT-4 to perform comprehensive technical feasibility analysis.
"""

from __future__ import annotations

from typing import Type, Dict, Any, List
import json
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .agent_output_schemas import TechCriticOutput

logger = logging.getLogger(__name__)


class LLMTechCriticAgent(BaseLLMAgent):
    """
    LLM-powered technical architecture critic agent.

    Uses GPT-4 expertise to analyze technical feasibility, identify risks,
    bottlenecks, and architectural concerns in the proposed MLOps plan.
    """

    SYSTEM_PROMPT = """
You are a senior technical architect and distributed systems expert specializing in MLOps and cloud-native architectures.

Your role is to perform comprehensive technical analysis of proposed MLOps architectures, identifying risks, bottlenecks, failure points, and providing actionable recommendations for improvement.

## Expertise Areas

### Distributed Systems Architecture
- Deep understanding of service architectures, coupling patterns, and failure domains
- Experience with microservices, event-driven architectures, and data flow patterns
- Knowledge of consensus algorithms, consistency patterns, and CAP theorem implications

### Cloud Platform Expertise  
- Extensive AWS service knowledge including limits, failure modes, and integration patterns
- Understanding of managed service capabilities and operational trade-offs
- Experience with multi-region deployments, disaster recovery, and high availability patterns

### ML Systems Architecture
- Knowledge of ML pipeline architectures and data flow patterns
- Understanding of model serving patterns, caching strategies, and performance optimization
- Experience with batch vs real-time processing trade-offs and scaling characteristics

### Performance and Scalability
- Deep understanding of bottleneck analysis and capacity planning
- Experience with load testing, performance profiling, and optimization strategies
- Knowledge of caching patterns, database scaling, and CDN optimization

### Operational Complexity Assessment
- Understanding of monitoring, alerting, and observability requirements
- Experience with deployment patterns, rollback strategies, and change management
- Knowledge of security patterns, compliance requirements, and operational overhead

## Analysis Framework

### Technical Feasibility Assessment (0.0 to 1.0 score)

**Architecture Soundness**:
- Service decomposition and boundary design quality
- Data flow and integration pattern appropriateness
- Technology stack consistency and compatibility
- Adherence to architectural best practices and patterns

**Performance Analysis**:
- Throughput and latency capability assessment
- Bottleneck identification and impact analysis
- Scaling behavior and capacity planning validation
- Resource utilization and cost-performance optimization

**Reliability and Availability**:
- Single point of failure identification and mitigation
- Failure domain analysis and isolation strategies
- Error handling, retry patterns, and graceful degradation
- Disaster recovery and business continuity planning

### Risk Assessment Categories

**High Severity Risks** (Must Address):
- Single points of failure that could cause system-wide outages
- Performance bottlenecks that violate critical SLA requirements
- Security vulnerabilities with significant business impact
- Scalability limits that could block business growth
- Technology complexity that exceeds team capabilities

**Medium Severity Risks** (Should Address):
- Operational complexity that increases maintenance overhead
- Integration challenges that could delay implementation
- Capacity constraints that may require careful monitoring
- Technology dependencies that create vendor lock-in concerns

**Low Severity Risks** (Monitor):
- Performance optimizations with marginal business impact
- Redundancy opportunities that improve resilience
- Monitoring and alerting enhancements
- Future scalability considerations beyond immediate needs

### Architecture Pattern Analysis

**Serverless Architectures**:
- Cold start impact on latency requirements
- Concurrency limits and throughput bottlenecks  
- Function timeout constraints for batch processing
- State management and data sharing patterns
- Cost implications at scale and optimization strategies

**Container-Based Architectures**:
- Orchestration complexity and operational overhead
- Resource allocation and scaling characteristics
- Security boundaries and isolation concerns
- Networking patterns and service discovery
- Storage persistence and data lifecycle management

**Managed Service Architectures**:
- Service limits and scaling boundaries
- Integration complexity and data flow patterns
- Vendor lock-in and migration considerations
- Cost optimization and reserved capacity planning
- Operational simplicity vs customization trade-offs

**Hybrid Architectures**:
- Integration complexity between different patterns
- Consistency guarantees across system boundaries
- Operational overhead of managing multiple patterns
- Data flow and synchronization challenges
- Cost optimization across diverse service types

## Analysis Guidelines

### Systematic Evaluation Process

1. **Architecture Review**: Analyze overall system design and component interactions
2. **Risk Identification**: Identify technical risks across all severity levels
3. **Bottleneck Analysis**: Assess performance bottlenecks and capacity constraints
4. **Failure Domain Mapping**: Identify failure points and assess blast radius
5. **Scalability Assessment**: Evaluate scaling characteristics and limits
6. **Security Analysis**: Review security boundaries and attack vectors
7. **Operational Complexity**: Assess monitoring, maintenance, and operational requirements

### Context-Aware Analysis

Consider the specific context:
- **Team Expertise**: Match recommendations to team capabilities and experience level
- **Business Requirements**: Align technical solutions with business criticality and SLAs
- **Budget Constraints**: Balance technical excellence with cost optimization
- **Timeline Pressures**: Consider implementation complexity vs time-to-market requirements
- **Growth Projections**: Evaluate architecture ability to handle future scale requirements

### Recommendation Quality

Provide recommendations that are:
- **Specific and Actionable**: Clear steps that can be implemented
- **Risk-Prioritized**: Focus on highest-impact issues first
- **Implementation-Aware**: Consider team capabilities and constraints
- **Cost-Conscious**: Balance technical improvements with budget impact
- **Measurable**: Include metrics and success criteria where possible

## Response Format

Your analysis must be comprehensive yet practical, focusing on issues that meaningfully impact system reliability, performance, and maintainability.

Provide specific, actionable recommendations with clear rationale and implementation guidance.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.CRITIC_TECH,
            name="LLM Technical Critic",
            description="LLM-powered technical architecture analysis and risk assessment",
            system_prompt=self.SYSTEM_PROMPT,
            model="gpt-4-turbo-preview",
            temperature=0.1,  # Very low temperature for consistent technical analysis
        )

    async def get_structured_output_type(self) -> Type[TechCriticOutput]:
        """Return the expected output schema for this agent."""
        return TechCriticOutput

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build comprehensive user prompt with plan details and constraints.
        """
        # Get the current plan
        plan = context.get_current_plan()
        if not plan:
            return (
                "ERROR: No plan found in context. PlannerAgent must be executed first."
            )

        # Get constraints and other context
        constraints_summary = (
            context.constraints.to_context_string()
            if context.constraints
            else "No constraints available"
        )
        context_summary = context.build_context_summary()

        # Get previous technical analysis if this is a refinement
        previous_outputs = context.get_previous_agent_outputs()
        refinement_context = ""
        if self.agent_type.value in previous_outputs:
            refinement_context = f"""
## Previous Technical Analysis
A previous technical analysis was conducted. Please consider refining or updating that analysis:
{json.dumps(previous_outputs[self.agent_type.value], indent=2)}
"""

        return f"""
Please perform a comprehensive technical analysis of the proposed MLOps architecture.

## Project Context
{context_summary}

## Current Constraints  
{constraints_summary}

## Proposed Architecture Plan
```json
{json.dumps(plan, indent=2)}
```

{refinement_context}

## Technical Analysis Request

Please conduct a thorough technical feasibility analysis focusing on:

### 1. Architecture Soundness Assessment
- Overall architectural design quality and best practice adherence
- Service boundaries, coupling patterns, and integration approaches
- Data flow patterns and consistency guarantees
- Technology stack compatibility and maturity

### 2. Performance and Scalability Analysis
- Throughput and latency capability against requirements
- Performance bottleneck identification and impact assessment
- Scaling characteristics and capacity planning validation
- Resource utilization patterns and optimization opportunities

### 3. Reliability and Availability Review
- Single point of failure identification and mitigation strategies
- Failure domain analysis and blast radius assessment
- Error handling patterns and graceful degradation capabilities
- Disaster recovery and business continuity planning

### 4. Security and Compliance Analysis
- Security boundaries and access control patterns
- Data protection and encryption strategies
- Compliance requirement alignment (based on data classification)
- Attack vector assessment and mitigation strategies

### 5. Operational Complexity Assessment
- Monitoring and observability requirements
- Deployment complexity and change management needs
- Maintenance overhead and skill requirements
- Troubleshooting and debugging capabilities

### 6. Risk Assessment and Mitigation
- Critical risks that could cause system failures
- Implementation risks that could delay project delivery
- Operational risks that could impact ongoing maintenance
- Mitigation strategies with implementation priorities

## Analysis Context Considerations

Focus your analysis on:
- **Team Capabilities**: Consider the complexity relative to team expertise
- **Business Criticality**: Align risk assessment with business impact
- **Cost Constraints**: Balance technical excellence with budget limitations
- **Implementation Timeline**: Consider time-to-market pressures
- **Future Growth**: Evaluate architecture evolution capabilities

## Expected Deliverables

Provide a comprehensive TechCriticOutput including:
- Overall technical feasibility score and architecture confidence
- Detailed risk analysis across all categories
- Specific bottleneck identification with impact assessment
- Failure domain analysis with mitigation recommendations
- Security assessment aligned with data classification
- Actionable recommendations prioritized by impact
- Implementation complexity assessment
- Monitoring and operational requirements

Be thorough but practical - focus on issues that meaningfully impact system success.
"""

    async def extract_state_updates(
        self, llm_response: TechCriticOutput, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from technical criticism output.
        """
        # Build comprehensive technical analysis
        tech_analysis = {
            "overall_feasibility_score": llm_response.technical_feasibility_score,
            "architecture_confidence": llm_response.architecture_confidence,
            "criticism_summary": llm_response.criticism_summary,
            "technical_risks": llm_response.technical_risks,
            "architecture_concerns": llm_response.architecture_concerns,
            "scalability_risks": llm_response.scalability_risks,
            "security_concerns": llm_response.security_concerns,
            "performance_bottlenecks": llm_response.performance_bottlenecks,
            "capacity_constraints": llm_response.capacity_constraints,
            "integration_challenges": llm_response.integration_challenges,
            "single_points_of_failure": llm_response.single_points_of_failure,
            "failure_domains": llm_response.failure_domains,
            "disaster_recovery_gaps": llm_response.disaster_recovery_gaps,
            "risk_mitigation_strategies": llm_response.risk_mitigation_strategies,
            "architecture_improvements": llm_response.architecture_improvements,
            "monitoring_requirements": llm_response.monitoring_requirements,
            "operational_complexity": llm_response.operational_complexity,
            "maintenance_requirements": llm_response.maintenance_requirements,
            "skill_requirements": llm_response.skill_requirements,
            "availability_impact": llm_response.availability_impact,
            "performance_impact": llm_response.performance_impact,
            "security_impact": llm_response.security_impact,
            "analysis_assumptions": llm_response.analysis_assumptions,
            "analysis_limitations": llm_response.analysis_limitations,
            "agent_version": "llm_1.0",
        }

        return {
            # Store the complete technical analysis
            "tech_critique": tech_analysis,
            # Store key metrics for easy access
            "technical_feasibility_score": llm_response.technical_feasibility_score,
            "architecture_confidence": llm_response.architecture_confidence,
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> List[str]:
        """Technical criticism requires a plan to analyze."""
        return [AgentType.PLANNER.value]

    async def build_next_agent_context(
        self, llm_response: TechCriticOutput
    ) -> Dict[str, Any]:
        """Build context for cost critic agent."""
        return {
            "from_agent": self.agent_type.value,
            "technical_analysis_complete": True,
            "feasibility_score": llm_response.technical_feasibility_score,
            "architecture_confidence": llm_response.architecture_confidence,
            "critical_risks_count": len(llm_response.technical_risks),
            "bottlenecks_identified": len(llm_response.performance_bottlenecks),
            "security_concerns_count": len(llm_response.security_concerns),
            "summary": f"Technical analysis complete: {llm_response.technical_feasibility_score:.1%} feasibility, {len(llm_response.technical_risks)} critical risks, {llm_response.architecture_confidence:.1%} confidence",
        }


def create_llm_tech_critic_agent() -> LLMTechCriticAgent:
    """Factory function to create a configured LLMTechCriticAgent."""
    return LLMTechCriticAgent()
