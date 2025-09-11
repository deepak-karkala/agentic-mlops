"""
LLM-Powered CostCriticAgent - Intelligent cost analysis and optimization

Transforms cost estimation from hard-coded tables to LLM reasoning.
Uses GPT-4 with current AWS pricing knowledge for accurate cost analysis.
"""

from __future__ import annotations

from typing import Type, Dict, Any, List
import json
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .agent_output_schemas import CostCriticOutput

logger = logging.getLogger(__name__)


class LLMCostCriticAgent(BaseLLMAgent):
    """
    LLM-powered cost analysis and optimization agent.

    Uses GPT-4 expertise to perform comprehensive cost analysis, validation
    against budget constraints, and identification of optimization opportunities.
    """

    SYSTEM_PROMPT = """
You are a senior cloud cost optimization expert and AWS pricing specialist with deep expertise in MLOps cost analysis and financial planning.

Your role is to perform comprehensive cost analysis of proposed MLOps architectures, validate budget compliance, identify optimization opportunities, and provide actionable cost management recommendations.

## Expertise Areas

### AWS Service Pricing
- Deep knowledge of current AWS service pricing models and cost structures
- Understanding of on-demand vs reserved vs spot pricing strategies
- Knowledge of data transfer costs, storage pricing, and compute optimization
- Experience with AWS cost management tools and billing optimization

### MLOps Cost Patterns
- Understanding of ML workload cost characteristics and scaling patterns
- Experience with training vs inference cost optimization strategies
- Knowledge of data storage and processing cost optimization in ML pipelines
- Understanding of model serving cost patterns and optimization techniques

### Cost Modeling and Forecasting
- Ability to model cost scaling with usage patterns and growth
- Experience with break-even analysis and ROI calculations
- Knowledge of cost volatility factors and risk assessment
- Understanding of budget planning and cost governance frameworks

### Cost Optimization Strategies
- Experience with architectural changes that reduce costs
- Knowledge of service substitution and optimization opportunities  
- Understanding of reserved capacity planning and commitment strategies
- Experience with cost monitoring, alerting, and automated optimization

## Cost Analysis Framework

### Cost Estimation Methodology

**Service-Level Cost Analysis**:
- Compute costs: EC2, Lambda, Fargate, SageMaker pricing
- Storage costs: S3, EBS, RDS storage with lifecycle policies
- Data transfer: Inter-service, cross-region, and internet transfer costs
- Managed service fees: RDS, ElastiCache, API Gateway, etc.

**Usage Pattern Modeling**:
- Baseline usage estimation based on throughput requirements
- Peak vs average usage patterns and scaling characteristics
- Seasonal variations and growth projections
- Cost scaling behavior with different usage levels

**Pricing Model Selection**:
- On-demand vs reserved instance cost comparison
- Spot instance opportunities and interruption risk assessment
- Savings plans vs reserved instance optimization
- Volume discounting and enterprise pricing considerations

### Budget Compliance Assessment

**Budget Band Validation**:
- Startup Band ($0-500/month): Focus on cost minimization and serverless patterns
- Growth Band ($500-1000/month): Balance cost and performance optimization
- Enterprise Band ($1000+/month): Focus on performance and advanced features

**Cost Risk Assessment**:
- Probability of exceeding budget based on usage uncertainty
- Cost volatility factors and potential surprises
- Scaling cost projections under different growth scenarios
- Hidden costs and billing complexity assessment

### Cost Optimization Framework

**Immediate Optimization Opportunities**:
- Right-sizing compute resources based on actual requirements
- Storage optimization through lifecycle policies and compression
- Reserved capacity opportunities with clear ROI calculations
- Service substitution for better price-performance ratios

**Architectural Cost Optimizations**:
- Serverless vs container cost trade-offs for different workloads
- Data processing optimization through batch scheduling
- Caching strategies to reduce compute and data transfer costs
- Multi-region deployment cost optimization strategies

**Long-term Cost Management**:
- Cost monitoring and alerting strategy recommendations
- Budget governance and approval workflow requirements
- Cost allocation and chargeback mechanism design
- Regular cost review and optimization process establishment

## Analysis Guidelines

### Current AWS Pricing Context (2024)

**Key Service Pricing Patterns**:
- Lambda: $0.0000166667 per GB-second + $0.20 per 1M requests
- EC2: Varies by instance type, typically $0.0464-$0.7776 per hour for common types
- S3: $0.023 per GB/month (Standard), with tiering for infrequent access
- RDS: $0.017-$0.68 per hour depending on instance type and engine
- SageMaker: $0.269-$31.218 per hour for training, $0.048-$6.786 per hour for inference

**Cost Optimization Patterns**:
- Reserved instances: Typically 30-60% savings for predictable workloads
- Spot instances: Up to 90% savings for fault-tolerant workloads
- Serverless optimization: Cost-effective for variable and spiky workloads
- Storage optimization: Significant savings through intelligent tiering

### Context-Aware Cost Analysis

**Workload-Specific Considerations**:
- **Batch Training**: Focus on spot instances and scheduled execution optimization
- **Real-time Inference**: Balance latency requirements with cost optimization
- **Data Processing**: Optimize for throughput and minimize data transfer costs
- **Experimentation**: Cost-effective environments for development and testing

**Scale-Dependent Optimization**:
- **Low Scale**: Maximize serverless and managed service usage
- **Medium Scale**: Optimize reserved capacity and right-sizing
- **High Scale**: Focus on custom optimization and enterprise discounts
- **Variable Scale**: Implement auto-scaling and cost monitoring

### Cost Confidence Assessment

**High Confidence Estimates** (>90% accuracy):
- Well-defined usage patterns with historical data
- Mature services with stable pricing
- Conservative scaling assumptions
- Standard deployment patterns

**Medium Confidence Estimates** (70-90% accuracy):
- New workloads with estimated usage patterns
- Mixed service architectures with multiple cost drivers
- Moderate scaling uncertainty
- Regional pricing variations

**Low Confidence Estimates** (<70% accuracy):
- Highly variable or unpredictable workloads
- New or changing service pricing models
- Significant usage pattern uncertainty
- Complex data transfer patterns

## Response Format

Your cost analysis must be comprehensive, practical, and actionable, providing clear guidance for cost optimization and budget management.

Focus on major cost drivers and optimization opportunities that meaningfully impact the overall budget.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.CRITIC_COST,
            name="LLM Cost Critic",
            description="LLM-powered cost analysis and budget validation",
            system_prompt=self.SYSTEM_PROMPT,
            model="gpt-4-turbo-preview",
            temperature=0.1,  # Very low temperature for consistent cost analysis
        )

    async def get_structured_output_type(self) -> Type[CostCriticOutput]:
        """Return the expected output schema for this agent."""
        return CostCriticOutput

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build comprehensive user prompt with plan, constraints, and previous analysis.
        """
        # Get the current plan
        plan = context.get_current_plan()
        if not plan:
            return (
                "ERROR: No plan found in context. PlannerAgent must be executed first."
            )

        # Get constraints and context
        constraints_summary = (
            context.constraints.to_context_string()
            if context.constraints
            else "No constraints available"
        )
        context_summary = context.build_context_summary()

        # Get technical analysis if available
        tech_analysis = context.get_technical_analysis()
        tech_context = ""
        if tech_analysis:
            tech_context = f"""
## Technical Analysis Context
The technical analysis has identified the following considerations that may impact costs:
- Feasibility Score: {tech_analysis.get("overall_feasibility_score", "N/A")}
- Performance Bottlenecks: {", ".join(tech_analysis.get("performance_bottlenecks", [])[:3])}
- Scaling Concerns: {", ".join(tech_analysis.get("scalability_risks", [])[:3])}
- Operational Complexity: {tech_analysis.get("operational_complexity", "Not specified")}
"""

        # Get previous cost analysis if this is a refinement
        previous_outputs = context.get_previous_agent_outputs()
        refinement_context = ""
        if self.agent_type.value in previous_outputs:
            refinement_context = f"""
## Previous Cost Analysis
A previous cost analysis was conducted. Please consider refining or updating that analysis:
{json.dumps(previous_outputs[self.agent_type.value], indent=2)}
"""

        return f"""
Please perform a comprehensive cost analysis of the proposed MLOps architecture.

## Project Context
{context_summary}

## Current Constraints
{constraints_summary}

## Proposed Architecture Plan
```json
{json.dumps(plan, indent=2)}
```

{tech_context}

{refinement_context}

## Cost Analysis Request

Please conduct a thorough cost analysis focusing on:

### 1. Detailed Cost Estimation
- Service-by-service monthly cost breakdown with current AWS pricing
- Infrastructure costs (compute, storage, networking)
- Operational costs (monitoring, logging, data transfer)
- Usage pattern assumptions and scaling characteristics

### 2. Budget Compliance Analysis
- Validation against specified budget band constraints
- Budget utilization percentage and risk assessment
- Cost distribution analysis across service categories
- Variable vs fixed cost breakdown

### 3. Cost Driver Identification
- Primary cost drivers ranked by impact (top 3-5)
- Cost scaling factors with usage growth
- Hidden costs and potential billing surprises
- Cost volatility factors and seasonal variations

### 4. Optimization Opportunities
- Immediate cost reduction recommendations with specific savings estimates
- Reserved instance opportunities and ROI calculations
- Alternative architecture options for cost reduction
- Right-sizing opportunities and service substitution benefits

### 5. Cost Management Strategy
- Cost monitoring and alerting recommendations
- Budget governance and approval workflow requirements
- Cost optimization automation opportunities
- Regular review and optimization process recommendations

## Analysis Context Considerations

**Budget Band Focus**:
- Startup ($0-500/month): Minimize costs, maximize serverless usage
- Growth ($500-1000/month): Balance cost and performance
- Enterprise ($1000+/month): Optimize for performance and features

**Workload Considerations**:
- Focus on workload-specific cost optimization patterns
- Consider usage variability and scaling requirements
- Account for data processing and model training cost patterns
- Factor in compliance and security cost implications

**Technical Integration**:
- Consider technical risks that may increase operational costs
- Account for monitoring and alerting costs based on complexity
- Factor in potential over-provisioning due to performance requirements
- Consider disaster recovery and backup cost implications

## Expected Deliverables

Provide a comprehensive CostCriticOutput including:
- Total estimated monthly cost with confidence level
- Detailed service-by-service cost breakdown
- Budget compliance status and risk assessment
- Primary cost drivers and optimization opportunities
- Specific recommendations with estimated savings
- Cost scaling projections for different usage levels
- Cost monitoring and governance recommendations
- Hidden costs and billing complexity considerations

Be thorough but practical - focus on cost factors that meaningfully impact the budget and provide actionable optimization guidance.
"""

    async def extract_state_updates(
        self, llm_response: CostCriticOutput, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from cost criticism output.
        """
        # Build comprehensive cost analysis
        cost_analysis = {
            "estimated_monthly_cost": llm_response.estimated_monthly_cost,
            "cost_confidence": llm_response.cost_confidence,
            "cost_analysis_summary": llm_response.cost_analysis_summary,
            "service_costs": llm_response.service_costs,
            "infrastructure_costs": llm_response.infrastructure_costs,
            "operational_costs": llm_response.operational_costs,
            "primary_cost_drivers": llm_response.primary_cost_drivers,
            "cost_distribution": llm_response.cost_distribution,
            "variable_vs_fixed": llm_response.variable_vs_fixed,
            "budget_compliance_status": llm_response.budget_compliance_status,
            "budget_utilization": llm_response.budget_utilization,
            "budget_risk_assessment": llm_response.budget_risk_assessment,
            "cost_scaling_factors": llm_response.cost_scaling_factors,
            "scaling_cost_projections": llm_response.scaling_cost_projections,
            "break_even_analysis": llm_response.break_even_analysis,
            "cost_optimization_recommendations": llm_response.cost_optimization_recommendations,
            "alternative_architectures": llm_response.alternative_architectures,
            "reserved_instance_opportunities": llm_response.reserved_instance_opportunities,
            "potential_hidden_costs": llm_response.potential_hidden_costs,
            "cost_volatility_factors": llm_response.cost_volatility_factors,
            "billing_complexity_notes": llm_response.billing_complexity_notes,
            "expected_roi_timeline": llm_response.expected_roi_timeline,
            "value_propositions": llm_response.value_propositions,
            "cost_vs_benefit_analysis": llm_response.cost_vs_benefit_analysis,
            "cost_monitoring_strategy": llm_response.cost_monitoring_strategy,
            "budget_alerts_recommended": llm_response.budget_alerts_recommended,
            "cost_governance_needs": llm_response.cost_governance_needs,
            "cost_assumptions": llm_response.cost_assumptions,
            "pricing_methodology": llm_response.pricing_methodology,
            "cost_analysis_limitations": llm_response.cost_analysis_limitations,
            "agent_version": "llm_1.0",
        }

        return {
            # Store the complete cost analysis
            "cost_estimate": cost_analysis,
            # Store key metrics for easy access
            "estimated_monthly_cost": llm_response.estimated_monthly_cost,
            "cost_confidence": llm_response.cost_confidence,
            "budget_compliance_status": llm_response.budget_compliance_status,
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> List[str]:
        """Cost criticism requires a plan and optionally technical analysis."""
        return [
            AgentType.PLANNER.value
            # TechCritic is optional but beneficial for context
        ]

    async def build_next_agent_context(
        self, llm_response: CostCriticOutput
    ) -> Dict[str, Any]:
        """Build context for policy engine agent."""
        return {
            "from_agent": self.agent_type.value,
            "cost_analysis_complete": True,
            "estimated_monthly_cost": llm_response.estimated_monthly_cost,
            "cost_confidence": llm_response.cost_confidence,
            "budget_compliance": llm_response.budget_compliance_status,
            "budget_utilization": llm_response.budget_utilization,
            "optimization_opportunities": len(
                llm_response.cost_optimization_recommendations
            ),
            "hidden_costs_identified": len(llm_response.potential_hidden_costs),
            "summary": f"Cost analysis complete: ${llm_response.estimated_monthly_cost}/month ({llm_response.budget_compliance_status} budget compliance, {llm_response.cost_confidence:.1%} confidence)",
        }


def create_llm_cost_critic_agent() -> LLMCostCriticAgent:
    """Factory function to create a configured LLMCostCriticAgent."""
    return LLMCostCriticAgent()
