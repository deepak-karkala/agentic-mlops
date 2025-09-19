"""HITL Test Graph - Focused graph to test Human-in-the-Loop functionality."""

from langgraph.graph import START, END, StateGraph
from langgraph.pregel import Pregel

from libs.agent_framework import MLOpsWorkflowState
from libs.database import create_async_checkpointer, create_appropriate_checkpointer
from libs.graph import gate_hitl, codegen, _safe_async_run


def build_hitl_test_graph() -> Pregel:
    """Build a focused graph to test Human-in-the-Loop functionality."""

    graph = StateGraph(MLOpsWorkflowState)

    def quick_setup(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
        """Setup minimal state to reach HITL gate quickly."""
        # Simulate completed agents with minimal plan and constraints
        plan = {
            "pattern_name": "HITL Test Pattern",
            "architecture_type": "app_runner",
            "key_services": {
                "api": "Test FastAPI service",
            },
            "implementation_phases": ["scaffold"],
            "estimated_monthly_cost": 100,
        }

        constraints = {
            "project_description": "Test project for HITL functionality",
            "budget_band": "startup",
            "deployment_preference": "serverless",
        }

        # Mock technical and cost analysis
        tech_critique = {
            "overall_feasibility_score": 0.85,
            "technical_risks": ["Minor risk 1"],
            "recommendations": ["Test recommendation"],
        }

        cost_estimate = {
            "estimated_monthly_cost": 100,
            "monthly_usd": 100,
            "primary_cost_drivers": ["App Runner", "RDS"],
            "budget_compliance_status": "within_budget",
        }

        policy_validation = {
            "overall_compliance_status": "compliant",
            "critical_violations": [],
            "warnings": [],
        }

        return {
            "constraints": constraints,
            "plan": plan,
            "tech_critique": tech_critique,
            "cost_estimate": cost_estimate,
            "policy_validation": policy_validation,
            "reason_cards": [],
            "execution_order": ["quick_setup"],
        }

    # Add nodes for quick path to HITL
    graph.add_node("quick_setup", quick_setup)
    graph.add_node("gate_hitl", gate_hitl)
    graph.add_node("codegen", codegen)

    # Define flow: setup -> HITL gate -> codegen
    graph.add_edge(START, "quick_setup")
    graph.add_edge("quick_setup", "gate_hitl")
    graph.add_edge("gate_hitl", "codegen")
    graph.add_edge("codegen", END)

    # Prefer async-compatible checkpointer when available
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()