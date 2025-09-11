"""
IntakeExtractAgent - LLM-powered natural language constraint extraction

Transforms unstructured user input into formal MLOpsConstraints using
intelligent parsing and reasoning. First agent in the processing chain.
"""

from __future__ import annotations

from typing import Type, Dict, Any
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .constraint_schema import ConstraintExtractionResult

logger = logging.getLogger(__name__)


class IntakeExtractAgent(BaseLLMAgent):
    """
    LLM-powered agent for extracting structured constraints from natural language.

    This agent performs sophisticated parsing of user requirements into the
    formal MLOpsConstraints schema using GPT-4's reasoning capabilities.
    """

    SYSTEM_PROMPT = """
You are an expert MLOps requirements analyst and consultant with deep expertise in cloud platforms, machine learning operations, and enterprise architecture.

Your role is to carefully parse natural language MLOps project descriptions and extract structured constraint information. You have extensive experience with:
- AWS cloud services and pricing models
- Machine learning workload patterns and requirements
- Data classification and compliance standards (GDPR, HIPAA, SOX, etc.)
- Team capabilities and operational constraints
- Budget planning and cost optimization
- Performance requirements and scalability patterns

## Instructions

Parse the user's MLOps project request and extract information for these key areas:

### Core Requirements
- **Project Description**: Clear summary of what they want to build
- **Budget Band**: startup ($0-500/month), growth ($500-1000/month), enterprise ($1000+/month)
- **Deployment Preference**: serverless, containers, kubernetes, managed services

### Workload Characteristics
- **Workload Types**: batch_training, online_inference, streaming_inference, feature_engineering, data_processing, model_experimentation, batch_inference
- **Expected Throughput**: low (<1K/day), medium (1K-100K/day), high (100K-1M/day), very_high (>1M/day)
- **Latency Requirements**: Response time requirements in milliseconds

### Data and Compliance
- **Data Classification**: public, internal, sensitive, restricted
- **Data Sources**: Types of data inputs (databases, APIs, files, streaming)
- **Compliance Requirements**: Required standards (GDPR, HIPAA, SOX, PCI-DSS, etc.)

### Infrastructure Preferences
- **Regions**: AWS regions for deployment
- **Availability Target**: Target uptime percentage (95.0 to 99.999)
- **Disaster Recovery**: Whether DR capabilities are required

### Technical Requirements
- **Model Types**: regression, classification, NLP, computer_vision, recommendation, etc.
- **Model Size**: small, medium, large, very_large
- **Training Frequency**: one_time, weekly, daily, real_time

### Team and Operations
- **Team Size**: Number of people working on the project
- **Team Expertise**: Areas where the team has experience
- **Operational Preferences**: How they prefer to manage systems

### Quality Attributes
- **Monitoring Requirements**: Specific monitoring needs
- **Logging Requirements**: Audit and compliance logging needs
- **Testing Requirements**: Testing strategy preferences

## Extraction Guidelines

1. **Be Conservative**: Only extract information you're confident about from the text
2. **Flag Uncertainty**: Mark fields where you're making assumptions
3. **Identify Gaps**: Note critical missing information
4. **Use Defaults Wisely**: Apply reasonable defaults based on context clues
5. **Extract Confidence**: Provide overall confidence in your extraction

## Response Format

You must respond with a valid JSON object matching the ConstraintExtractionResult schema. Include:
- Complete MLOpsConstraints object with all extracted information
- Extraction confidence score (0.0-1.0)
- List of uncertain fields where confidence is low
- Clear rationale explaining your extraction decisions
- Boolean indicating whether follow-up questions are needed

## Examples of Good Extraction

If a user says "We need a real-time recommendation system for our e-commerce site, handling about 50K requests per day, budget is tight": 
- workload_types: [online_inference]
- expected_throughput: medium
- budget_band: startup (implied by "tight budget")
- model_types: [recommendation]
- uncertain_fields: [data_classification, regions, compliance_requirements]

Be thorough but practical. Focus on information that will meaningfully impact architecture decisions.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.INTAKE_EXTRACT,
            name="Intake Extract Agent",
            description="Parse natural language input into structured MLOps constraints",
            system_prompt=self.SYSTEM_PROMPT,
            model="gpt-4-turbo-preview",
            temperature=0.3,  # Lower temperature for more consistent extraction
        )

    async def get_structured_output_type(self) -> Type[ConstraintExtractionResult]:
        """Return the expected output schema for this agent."""
        return ConstraintExtractionResult

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build user prompt from the original user input.

        Since this is the first agent in the chain, we primarily work with
        the original user message.
        """
        user_input = context.user_input

        # Check if there are any previous constraint extractions to refine
        previous_outputs = context.get_previous_agent_outputs()
        if self.agent_type.value in previous_outputs:
            return f"""
REFINEMENT REQUEST: Please refine the previous constraint extraction based on new information or corrections.

Original User Input:
{user_input}

Previous Extraction:
{previous_outputs[self.agent_type.value]}

Please provide an updated and improved constraint extraction, incorporating any new insights or corrections.
"""

        return f"""
Please parse the following MLOps project request and extract structured constraint information:

USER REQUEST:
{user_input}

Extract all relevant constraints and requirements from this request. Be thorough but conservative - only extract information you're confident about based on the provided text.

Pay special attention to:
- Budget implications and organizational size clues
- Technical complexity and deployment preferences  
- Data sensitivity and compliance hints
- Performance and scale requirements
- Team capability indicators

Provide a complete ConstraintExtractionResult with your analysis.
"""

    async def extract_state_updates(
        self, llm_response: ConstraintExtractionResult, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from the constraint extraction result.

        This agent adds the extracted constraints to the state and updates
        confidence tracking information.
        """
        return {
            # Store the formal constraint schema
            "constraints": llm_response.constraints.model_dump(),
            # Track extraction metadata
            "constraint_extraction": {
                "confidence": llm_response.extraction_confidence,
                "uncertain_fields": llm_response.uncertain_fields,
                "rationale": llm_response.extraction_rationale,
                "follow_up_needed": llm_response.follow_up_needed,
                "extraction_method": "llm_gpt4",
                "agent_version": "1.0",
            },
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> list[str]:
        """This is the first agent in the chain, no predecessors required."""
        return []

    async def build_next_agent_context(
        self, llm_response: ConstraintExtractionResult
    ) -> Dict[str, Any]:
        """Build context for the next agent (CoverageCheckAgent)."""
        return {
            "from_agent": self.agent_type.value,
            "constraints_extracted": True,
            "extraction_confidence": llm_response.extraction_confidence,
            "follow_up_recommended": llm_response.follow_up_needed,
            "summary": f"Extracted {len([f for f in llm_response.constraints.model_dump() if llm_response.constraints.model_dump()[f] is not None])} constraint fields with {llm_response.extraction_confidence:.1%} confidence",
        }


def create_intake_extract_agent() -> IntakeExtractAgent:
    """Factory function to create a configured IntakeExtractAgent."""
    return IntakeExtractAgent()
