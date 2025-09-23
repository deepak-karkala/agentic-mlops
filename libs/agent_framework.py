"""
MLOps Agent Framework

Core framework for implementing the multi-agent MLOps planning system.
Provides shared state management, base agent classes, and reason card models
for transparent decision making.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(Enum):
    """Types of MLOps planning agents."""

    # Early-stage LLM agents
    INTAKE_EXTRACT = "intake.extract"
    COVERAGE_CHECK = "coverage.check"
    ADAPTIVE_QUESTIONS = "adaptive.questions"

    # Core planning agents
    PLANNER = "planner"
    CRITIC_TECH = "critic.tech"
    CRITIC_COST = "critic.cost"
    POLICY_ENGINE = "policy.engine"

    # Domain-specific agents
    PROJECT_STAGES = "project.stages"
    VERSIONING_GOVERNANCE = "versioning.governance"
    DATA_SOURCING = "data.sourcing"
    PIPELINES_WORKFLOWS = "pipelines.workflows"
    TECH_STACK = "tech.stack"
    TESTING_STRATEGY = "testing.strategy"
    DATA_ENGINEERING = "data.engineering"
    FEATURE_ENGINEERING = "feature.engineering"
    MODEL_DEVELOPMENT = "model.development"
    TRAINING_PIPELINES = "training.pipelines"
    DEPLOYMENT_SERVING = "deployment.serving"
    INFERENCE_PIPELINE = "inference.pipeline"
    MONITORING_OBSERVABILITY = "monitoring.observability"
    CONTINUAL_LEARNING = "continual.learning"
    GOVERNANCE_ETHICS = "governance.ethics"
    SYSTEM_ARCHITECTURE = "system.architecture"


class TriggerType(Enum):
    """Types of triggers for agent execution."""

    CONSTRAINTS_UPDATED = "constraints_updated"
    USER_APPROVE = "user_approve"
    REGEN = "regen"
    FOLLOW_UP = "follow_up"
    INITIAL = "initial"


class PolicyStatus(Enum):
    """Policy evaluation results."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


# Consolidated MLOps Workflow State Schema
class MLOpsWorkflowState(TypedDict, total=False):
    """
    Comprehensive state schema for MLOps workflows that combines all agent framework
    state with LangGraph compatibility. This replaces both the old MLOpsProjectState
    and the previous MLOpsWorkflowState to eliminate duplication.
    """

    # Original messages for compatibility with existing API
    messages: List[Any]

    # Core workflow state
    project_id: Optional[str]
    decision_set_id: Optional[str]
    version: Optional[int]

    # User input and constraints
    constraints: Optional[Dict[str, Any]]
    coverage_score: Optional[float]
    missing_fields: Optional[List[str]]

    # Planning outputs
    plan: Optional[Dict[str, Any]]
    candidates: Optional[List[Dict[str, Any]]]
    selected_pattern_id: Optional[str]

    # Critics and policy results
    tech_critique: Optional[Dict[str, Any]]
    cost_estimate: Optional[Dict[str, Any]]
    policy_results: Optional[Dict[str, Any]]

    # Agent execution tracking
    agent_outputs: Optional[Dict[str, Any]]
    reason_cards: Optional[List[Dict[str, Any]]]

    # Artifacts and reports
    artifacts: Optional[List[Dict[str, Any]]]
    reports: Optional[Dict[str, Any]]

    # Execution metadata
    run_meta: Optional[Dict[str, Any]]
    last_updated: Optional[str]
    execution_order: Optional[List[str]]

    # LLM-specific fields for enhanced agent capabilities
    constraint_extraction: Optional[Dict[str, Any]]
    coverage_analysis: Optional[Dict[str, Any]]
    adaptive_questioning: Optional[Dict[str, Any]]
    questioning_history: Optional[List[Dict[str, Any]]]
    questioning_complete: Optional[bool]
    current_questions: Optional[List[Dict[str, Any]]]
    planning_analysis: Optional[Dict[str, Any]]
    technical_feasibility_score: Optional[float]
    architecture_confidence: Optional[float]
    estimated_monthly_cost: Optional[float]
    cost_confidence: Optional[float]
    budget_compliance_status: Optional[str]
    overall_compliance_status: Optional[str]
    compliance_score: Optional[float]
    escalation_required: Optional[bool]
    policy_validation: Optional[Dict[str, Any]]

    # Legacy fields for backward compatibility
    coverage: Optional[Dict[str, Any]]
    cost: Optional[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    hitl: Optional[Dict[str, Any]]
    rationale: Optional[Dict[str, Any]]
    diff_summary: Optional[Dict[str, Any]]


# MLOpsProjectState removed - all code now uses MLOpsWorkflowState directly


# Pydantic Models for Reason Cards and Transparency


class CandidateOption(BaseModel):
    """A candidate option considered by an agent."""

    id: str
    summary: str
    tradeoffs: List[str]
    estimated_cost: Optional[float] = None
    confidence: Optional[float] = None


class DecisionChoice(BaseModel):
    """The choice made by an agent."""

    id: str
    justification: str
    confidence: float = Field(ge=0.0, le=1.0)


class PolicyResult(BaseModel):
    """Result of policy evaluation."""

    rule_id: str
    status: PolicyStatus
    detail: str


class ImpactAssessment(BaseModel):
    """Assessment of decision impacts."""

    monthly_usd: Optional[float] = None
    p95_latency_ms: Optional[int] = None
    availability_impact: Optional[str] = None
    security_impact: Optional[str] = None
    scalability_impact: Optional[str] = None


class ReasonCard(BaseModel):
    """
    Structured reason card for transparent agent decision making.
    This is what gets streamed to users for full transparency.
    """

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentType
    node_name: str
    trigger: TriggerType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Input context
    inputs: Dict[str, Any] = Field(default_factory=dict)
    constraints_keys: List[str] = Field(default_factory=list)
    artifacts_consulted: List[str] = Field(default_factory=list)

    # Decision process
    candidates: List[CandidateOption] = Field(default_factory=list)
    choice: Optional[DecisionChoice] = None

    # Policy and impact assessment
    policy_results: Dict[str, PolicyStatus] = Field(default_factory=dict)
    impacts: Optional[ImpactAssessment] = None

    # Confidence and risk assessment
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    # Links and references
    links: Dict[str, str] = Field(default_factory=dict)

    # Agent-specific outputs
    outputs: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class AgentOutput(BaseModel):
    """Standard output format for all agents."""

    success: bool
    reason_card: ReasonCard
    state_updates: Dict[str, Any] = Field(default_factory=dict)
    next_agent_context: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


# Base Agent Framework


class BaseMLOpsAgent(ABC):
    """
    Base class for all MLOps planning agents.

    Provides common functionality for state management, reason card generation,
    and integration with the LangGraph workflow.
    """

    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        system_prompt_path: Optional[str] = None,
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.system_prompt_path = system_prompt_path
        self._system_prompt: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        """Load system prompt from file if not already loaded."""
        if self._system_prompt is None and self.system_prompt_path:
            try:
                with open(self.system_prompt_path, "r") as f:
                    self._system_prompt = f.read()
            except FileNotFoundError:
                self._system_prompt = (
                    f"You are a {self.name} agent for MLOps system design."
                )
        return (
            self._system_prompt
            or f"You are a {self.name} agent for MLOps system design."
        )

    @abstractmethod
    async def execute(
        self, state: MLOpsWorkflowState, trigger: TriggerType = TriggerType.INITIAL
    ) -> AgentOutput:
        """
        Execute the agent's logic.

        Args:
            state: Current shared state of the MLOps workflow
            trigger: What triggered this agent execution

        Returns:
            AgentOutput with reason card and state updates
        """
        pass

    def create_reason_card(
        self,
        trigger: TriggerType,
        inputs: Dict[str, Any],
        candidates: List[CandidateOption] = None,
        choice: DecisionChoice = None,
        confidence: float = 0.5,
    ) -> ReasonCard:
        """Create a structured reason card for this agent's decision."""
        # Prefer canonical LangGraph node identifiers ("intake_extract", "critic_tech", ...)
        node_identifier = self.agent_type.value.replace(".", "_")
        if not node_identifier:
            node_identifier = self.name.lower().replace(" ", "_")

        return ReasonCard(
            agent=self.agent_type,
            node_name=node_identifier,
            trigger=trigger,
            inputs=inputs,
            candidates=candidates or [],
            choice=choice,
            confidence=confidence,
        )

    def extract_constraints_keys(self, state: MLOpsWorkflowState) -> List[str]:
        """Extract relevant constraint keys for this agent."""
        constraints = state.get("constraints", {})
        return list(constraints.keys())

    def log_execution(self, state: MLOpsWorkflowState, reason_card: ReasonCard):
        """Log this agent's execution in the state."""
        if "reason_cards" not in state:
            state["reason_cards"] = []
        if "execution_order" not in state:
            state["execution_order"] = []

        state["reason_cards"].append(reason_card.model_dump())
        state["execution_order"].append(self.agent_type.value)
        state["last_updated"] = datetime.now(timezone.utc).isoformat()


@dataclass
class AgentContext:
    """Context passed between agents for coordination."""

    previous_outputs: Dict[AgentType, AgentOutput] = field(default_factory=dict)
    execution_history: List[str] = field(default_factory=list)
    shared_artifacts: Dict[str, Any] = field(default_factory=dict)
    user_feedback: Optional[str] = None


class AgentRegistry:
    """Registry for managing available MLOps agents."""

    def __init__(self):
        self._agents: Dict[AgentType, BaseMLOpsAgent] = {}
        self._execution_order: List[AgentType] = []

    def register_agent(self, agent: BaseMLOpsAgent, position: Optional[int] = None):
        """Register an agent in the system."""
        self._agents[agent.agent_type] = agent
        if position is not None:
            self._execution_order.insert(position, agent.agent_type)
        else:
            self._execution_order.append(agent.agent_type)

    def get_agent(self, agent_type: AgentType) -> Optional[BaseMLOpsAgent]:
        """Get an agent by type."""
        return self._agents.get(agent_type)

    def get_execution_order(self) -> List[AgentType]:
        """Get the defined execution order for agents."""
        return self._execution_order.copy()

    def list_agents(self) -> Dict[AgentType, str]:
        """List all registered agents."""
        return {agent_type: agent.name for agent_type, agent in self._agents.items()}


# Global registry instance
agent_registry = AgentRegistry()
