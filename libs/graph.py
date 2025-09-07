from __future__ import annotations

from typing import Literal, TypedDict, Optional, List, Dict, Any

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.pregel import Pregel
from langchain_core.messages import AIMessage, HumanMessage

from libs.database import create_appropriate_checkpointer


class ChatMessage(TypedDict):
    """Simplified message format for API serialization."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str


class MLOpsProjectState(TypedDict):
    """
    Full state schema for the MLOps planning and generation workflow.
    Based on the requirements in implementation_details.md section 21.2.
    """

    # Original messages for compatibility with existing API
    messages: List[Any]

    # Core workflow state
    constraints: Optional[Dict[str, Any]]
    coverage: Optional[Dict[str, Any]]
    plan: Optional[Dict[str, Any]]
    candidates: Optional[List[Dict[str, Any]]]
    tech_critique: Optional[Dict[str, Any]]  # From critic_tech
    cost: Optional[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    hitl: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, Any]]
    reports: Optional[Dict[str, Any]]
    rationale: Optional[Dict[str, Any]]  # From rationale_compile
    diff_summary: Optional[Dict[str, Any]]
    run_meta: Optional[Dict[str, Any]]


# Agent node functions (initially as stubs)


def intake_extract(state: MLOpsProjectState) -> MLOpsProjectState:
    """Parse freeform input into Constraint Schema."""
    messages = state.get("messages", [])

    # Extract user prompt from messages
    user_prompt = "Default user prompt"
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_prompt = msg.content
            break

    # Mock constraint extraction
    constraints = {
        "extracted_from": user_prompt,
        "cloud": "aws",
        "region": "us-east-1",
        "budget_band": "startup",
        "data_classification": "internal",
    }

    return {"constraints": constraints}


def coverage_check(state: MLOpsProjectState) -> MLOpsProjectState:
    """Compute coverage score and emit missing/ambiguous fields."""
    _constraints = state.get("constraints", {})

    # Mock coverage analysis
    coverage = {
        "score": 0.75,
        "missing_fields": ["sla_latency_ms", "throughput"],
        "ambiguous_fields": [],
        "complete": True,  # For now, assume complete
    }

    return {"coverage": coverage}


def adaptive_questions(state: MLOpsProjectState) -> MLOpsProjectState:
    """Generate follow-up questions if coverage is insufficient."""
    _coverage = state.get("coverage", {})

    # For now, just pass through - no additional questions
    return {}


def planner(state: MLOpsProjectState) -> MLOpsProjectState:
    """Compose capability patterns into a candidate plan."""
    _constraints = state.get("constraints", {})

    # Mock MLOps plan
    plan = {
        "architecture_type": "serverless_ml",
        "services": {
            "data_ingestion": "s3_batch",
            "feature_engineering": "sagemaker_processing",
            "training": "sagemaker_training",
            "model_registry": "sagemaker_model_registry",
            "inference": "sagemaker_serverless",
        },
        "estimated_monthly_cost": 420.0,
    }

    candidates = [
        {"id": "serverless_option", "summary": "Serverless ML stack", "plan": plan}
    ]

    return {"plan": plan, "candidates": candidates}


def critic_tech(state: MLOpsProjectState) -> MLOpsProjectState:
    """Analyze feasibility, coupling, bottlenecks; emit risks."""
    _plan = state.get("plan", {})

    # Mock technical criticism
    tech_critique = {
        "feasibility_score": 0.85,
        "risks": ["cold start latency for serverless inference"],
        "bottlenecks": ["feature engineering step"],
        "recommendations": ["consider feature store for low latency"],
    }

    return {"tech_critique": tech_critique}


def critic_cost(state: MLOpsProjectState) -> MLOpsProjectState:
    """Generate coarse BOM and monthly estimate; compute deltas vs previous."""
    plan = state.get("plan", {})

    # Mock cost analysis
    cost = {
        "monthly_usd": plan.get("estimated_monthly_cost", 420.0),
        "breakdown": [
            {"service": "sagemaker_training", "monthly_usd": 200.0},
            {"service": "sagemaker_inference", "monthly_usd": 150.0},
            {"service": "s3_storage", "monthly_usd": 70.0},
        ],
        "confidence": 0.7,
    }

    return {"cost": cost}


def policy_eval(state: MLOpsProjectState) -> MLOpsProjectState:
    """Apply rules; pass/warn/fail with explanations."""
    _constraints = state.get("constraints", {})
    _cost = state.get("cost", {})

    # Mock policy evaluation
    policy = {
        "overall_status": "pass",
        "rules": [
            {"id": "budget_check", "status": "pass", "detail": "Within startup budget"},
            {"id": "region_check", "status": "pass", "detail": "Using approved region"},
            {
                "id": "data_classification",
                "status": "pass",
                "detail": "Internal data handling OK",
            },
        ],
    }

    return {"policy": policy}


def gate_hitl(state: MLOpsProjectState) -> MLOpsProjectState:
    """Human-in-the-loop approval gate (interrupt point)."""
    # This will be an interrupt point in the actual implementation
    # For now, just pass through
    hitl = {
        "status": "approved",
        "comment": "Auto-approved for testing",
        "timestamp": "2025-01-01T00:00:00Z",
    }

    return {"hitl": hitl}


def codegen(state: MLOpsProjectState) -> MLOpsProjectState:
    """Generate repo skeletons (services, IaC, CI, docs)."""
    _plan = state.get("plan", {})

    # Mock code generation
    artifacts = {
        "repo_structure": {
            "terraform/": "Infrastructure as code",
            "src/": "Application code",
            "ci/": "CI/CD pipelines",
            "docs/": "Documentation",
        },
        "file_count": 25,
        "generated_timestamp": "2025-01-01T00:00:00Z",
    }

    return {"artifacts": artifacts}


def validators(state: MLOpsProjectState) -> MLOpsProjectState:
    """Run static checks; compile /reports."""
    _artifacts = state.get("artifacts", {})

    # Mock validation results
    reports = {
        "terraform_validate": {"status": "pass", "issues": []},
        "ruff_check": {"status": "pass", "issues": []},
        "security_scan": {"status": "pass", "secrets_found": 0},
        "overall_status": "pass",
    }

    return {"reports": reports}


def rationale_compile(state: MLOpsProjectState) -> MLOpsProjectState:
    """Transform per-node rationale into Reason Cards and Design Rationale doc."""
    # Mock rationale compilation
    rationale = {
        "reason_cards": [
            {
                "node": "planner",
                "decision": "chose serverless architecture",
                "rationale": "cost effective for startup",
            },
            {
                "node": "critic_cost",
                "decision": "approved cost estimate",
                "rationale": "within budget constraints",
            },
        ],
        "design_doc": "Generated design rationale document",
    }

    return {"rationale": rationale}


def diff_and_persist(state: MLOpsProjectState) -> MLOpsProjectState:
    """Commit artifacts to git/S3; write decision_set + events; output composite Change Summary."""
    # Mock diff and persistence
    diff_summary = {
        "files_added": 25,
        "files_modified": 0,
        "files_removed": 0,
        "cost_delta_usd": 420.0,
        "git_commit": "abc123",
        "s3_artifact_key": "projects/test/artifacts/abc123.zip",
    }

    return {"diff_summary": diff_summary}


# Legacy function for backward compatibility
def call_llm(state: MessagesState) -> MessagesState:
    """
    Thin-slice node: returns a deterministic assistant reply without
    calling external providers (offline-friendly for CI).

    Args:
        state: The current graph state containing messages

    Returns:
        Updated state with new assistant message
    """
    messages = state.get("messages", [])

    # Find the last user message content to echo back
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if last_user_msg:
        reply = f"You said: {last_user_msg}. Thin slice online."
    else:
        reply = "Thin slice online."

    return {"messages": [AIMessage(content=reply)]}


def build_full_graph() -> Pregel:
    """
    Build and compile the full MLOps workflow graph with all agent nodes.

    This creates the complete deterministic sequential graph as specified in
    implementation_details.md section 21.1. All nodes are initially stubs
    that return mock data for testing the graph topology.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MLOpsProjectState)

    # Add all agent nodes in the order specified in section 21.1
    graph.add_node("intake_extract", intake_extract)
    graph.add_node("coverage_check", coverage_check)
    graph.add_node("adaptive_questions", adaptive_questions)
    graph.add_node("planner", planner)
    graph.add_node("critic_tech", critic_tech)
    graph.add_node("critic_cost", critic_cost)
    graph.add_node("policy_eval", policy_eval)
    graph.add_node("gate_hitl", gate_hitl)
    graph.add_node("codegen", codegen)
    graph.add_node("validators", validators)
    graph.add_node("rationale_compile", rationale_compile)
    graph.add_node("diff_and_persist", diff_and_persist)

    # Define the sequential execution flow with normal edges
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "coverage_check")
    graph.add_edge("coverage_check", "adaptive_questions")
    graph.add_edge("adaptive_questions", "planner")
    graph.add_edge("planner", "critic_tech")
    graph.add_edge("critic_tech", "critic_cost")
    graph.add_edge("critic_cost", "policy_eval")
    graph.add_edge("policy_eval", "gate_hitl")
    graph.add_edge("gate_hitl", "codegen")
    graph.add_edge("codegen", "validators")
    graph.add_edge("validators", "rationale_compile")
    graph.add_edge("rationale_compile", "diff_and_persist")
    graph.add_edge("diff_and_persist", END)

    # Create appropriate checkpointer based on environment
    checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()


def build_thin_graph() -> Pregel:
    """
    Build and compile the minimal deterministic LangGraph graph with checkpointing.

    This creates a simple linear graph with a single node that processes
    user messages and returns deterministic responses. It includes PostgreSQL
    checkpointing for durable state when available.

    This function is kept for backward compatibility with existing tests and API.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MessagesState)

    # Add the single processing node
    graph.add_node("call_llm", call_llm)

    # Define the execution flow: START -> call_llm -> END
    graph.add_edge(START, "call_llm")
    graph.add_edge("call_llm", END)

    # Create appropriate checkpointer based on environment
    checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()
