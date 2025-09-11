"""
Base LLM Agent Class

Enhanced base class for LLM-powered agents with context accumulation,
structured outputs, and robust error handling.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from abc import abstractmethod

from .agent_framework import (
    BaseMLOpsAgent,
    AgentOutput,
    AgentType,
    TriggerType,
    MLOpsWorkflowState,
    ReasonCard,
)
from .llm_client import OpenAIClient, get_llm_client, LLMClientError
from .constraint_schema import MLOpsConstraints
from pydantic import BaseModel

# Type variable for structured outputs
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class MLOpsExecutionContext:
    """
    Rich context object that accumulates information across agent executions.

    Provides structured access to project state, previous decisions, and
    execution history for LLM agents.
    """

    def __init__(self, state: MLOpsWorkflowState):
        self.state = state
        self.user_input = self._extract_user_input()
        self.constraints = self._get_constraints()
        self.execution_history = state.get("execution_order", [])
        self.reason_cards = state.get("reason_cards", [])

    def _extract_user_input(self) -> str:
        """Extract original user input from messages."""
        messages = self.state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                return msg.content
            elif isinstance(msg, dict) and "content" in msg:
                return msg["content"]
        return "No user input found"

    def _get_constraints(self) -> Optional[MLOpsConstraints]:
        """Get structured constraints if available."""
        constraints_dict = self.state.get("constraints", {})
        if not constraints_dict:
            return None

        try:
            return MLOpsConstraints.model_validate(constraints_dict)
        except Exception:
            return None

    def get_previous_agent_outputs(self) -> Dict[str, Any]:
        """Get outputs from all previously executed agents."""
        return self.state.get("agent_outputs", {})

    def get_previous_decisions(self) -> List[Dict[str, Any]]:
        """Get decision history from reason cards."""
        decisions = []
        for card in self.reason_cards:
            if card.get("choice"):
                decisions.append(
                    {
                        "agent": card.get("agent", "unknown"),
                        "decision_id": card.get("decision_id"),
                        "choice": card.get("choice"),
                        "confidence": card.get("confidence", 0.0),
                        "rationale": card.get("choice", {}).get("justification", ""),
                        "outputs": card.get("outputs", {}),
                        "timestamp": card.get("timestamp"),
                    }
                )
        return decisions

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """Get current plan if available."""
        return self.state.get("plan")

    def get_technical_analysis(self) -> Optional[Dict[str, Any]]:
        """Get technical analysis if available."""
        return self.state.get("tech_critique")

    def get_cost_analysis(self) -> Optional[Dict[str, Any]]:
        """Get cost analysis if available."""
        return self.state.get("cost_estimate")

    def build_context_summary(self) -> str:
        """Build comprehensive context summary for LLM consumption."""
        parts = []

        # Original user request
        parts.append(f"Original User Request:\n{self.user_input}")

        # Constraints if extracted
        if self.constraints:
            parts.append(
                f"\nExtracted Constraints:\n{self.constraints.to_context_string()}"
            )

        # Previous decisions
        decisions = self.get_previous_decisions()
        if decisions:
            parts.append("\nPrevious Agent Decisions:")
            for decision in decisions:
                parts.append(
                    f"- {decision['agent']}: {decision['rationale']} "
                    f"(confidence: {decision['confidence']:.2f})"
                )

        # Current plan details
        plan = self.get_current_plan()
        if plan:
            parts.append(f"\nSelected Plan: {plan.get('pattern_name', 'Unknown')}")
            parts.append(f"Architecture: {plan.get('architecture_type', 'Unknown')}")
            parts.append(
                f"Estimated Cost: ${plan.get('estimated_monthly_cost', 0)}/month"
            )

        # Technical analysis
        tech_analysis = self.get_technical_analysis()
        if tech_analysis:
            parts.append("\nTechnical Analysis:")
            parts.append(
                f"- Feasibility Score: {tech_analysis.get('overall_feasibility_score', 'N/A')}"
            )
            if tech_analysis.get("technical_risks"):
                parts.append(f"- Key Risks: {', '.join(tech_analysis['technical_risks'][:3])}")

        # Cost analysis
        cost_analysis = self.get_cost_analysis()
        if cost_analysis:
            parts.append("\nCost Analysis:")
            parts.append(f"- Monthly Cost: ${cost_analysis.get('monthly_usd', 0)}")
            if cost_analysis.get("cost_drivers"):
                parts.append(
                    f"- Top Cost Drivers: {', '.join(cost_analysis['cost_drivers'][:3])}"
                )

        return "\n".join(parts)

    def get_agent_specific_context(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get context relevant to a specific agent type."""
        base_context = {
            "user_input": self.user_input,
            "constraints": self.constraints.model_dump() if self.constraints else {},
            "previous_outputs": self.get_previous_agent_outputs(),
            "execution_history": self.execution_history,
        }

        # Add agent-specific context
        if agent_type == AgentType.CRITIC_TECH:
            base_context["plan"] = self.get_current_plan()
        elif agent_type == AgentType.CRITIC_COST:
            base_context["plan"] = self.get_current_plan()
            base_context["tech_analysis"] = self.get_technical_analysis()
        elif agent_type == AgentType.POLICY_ENGINE:
            base_context["plan"] = self.get_current_plan()
            base_context["tech_analysis"] = self.get_technical_analysis()
            base_context["cost_analysis"] = self.get_cost_analysis()

        return base_context


class BaseLLMAgent(BaseMLOpsAgent):
    """
    Enhanced base class for LLM-powered MLOps agents.

    Provides:
    - LLM integration with structured outputs
    - Context accumulation from previous agents
    - Robust error handling and retry logic
    - Token usage tracking
    - Prompt template management
    """

    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        system_prompt: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM-powered agent.

        Args:
            agent_type: Type of agent
            name: Human-readable name
            description: Agent description
            system_prompt: System prompt for the LLM
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        super().__init__(agent_type, name, description)

        self._system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # LLM client (lazy initialization)
        self._llm_client: Optional[OpenAIClient] = None

    @property
    def system_prompt(self) -> str:
        """Get system prompt for this LLM agent."""
        return self._system_prompt

    @property
    def llm_client(self) -> OpenAIClient:
        """Get LLM client (lazy initialization)."""
        if self._llm_client is None:
            self._llm_client = get_llm_client(default_model=self.model)
        return self._llm_client

    @abstractmethod
    async def get_structured_output_type(self) -> Type[T]:
        """
        Get the Pydantic model type for structured output.

        Must be implemented by each agent to define their output schema.
        """
        pass

    @abstractmethod
    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build user prompt from execution context.

        Must be implemented by each agent to construct their specific prompt.
        """
        pass

    async def execute(
        self, state: MLOpsWorkflowState, trigger: TriggerType = TriggerType.INITIAL
    ) -> AgentOutput:
        """
        Execute the LLM-powered agent.

        This method orchestrates the complete agent execution:
        1. Build execution context from state
        2. Construct LLM prompt
        3. Make structured LLM call
        4. Create reason card
        5. Update state
        """
        try:
            # Build rich context from current state
            context = MLOpsExecutionContext(state)
            start = time.time()
            thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
            logger.info(
                f"Agent start: {self.name}",
                extra={
                    "agent": self.agent_type.value,
                    "model": self.model,
                    "thread_id": thread_id,
                },
            )

            # Build messages for LLM
            user_prompt = self.build_user_prompt(context)
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Get structured output type
            output_type = await self.get_structured_output_type()

            # Make LLM call with structured output
            llm_response = await self.llm_client.complete(
                messages=messages,
                response_format=output_type,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Process LLM response into agent output
            out = await self.process_llm_response(llm_response, context, trigger, state)
            logger.info(
                f"Agent success: {self.name}",
                extra={
                    "agent": self.agent_type.value,
                    "duration_ms": int((time.time() - start) * 1000),
                    "thread_id": thread_id,
                },
            )
            return out

        except LLMClientError as e:
            logger.error(f"{self.name} LLM error: {str(e)}")
            return self._create_error_output(
                trigger, f"LLM service error: {str(e)}", state
            )
        except Exception as e:
            logger.error(f"{self.name} execution error: {str(e)}")
            return self._create_error_output(
                trigger, f"Agent execution failed: {str(e)}", state
            )

    async def process_llm_response(
        self,
        llm_response: BaseModel,
        context: MLOpsExecutionContext,
        trigger: TriggerType,
        state: MLOpsWorkflowState,
    ) -> AgentOutput:
        """
        Process structured LLM response into agent output.

        Can be overridden by specific agents for custom processing.
        """
        # Create reason card from LLM response
        reason_card = await self.create_reason_card_from_llm(
            llm_response, context, trigger
        )

        # Extract state updates from LLM response
        state_updates = await self.extract_state_updates(llm_response, state)

        # Log execution
        self.log_execution(state, reason_card)

        return AgentOutput(
            success=True,
            reason_card=reason_card,
            state_updates=state_updates,
            next_agent_context=await self.build_next_agent_context(llm_response),
        )

    async def create_reason_card_from_llm(
        self,
        llm_response: BaseModel,
        context: MLOpsExecutionContext,
        trigger: TriggerType,
    ) -> ReasonCard:
        """Create reason card from LLM structured output."""
        # Build inputs for reason card
        inputs = {
            "user_input_summary": context.user_input[:200] + "..."
            if len(context.user_input) > 200
            else context.user_input,
            "context_agents": context.execution_history,
            "model_used": self.model,
        }

        # Extract confidence from LLM response if available
        confidence = getattr(llm_response, "confidence", None)
        if confidence is None:
            confidence = getattr(llm_response, "extraction_confidence", None)
        if confidence is None:
            confidence = 0.7  # Default confidence

        # Create base reason card
        reason_card = self.create_reason_card(
            trigger=trigger, inputs=inputs, confidence=confidence
        )

        # Add LLM-specific outputs
        reason_card.outputs = llm_response.model_dump()

        # Extract risks and assumptions if present
        if hasattr(llm_response, "risks"):
            reason_card.risks = getattr(llm_response, "risks", [])
        if hasattr(llm_response, "assumptions"):
            reason_card.assumptions = getattr(llm_response, "assumptions", [])

        return reason_card

    async def extract_state_updates(
        self, llm_response: BaseModel, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from LLM response.

        Override in specific agents to define state update logic.
        """
        return {
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            }
        }

    async def build_next_agent_context(self, llm_response: BaseModel) -> Dict[str, Any]:
        """Build context for next agent in the chain."""
        return {
            "from_agent": self.agent_type.value,
            "summary": getattr(llm_response, "summary", str(llm_response)[:200]),
        }

    def _create_error_output(
        self, trigger: TriggerType, error_message: str, state: MLOpsWorkflowState
    ) -> AgentOutput:
        """Create error output for failed execution."""
        error_reason_card = self.create_reason_card(
            trigger=trigger, inputs={"error": error_message}, confidence=0.0
        )

        error_reason_card.risks = [f"Agent execution failed: {error_message}"]

        return AgentOutput(
            success=False, reason_card=error_reason_card, error_message=error_message
        )

    async def validate_prerequisites(self, context: MLOpsExecutionContext) -> List[str]:
        """
        Validate that prerequisites for this agent are met.

        Returns:
            List of error messages, empty if all prerequisites are satisfied
        """
        errors = []

        # Check if required previous agents have executed
        required_agents = self.get_required_predecessor_agents()
        for required_agent in required_agents:
            if required_agent not in context.execution_history:
                errors.append(
                    f"Required predecessor agent not executed: {required_agent}"
                )

        return errors

    def get_required_predecessor_agents(self) -> List[str]:
        """
        Get list of required predecessor agents.

        Override in specific agents to define dependencies.
        """
        return []

    async def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary for this agent."""
        if self._llm_client:
            return self._llm_client.get_usage_summary()
        return {"total_tokens": 0, "total_cost_usd": 0.0, "request_count": 0}
