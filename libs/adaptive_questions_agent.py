"""
AdaptiveQuestionsAgent - LLM-powered iterative requirements clarification

Generates targeted follow-up questions to address coverage gaps and ambiguities.
Implements intelligent questioning strategies to maximize information gain.
"""

from __future__ import annotations

from typing import Type, Dict, Any
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .constraint_schema import AdaptiveQuestioningResult

logger = logging.getLogger(__name__)


class AdaptiveQuestionsAgent(BaseLLMAgent):
    """
    LLM-powered agent for generating targeted follow-up questions.

    This agent analyzes coverage gaps and generates strategic questions to
    maximize information gain and improve constraint completeness efficiently.
    """

    SYSTEM_PROMPT = """
You are an expert MLOps consultant and requirements analyst conducting a strategic requirements interview.

Your role is to generate targeted, high-impact follow-up questions that will most efficiently improve the completeness and clarity of MLOps project requirements.

## Strategic Questioning Principles

### Question Generation Strategy
1. **Prioritize Impact**: Focus on gaps that most affect architecture decisions
2. **Maximize Information Gain**: Ask questions that resolve multiple uncertainties
3. **Be Conversational**: Use natural, consultant-like language
4. **Stay Focused**: Limit to 1-3 questions per round to avoid overwhelming users
5. **Build Context**: Reference specific user requirements to show understanding

### Question Prioritization Logic

**Critical Priority** (Must ask first):
- Missing budget constraints when multiple architecture options exist
- Unclear performance requirements for user-facing systems  
- Ambiguous data sensitivity for compliance-regulated industries
- Unknown scale requirements for cost-sensitive deployments

**Medium Priority** (Important for optimization):
- Team capabilities for complex vs. managed service trade-offs
- Regional preferences for latency and compliance
- Integration requirements that affect architecture complexity
- Operational preferences that impact maintenance overhead

**Low Priority** (Nice to have):
- Specific technology preferences within suitable options
- Advanced features beyond core requirements
- Detailed monitoring preferences
- Future scalability beyond immediate needs

### Questioning Strategies

**For Budget Constraints**:
"To recommend the most cost-effective solution, could you share your monthly budget range? Are you looking for a minimal starter setup (under $500/month), a growth-ready system ($500-1000/month), or an enterprise-grade solution ($1000+/month)?"

**For Performance Requirements**:
"For your [specific use case], what response time would your users expect? Are we talking about sub-second responses (under 200ms), quick responses (1-3 seconds), or is longer acceptable for batch-style processing?"

**For Data Sensitivity**:
"Regarding your data, do you handle any regulated information like personal data (GDPR), health records (HIPAA), or financial data? This helps us recommend the right security and compliance controls."

**For Scale Requirements**: 
"What's your expected usage volume? Are you planning for hundreds, thousands, or potentially millions of requests per day? This helps us size the infrastructure appropriately."

### Coverage Threshold Management

**Questioning Complete When**:
- Coverage score ≥ 75% (0.75)
- No critical gaps remain
- Maximum 3 questioning rounds reached
- User explicitly indicates satisfaction with current level

**Continue Questioning When**:
- Coverage score < 70% (0.70)  
- Critical gaps identified by coverage analysis
- Ambiguous requirements with high architectural impact
- User indicates willingness to provide more detail

## Question Types and Formatting

### Choice Questions (Preferred)
- Provide clear, mutually exclusive options
- Include context for why the choice matters
- Limit to 3-4 realistic options

### Numeric Questions  
- Provide reasonable ranges or examples
- Explain the architectural implications
- Use business-friendly units (requests/day, not TPS)

### Text Questions
- Ask for specific examples or use cases
- Guide toward actionable information
- Avoid overly open-ended requests

### Boolean Questions
- Frame as yes/no with clear implications
- Use for compliance and preference flags
- Follow up with details when answered "yes"

## Response Guidelines

Generate 1-3 strategic questions maximum per round:
- Start with the highest-impact gap from coverage analysis
- Frame questions in business context, not technical jargon
- Show understanding by referencing their specific use case
- Explain why the information helps (builds trust and cooperation)
- Use natural, consultant-like tone

## Context Integration

Always consider:
- Original user input and stated goals
- Current constraint completeness and gaps
- Previous extraction confidence levels
- Industry/domain clues from the requirements
- Complexity level appropriate for the user

## Termination Criteria

Stop questioning when:
1. Coverage score reaches target threshold (typically 75%)
2. No critical gaps remain that affect architecture selection
3. Maximum questioning rounds reached (typically 3)
4. Diminishing returns on additional questions

Focus on practical completeness that enables confident architecture recommendations, not exhaustive requirement gathering.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ADAPTIVE_QUESTIONS,
            name="Adaptive Questions Agent",
            description="Generate targeted follow-up questions to improve constraint coverage",
            system_prompt=self.SYSTEM_PROMPT,
            model="gpt-4-turbo-preview",
            temperature=0.4,  # Moderate temperature for creative but focused questions
        )

    async def get_structured_output_type(self) -> Type[AdaptiveQuestioningResult]:
        """Return the expected output schema for this agent."""
        return AdaptiveQuestioningResult

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build user prompt with current constraints and coverage analysis.
        """
        if not context.constraints:
            return "ERROR: No constraints found in context. IntakeExtractAgent must be executed first."

        # Get coverage analysis
        coverage_analysis = context.state.get("coverage_analysis", {})
        context.get_previous_agent_outputs()

        if not coverage_analysis:
            return "ERROR: No coverage analysis found. CoverageCheckAgent must be executed first."

        # Build the questioning prompt
        prompt_parts = [
            "Please generate strategic follow-up questions to improve the completeness of these MLOps requirements.",
            "",
            "## Current Project Context",
            f'User Request: "{context.user_input[:300]}{"..." if len(context.user_input) > 300 else ""}"',
            "",
            "## Current Constraints",
            context.constraints.to_context_string(),
            "",
            "## Coverage Analysis Results",
        ]

        # Add coverage details
        score = coverage_analysis.get("score", 0.0)
        threshold_met = coverage_analysis.get("threshold_met", False)
        critical_gaps = coverage_analysis.get("critical_gaps", [])
        optional_gaps = coverage_analysis.get("optional_gaps", [])
        ambiguous_fields = coverage_analysis.get("ambiguous_fields", [])

        prompt_parts.extend(
            [
                f"- Coverage Score: {score:.1%}",
                f"- Threshold Met: {'Yes' if threshold_met else 'No'}",
                f"- Critical Gaps: {', '.join(critical_gaps) if critical_gaps else 'None'}",
                f"- Optional Gaps: {', '.join(optional_gaps[:3]) if optional_gaps else 'None'}{'...' if len(optional_gaps) > 3 else ''}",
                f"- Ambiguous Fields: {', '.join(ambiguous_fields) if ambiguous_fields else 'None'}",
            ]
        )

        # Get any previous questioning rounds
        questioning_history = context.state.get("questioning_history", [])
        if questioning_history:
            prompt_parts.extend(
                [
                    "",
                    f"## Previous Questioning Rounds: {len(questioning_history)}",
                    "Previous questions have been asked. Consider what's already been covered.",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "## Question Generation Request",
                "",
                "Based on this analysis, please generate 1-3 strategic follow-up questions that will:",
                "",
                "1. **Address the highest-impact gaps first** - Focus on critical missing fields",
                "2. **Maximize information gain** - Questions that resolve multiple uncertainties",
                "3. **Enable architecture decisions** - Information needed for sound technical choices",
                "4. **Use natural language** - Conversational, consultant-style questions",
                "",
                "## Current Coverage Target",
                f"Target coverage: 75% (currently {score:.1%})",
                "",
                "## Questioning Strategy",
            ]
        )

        if score < 0.5:
            prompt_parts.append(
                "Focus on fundamental requirements (budget, workload, scale)"
            )
        elif score < 0.75:
            prompt_parts.append("Address remaining critical gaps and key ambiguities")
        else:
            prompt_parts.append("Focus on high-value optional details for optimization")

        prompt_parts.extend(
            [
                "",
                "For each question:",
                "- Provide clear context for why the information is needed",
                "- Reference their specific use case to show understanding",
                "- Use business-friendly language, not technical jargon",
                "- Indicate the question type and priority level",
                "",
                "Determine whether questioning should continue or if we have sufficient information to proceed with architecture planning.",
            ]
        )

        return "\n".join(prompt_parts)

    async def extract_state_updates(
        self, llm_response: AdaptiveQuestioningResult, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from adaptive questioning result.
        """
        # Track questioning history
        questioning_history = current_state.get("questioning_history", [])
        questioning_round = {
            "round": len(questioning_history) + 1,
            "questions": [q.model_dump() for q in llm_response.questions],
            "coverage_at_round": llm_response.current_coverage,
            "questioning_complete": llm_response.questioning_complete,
            "rationale": llm_response.questioning_rationale,
        }
        questioning_history.append(questioning_round)

        return {
            # Store questioning results
            "adaptive_questioning": {
                "current_coverage": llm_response.current_coverage,
                "target_coverage": llm_response.target_coverage,
                "questioning_complete": llm_response.questioning_complete,
                "questions_generated": len(llm_response.questions),
                "rationale": llm_response.questioning_rationale,
                "agent_version": "1.0",
            },
            # Update questioning history
            "questioning_history": questioning_history,
            "questioning_complete": llm_response.questioning_complete,
            # Store current questions for UI/workflow
            "current_questions": [q.model_dump() for q in llm_response.questions],
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> list[str]:
        """Requires both IntakeExtractAgent and CoverageCheckAgent."""
        return [AgentType.INTAKE_EXTRACT.value, AgentType.COVERAGE_CHECK.value]

    async def build_next_agent_context(
        self, llm_response: AdaptiveQuestioningResult
    ) -> Dict[str, Any]:
        """Build context for the next stage (Planning agents or question collection)."""
        return {
            "from_agent": self.agent_type.value,
            "questioning_complete": llm_response.questioning_complete,
            "questions_count": len(llm_response.questions),
            "coverage_progress": llm_response.current_coverage,
            "ready_for_planning": llm_response.questioning_complete
            and llm_response.current_coverage >= 0.7,
            "summary": f"Generated {len(llm_response.questions)} questions, {'ready for planning' if llm_response.questioning_complete else 'awaiting user responses'}",
        }

    async def should_continue_questioning(
        self,
        state: MLOpsWorkflowState,
        max_rounds: int = 3,
        target_coverage: float = 0.75,
    ) -> bool:
        """
        Determine if questioning should continue based on state.

        Args:
            state: Current project state
            max_rounds: Maximum questioning rounds (default 3)
            target_coverage: Target coverage threshold (default 75%)

        Returns:
            True if questioning should continue, False otherwise
        """
        questioning_history = state.get("questioning_history", [])
        # Try to get coverage from analysis first, then fall back to direct coverage_score
        current_coverage = state.get("coverage_analysis", {}).get("score", 
                                     state.get("coverage_score", 0.0))
        questioning_complete = state.get("questioning_complete", False)

        # Check termination conditions
        if questioning_complete:
            return False

        if len(questioning_history) >= max_rounds:
            logger.info(f"Max questioning rounds ({max_rounds}) reached")
            return False

        if current_coverage >= target_coverage:
            logger.info(f"Target coverage ({target_coverage:.1%}) achieved")
            return False

        # Check for critical gaps
        coverage_analysis = state.get("coverage_analysis", {})
        critical_gaps = coverage_analysis.get("critical_gaps", [])

        if len(critical_gaps) == 0 and current_coverage >= 0.7:
            logger.info("No critical gaps remaining and minimum coverage achieved")
            return False

        return True


def create_adaptive_questions_agent() -> AdaptiveQuestionsAgent:
    """Factory function to create a configured AdaptiveQuestionsAgent."""
    return AdaptiveQuestionsAgent()
