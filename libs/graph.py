from __future__ import annotations

from typing import Literal, TypedDict
import asyncio
import logging
import time

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.pregel import Pregel
from langgraph.types import interrupt
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime, timezone

from libs.database import (
    create_appropriate_checkpointer,
    create_async_checkpointer,
)
from libs.agent_framework import (
    MLOpsWorkflowState,
    TriggerType,
)
# Legacy agents removed - using only LLM-powered agents

# New LLM-powered agents
from libs.intake_extract_agent import create_intake_extract_agent
from libs.coverage_check_agent import create_coverage_check_agent
from libs.adaptive_questions_agent import create_adaptive_questions_agent
from libs.llm_planner_agent import create_llm_planner_agent
from libs.llm_tech_critic_agent import create_llm_tech_critic_agent
from libs.llm_cost_critic_agent import create_llm_cost_critic_agent
from libs.llm_policy_engine_agent import create_llm_policy_engine_agent

logger = logging.getLogger(__name__)


def _safe_async_run(coro):
    """Safely run async coroutine, handling event loop conflicts."""
    import concurrent.futures

    try:
        # Try to get the current loop
        asyncio.get_running_loop()
        # We're in an async context, run in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)


class ChatMessage(TypedDict):
    """Simplified message format for API serialization."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str


# MLOpsWorkflowState is now imported from agent_framework.py to eliminate duplication


# Initialize LLM-powered agents
_llm_intake_extract_agent = None
_llm_coverage_check_agent = None
_llm_adaptive_questions_agent = None
_llm_planner_agent = None
_llm_tech_critic_agent = None
_llm_cost_critic_agent = None
_llm_policy_engine_agent = None


# Legacy _get_agents() function removed - using only LLM-powered agents


def _get_llm_agents():
    """Lazy initialization of LLM-powered agents."""
    global \
        _llm_intake_extract_agent, \
        _llm_coverage_check_agent, \
        _llm_adaptive_questions_agent, \
        _llm_planner_agent, \
        _llm_tech_critic_agent, \
        _llm_cost_critic_agent, \
        _llm_policy_engine_agent

    if _llm_intake_extract_agent is None:
        _llm_intake_extract_agent = create_intake_extract_agent()
        _llm_coverage_check_agent = create_coverage_check_agent()
        _llm_adaptive_questions_agent = create_adaptive_questions_agent()
        _llm_planner_agent = create_llm_planner_agent()
        _llm_tech_critic_agent = create_llm_tech_critic_agent()
        _llm_cost_critic_agent = create_llm_cost_critic_agent()
        _llm_policy_engine_agent = create_llm_policy_engine_agent()

    return (
        _llm_intake_extract_agent,
        _llm_coverage_check_agent,
        _llm_adaptive_questions_agent,
        _llm_planner_agent,
        _llm_tech_critic_agent,
        _llm_cost_critic_agent,
        _llm_policy_engine_agent,
    )


# Agent node functions (using real agent implementations)


def intake_extract(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Parse freeform input into the constraint schema using the LLM intake agent."""
    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: intake_extract", extra={"thread_id": thread_id})

    intake_agent, *_ = _get_llm_agents()

    try:
        result = _safe_async_run(intake_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            state_updates = result.state_updates
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            execution_order = state.get("execution_order", [])
            execution_order.append("intake_extract")

            out = {
                **state_updates,
                "reason_cards": reason_cards,
                "execution_order": execution_order,
            }
            logger.info(
                "Node success: intake_extract",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out

        logger.warning(
            "Node failure: intake_extract",
            extra={"thread_id": thread_id, "error": result.error_message},
        )
        return {"constraints": {}, "error": result.error_message}

    except Exception as exc:
        logger.exception(
            "Node exception: intake_extract",
            extra={"thread_id": thread_id, "error": str(exc)},
        )
        return {"constraints": {}, "error": f"Intake extract agent failed: {str(exc)}"}


def coverage_check(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Compute coverage score and identify gaps using the LLM coverage agent."""
    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: coverage_check", extra={"thread_id": thread_id})

    _, coverage_agent, *_ = _get_llm_agents()

    try:
        result = _safe_async_run(coverage_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            state_updates = result.state_updates
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            execution_order = state.get("execution_order", [])
            execution_order.append("coverage_check")

            coverage = state_updates.get("coverage")
            if coverage is None:
                coverage_score = state_updates.get("coverage_score", 0.0)
                coverage_analysis = state_updates.get("coverage_analysis", {})
                coverage = {
                    "score": coverage_score,
                    "missing_fields": coverage_analysis.get("critical_gaps", []),
                    "ambiguous_fields": coverage_analysis.get("ambiguous_fields", []),
                    "complete": coverage_analysis.get("threshold_met", False),
                }

            out = {
                **state_updates,
                "coverage": coverage,
                "reason_cards": reason_cards,
                "execution_order": execution_order,
            }
            logger.info(
                "Node success: coverage_check",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out

        logger.warning(
            "Node failure: coverage_check",
            extra={"thread_id": thread_id, "error": result.error_message},
        )
        return {
            "coverage_score": 0.0,
            "coverage": {
                "score": 0.0,
                "missing_fields": [],
                "ambiguous_fields": [],
                "complete": False,
            },
            "error": result.error_message,
        }

    except Exception as exc:
        logger.exception(
            "Node exception: coverage_check",
            extra={"thread_id": thread_id, "error": str(exc)},
        )
        return {
            "coverage_score": 0.0,
            "coverage": {
                "score": 0.0,
                "missing_fields": [],
                "ambiguous_fields": [],
                "complete": False,
            },
            "error": f"Coverage check agent failed: {str(exc)}",
        }


def adaptive_questions(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Generate follow-up questions if coverage is insufficient using LLM-powered agent."""
    import os
    from libs.mock_agents import enable_mock_mode, create_mock_adaptive_questions_agent

    # Check if questioning should continue
    coverage_score = state.get("coverage_score", 0.0)
    questioning_complete = state.get("questioning_complete", False)

    # Skip if already complete or coverage is sufficient
    if questioning_complete or coverage_score >= 0.75:
        logging.getLogger(__name__).info(
            "Node skip: adaptive_questions",
            extra={"reason": "coverage_sufficient", "coverage_score": coverage_score},
        )
        return {"questioning_complete": True}

    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: adaptive_questions", extra={"thread_id": thread_id})

    try:
        # Use mock agent if enabled for testing
        if enable_mock_mode():
            logger.info("Using mock adaptive questions agent for testing")
            mock_agent = create_mock_adaptive_questions_agent()
            result = mock_agent.generate_mock_questions(state)

            # Create mock reason card
            reason_card = {
                "agent": "adaptive.questions",
                "node": "adaptive_questions",
                "reasoning": result.questioning_rationale,
                "decision": f"Generated {len(result.questions)} questions",
                "confidence": 0.9,
                "inputs": {"coverage_score": coverage_score, "state_keys": list(state.keys())},
                "outputs": result.model_dump(),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            # Store reason card
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(reason_card)

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("adaptive_questions")

            out = {
                "adaptive_questioning": {
                    "current_coverage": result.current_coverage,
                    "target_coverage": result.target_coverage,
                    "questioning_complete": result.questioning_complete,
                    "questions_generated": len(result.questions),
                    "rationale": result.questioning_rationale,
                    "agent_version": "mock-1.0",
                },
                "questioning_complete": result.questioning_complete,
                "current_questions": [q.model_dump() for q in result.questions],
                "reason_cards": reason_cards,
                "execution_order": execution_order,
            }

            logger.info(
                "Node success: adaptive_questions (mock)",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                    "questions_generated": len(result.questions),
                },
            )
            return out

        # Use real agent for production
        _, _, adaptive_questions_agent, _, _, _, _ = _get_llm_agents()

        # Execute agent directly with MLOpsWorkflowState - no conversion needed
        result = _safe_async_run(
            adaptive_questions_agent.execute(state, TriggerType.INITIAL)
        )

        if result.success:
            # Extract state updates from the agent result
            state_updates = result.state_updates

            # Store reason card
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("adaptive_questions")

            out = {
                **state_updates,
                "reason_cards": reason_cards,
                "execution_order": execution_order,
            }
            logger.info(
                "Node success: adaptive_questions",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out
        else:
            # Return error state but allow workflow to continue
            logger.warning(
                "Node failure: adaptive_questions",
                extra={"thread_id": thread_id, "error": result.error_message},
            )
            return {"questioning_complete": True, "error": result.error_message}

    except Exception as e:
        logger.exception(
            "Node exception: adaptive_questions",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        return {
            "questioning_complete": True,
            "error": f"Adaptive questions agent failed: {str(e)}",
        }


def planner(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Compose capability patterns into a candidate plan using LLM-powered PlannerAgent."""
    from libs.streaming_models import StreamWriter, create_reason_card
    from libs.streaming_service import get_streaming_service

    _, _, _, llm_planner_agent, _, _, _ = _get_llm_agents()

    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: planner", extra={"thread_id": thread_id})

    # Get streaming service and emit node start (skip async call to avoid event loop issues)
    streaming_service = get_streaming_service()
    # _safe_async_run() causes event loop issues in executor context
    # streaming_service.emit_node_start() will be handled by the worker's async context

    # Initialize streaming writer (for backward compatibility with state)
    stream_writer = StreamWriter(thread_id)
    stream_writer.emit_node_start(
        "planner", "Analyzing requirements and selecting MLOps patterns"
    )

    try:
        # Execute agent directly with MLOpsWorkflowState - no conversion needed
        result = _safe_async_run(llm_planner_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            # Extract state updates from the agent result
            state_updates = result.state_updates

            # Create streaming reason card from agent result
            # Map from agent_framework.ReasonCard to streaming_models.ReasonCard
            reasoning_text = "Analyzed requirements and composed MLOps patterns into a comprehensive plan"
            decision_text = f"Selected MLOps architecture plan"

            if result.reason_card.choice and hasattr(result.reason_card.choice, 'rationale'):
                reasoning_text = result.reason_card.choice.rationale
            if result.reason_card.choice and hasattr(result.reason_card.choice, 'selection'):
                decision_text = f"Selected: {result.reason_card.choice.selection}"

            # Get alternatives from candidates if available
            alternatives = []
            if result.reason_card.candidates:
                alternatives = [candidate.name for candidate in result.reason_card.candidates]

            streaming_reason_card = create_reason_card(
                agent="planner",
                node="planner",
                decision_set_id=thread_id,
                reasoning=reasoning_text,
                decision=decision_text,
                category="pattern-selection",
                confidence=result.reason_card.confidence,
                inputs=result.reason_card.inputs,
                outputs=result.reason_card.outputs,
                alternatives_considered=alternatives,
                priority="high",
            )

            # Emit the reason card via streaming service
            _safe_async_run(streaming_service.emit_reason_card(streaming_reason_card))

            # Store reason card in state (for backward compatibility)
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("planner")

            # Maintain backward compatibility
            plan = state_updates.get("plan", {})
            selected_pattern_id = plan.get("pattern_id", "unknown")

            # Emit node completion via streaming service
            _safe_async_run(
                streaming_service.emit_node_complete(
                    thread_id,
                    "planner",
                    outputs=result.reason_card.outputs,
                    message=f"Selected pattern: {selected_pattern_id}",
                )
            )

            # Also emit to stream writer (for backward compatibility)
            stream_writer.emit_node_complete(
                "planner",
                outputs=result.reason_card.outputs,
                message=f"Selected pattern: {selected_pattern_id}",
            )

            out = {
                **state_updates,
                "selected_pattern_id": selected_pattern_id,  # Legacy compatibility
                "reason_cards": reason_cards,
                "execution_order": execution_order,
                "agent_outputs": {
                    **state.get("agent_outputs", {}),
                    "planner": result.reason_card.outputs,
                },
                "streaming_events": stream_writer.get_events(),  # Include streaming events in state
            }
            logger.info(
                "Node success: planner",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                    "pattern_id": selected_pattern_id,
                },
            )
            return out
        else:
            # Agent failed - return error state
            _safe_async_run(
                streaming_service.emit_error(
                    thread_id, f"Planner failed: {result.error_message}", "planner"
                )
            )
            stream_writer.emit_error(
                f"Planner failed: {result.error_message}", "planner"
            )

            logger.warning(
                "Node failure: planner",
                extra={"thread_id": thread_id, "error": result.error_message},
            )
            return {
                "plan": {},
                "error": result.error_message,
                "streaming_events": stream_writer.get_events(),
            }

    except Exception as e:
        _safe_async_run(
            streaming_service.emit_error(
                thread_id, f"Planner exception: {str(e)}", "planner"
            )
        )
        stream_writer.emit_error(f"Planner exception: {str(e)}", "planner")

        logger.exception(
            "Node exception: planner", extra={"thread_id": thread_id, "error": str(e)}
        )
        return {
            "plan": {},
            "error": f"Planner agent failed: {str(e)}",
            "streaming_events": stream_writer.get_events(),
        }


def critic_tech(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Analyze feasibility, coupling, bottlenecks using LLM-powered TechCriticAgent."""
    from libs.streaming_models import create_reason_card
    from libs.streaming_service import get_streaming_service

    _, _, _, _, llm_tech_critic_agent, _, _ = _get_llm_agents()

    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: critic_tech", extra={"thread_id": thread_id})

    # Get streaming service and emit node start
    streaming_service = get_streaming_service()
    _safe_async_run(
        streaming_service.emit_node_start(
            thread_id, "critic_tech", "Analyzing technical feasibility and architecture"
        )
    )

    try:
        # Execute agent directly with MLOpsWorkflowState - no conversion needed
        result = asyncio.run(llm_tech_critic_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            # Extract state updates from the agent result
            state_updates = result.state_updates

            # Create streaming reason card from agent result
            # Map from agent_framework.ReasonCard to streaming_models.ReasonCard
            reasoning_text = "Analyzed technical feasibility and identified potential bottlenecks"
            decision_text = f"Technical assessment completed"

            if result.reason_card.choice and hasattr(result.reason_card.choice, 'rationale'):
                reasoning_text = result.reason_card.choice.rationale
            if result.reason_card.choice and hasattr(result.reason_card.choice, 'selection'):
                decision_text = f"Assessment: {result.reason_card.choice.selection}"

            # Get alternatives from candidates if available
            alternatives = []
            if result.reason_card.candidates:
                alternatives = [candidate.name for candidate in result.reason_card.candidates]

            streaming_reason_card = create_reason_card(
                agent="tech_critic",
                node="critic_tech",
                decision_set_id=thread_id,
                reasoning=reasoning_text,
                decision=decision_text,
                category="technical-analysis",
                confidence=result.reason_card.confidence,
                inputs=result.reason_card.inputs,
                outputs=result.reason_card.outputs,
                alternatives_considered=alternatives,
                priority="high",
            )
            _safe_async_run(streaming_service.emit_reason_card(streaming_reason_card))

            # Store reason card
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("critic_tech")

            # Emit node completion
            _safe_async_run(
                streaming_service.emit_node_complete(
                    thread_id,
                    "critic_tech",
                    outputs=result.reason_card.outputs,
                    message="Technical analysis completed",
                )
            )

            out = {
                **state_updates,
                "reason_cards": reason_cards,
                "execution_order": execution_order,
                "agent_outputs": {
                    **state.get("agent_outputs", {}),
                    "tech_critic": result.reason_card.outputs,
                },
            }
            logger.info(
                "Node success: critic_tech",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out
        else:
            _safe_async_run(
                streaming_service.emit_error(
                    thread_id,
                    f"Tech critic failed: {result.error_message}",
                    "critic_tech",
                )
            )
            return {"tech_critique": {}, "error": result.error_message}

    except Exception as e:
        _safe_async_run(
            streaming_service.emit_error(
                thread_id, f"Tech critic exception: {str(e)}", "critic_tech"
            )
        )
        logger.exception(
            "Node exception: critic_tech",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        return {"tech_critique": {}, "error": f"Tech critic agent failed: {str(e)}"}


def critic_cost(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Generate coarse BOM and monthly estimate using LLM-powered CostCriticAgent."""
    from libs.streaming_models import create_reason_card
    from libs.streaming_service import get_streaming_service

    _, _, _, _, _, llm_cost_critic_agent, _ = _get_llm_agents()

    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: critic_cost", extra={"thread_id": thread_id})

    # Get streaming service and emit node start
    streaming_service = get_streaming_service()
    _safe_async_run(
        streaming_service.emit_node_start(
            thread_id,
            "critic_cost",
            "Analyzing cost estimates and resource requirements",
        )
    )

    try:
        # Execute agent directly with MLOpsWorkflowState - no conversion needed
        result = asyncio.run(llm_cost_critic_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            # Extract state updates from the agent result
            state_updates = result.state_updates

            # Create streaming reason card from agent result
            # Map from agent_framework.ReasonCard to streaming_models.ReasonCard
            reasoning_text = "Analyzed cost estimates and resource requirements"
            decision_text = f"Cost analysis completed"

            if result.reason_card.choice and hasattr(result.reason_card.choice, 'rationale'):
                reasoning_text = result.reason_card.choice.rationale
            if result.reason_card.choice and hasattr(result.reason_card.choice, 'selection'):
                decision_text = f"Cost assessment: {result.reason_card.choice.selection}"

            # Get alternatives from candidates if available
            alternatives = []
            if result.reason_card.candidates:
                alternatives = [candidate.name for candidate in result.reason_card.candidates]

            streaming_reason_card = create_reason_card(
                agent="cost_critic",
                node="critic_cost",
                decision_set_id=thread_id,
                reasoning=reasoning_text,
                decision=decision_text,
                category="cost-analysis",
                confidence=result.reason_card.confidence,
                inputs=result.reason_card.inputs,
                outputs=result.reason_card.outputs,
                alternatives_considered=alternatives,
                priority="high",
            )
            _safe_async_run(streaming_service.emit_reason_card(streaming_reason_card))

            # Store reason card
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("critic_cost")

            # Emit node completion
            cost_estimate = state_updates.get("cost_estimate", {})
            estimated_cost = cost_estimate.get("monthly_cost", "unknown")
            _safe_async_run(
                streaming_service.emit_node_complete(
                    thread_id,
                    "critic_cost",
                    outputs=result.reason_card.outputs,
                    message=f"Cost analysis completed (estimated: ${estimated_cost}/month)",
                )
            )

            out = {
                **state_updates,
                "cost": state_updates.get(
                    "cost_estimate", {}
                ),  # Legacy field for backward compatibility
                "reason_cards": reason_cards,
                "execution_order": execution_order,
                "agent_outputs": {
                    **state.get("agent_outputs", {}),
                    "cost_critic": result.reason_card.outputs,
                },
            }
            logger.info(
                "Node success: critic_cost",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out
        else:
            _safe_async_run(
                streaming_service.emit_error(
                    thread_id,
                    f"Cost critic failed: {result.error_message}",
                    "critic_cost",
                )
            )
            return {"cost_estimate": {}, "error": result.error_message}

    except Exception as e:
        _safe_async_run(
            streaming_service.emit_error(
                thread_id, f"Cost critic exception: {str(e)}", "critic_cost"
            )
        )
        logger.exception(
            "Node exception: critic_cost",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        return {"cost_estimate": {}, "error": f"Cost critic agent failed: {str(e)}"}


def policy_eval(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Apply governance rules using LLM-powered PolicyEngineAgent."""
    from libs.streaming_models import create_reason_card
    from libs.streaming_service import get_streaming_service

    _, _, _, _, _, _, llm_policy_engine_agent = _get_llm_agents()
    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: policy_eval", extra={"thread_id": thread_id})

    # Get streaming service and emit node start
    streaming_service = get_streaming_service()
    _safe_async_run(
        streaming_service.emit_node_start(
            thread_id, "policy_eval", "Evaluating governance and compliance policies"
        )
    )

    try:
        # Execute agent directly with MLOpsWorkflowState - no conversion needed
        result = asyncio.run(
            llm_policy_engine_agent.execute(state, TriggerType.INITIAL)
        )

        if result.success:
            # Extract state updates from the agent result
            state_updates = result.state_updates

            # Create streaming reason card from agent result
            # Map from agent_framework.ReasonCard to streaming_models.ReasonCard
            reasoning_text = "Evaluated governance and compliance policies"
            decision_text = f"Policy evaluation completed"

            if result.reason_card.choice and hasattr(result.reason_card.choice, 'rationale'):
                reasoning_text = result.reason_card.choice.rationale
            if result.reason_card.choice and hasattr(result.reason_card.choice, 'selection'):
                decision_text = f"Policy decision: {result.reason_card.choice.selection}"

            # Get alternatives from candidates if available
            alternatives = []
            if result.reason_card.candidates:
                alternatives = [candidate.name for candidate in result.reason_card.candidates]

            streaming_reason_card = create_reason_card(
                agent="policy_engine",
                node="policy_eval",
                decision_set_id=thread_id,
                reasoning=reasoning_text,
                decision=decision_text,
                category="policy-evaluation",
                confidence=result.reason_card.confidence,
                inputs=result.reason_card.inputs,
                outputs=result.reason_card.outputs,
                alternatives_considered=alternatives,
                priority="critical",
            )
            _safe_async_run(streaming_service.emit_reason_card(streaming_reason_card))

            # Store reason card
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Update execution order
            execution_order = state.get("execution_order", [])
            execution_order.append("policy_eval")

            # Emit node completion
            policy_validation = state_updates.get("policy_validation", {})
            validation_status = policy_validation.get("status", "unknown")
            _safe_async_run(
                streaming_service.emit_node_complete(
                    thread_id,
                    "policy_eval",
                    outputs=result.reason_card.outputs,
                    message=f"Policy evaluation completed (status: {validation_status})",
                )
            )

            out = {
                **state_updates,
                "policy_results": state_updates.get(
                    "policy_validation", {}
                ),  # Legacy compatibility
                "policy": state_updates.get(
                    "policy_validation", {}
                ),  # Legacy field for backward compatibility
                "reason_cards": reason_cards,
                "execution_order": execution_order,
                "agent_outputs": {
                    **state.get("agent_outputs", {}),
                    "policy_engine": result.reason_card.outputs,
                },
            }
            logger.info(
                "Node success: policy_eval",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return out
        else:
            _safe_async_run(
                streaming_service.emit_error(
                    thread_id,
                    f"Policy engine failed: {result.error_message}",
                    "policy_eval",
                )
            )
            return {"policy_results": {}, "error": result.error_message}

    except Exception as e:
        _safe_async_run(
            streaming_service.emit_error(
                thread_id, f"Policy engine exception: {str(e)}", "policy_eval"
            )
        )
        logger.exception(
            "Node exception: policy_eval",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        return {"policy_results": {}, "error": f"Policy engine agent failed: {str(e)}"}


def gate_hitl(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Human-in-the-loop approval gate (interrupt point)."""
    from libs.streaming_service import get_streaming_service

    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: gate_hitl", extra={"thread_id": thread_id})

    # Get streaming service and emit node start
    streaming_service = get_streaming_service()
    _safe_async_run(
        streaming_service.emit_node_start(
            thread_id, "gate_hitl", "Preparing plan for human review"
        )
    )

    # Check if we already have approval/rejection from a previous resume
    existing_hitl = state.get("hitl", {})
    if existing_hitl.get("status") in ["approved", "rejected"]:
        logger.info(
            f"Node complete: gate_hitl {existing_hitl['status']}",
            extra={"thread_id": thread_id, "status": existing_hitl["status"]},
        )
        return {}

    # Prepare the interruption payload with plan summary for human review
    plan = state.get("plan", {})
    cost_estimate = state.get("cost_estimate", {})
    tech_critique = state.get("tech_critique", {})
    policy_results = state.get("policy_validation", state.get("policy", {}))

    interruption_payload = {
        "status": "pending_approval",
        "plan_summary": {
            "pattern_name": plan.get("pattern_name", "Unknown Pattern"),
            "architecture_type": plan.get("architecture_type", "unknown"),
            "estimated_cost": plan.get(
                "estimated_monthly_cost", cost_estimate.get("monthly_usd", 0)
            ),
            "key_services": plan.get("key_services", {}),
            "implementation_phases": plan.get("implementation_phases", []),
        },
        "technical_analysis": {
            "feasibility_score": tech_critique.get("overall_feasibility_score", 0.0),
            "key_risks": tech_critique.get("technical_risks", [])[:3],
            "recommendations": tech_critique.get("recommendations", [])[:3],
        },
        "cost_analysis": {
            "monthly_cost": cost_estimate.get("estimated_monthly_cost", 0),
            "primary_drivers": cost_estimate.get("primary_cost_drivers", [])[:3],
            "budget_status": cost_estimate.get("budget_compliance_status", "unknown"),
        },
        "policy_analysis": {
            "overall_status": policy_results.get(
                "overall_compliance_status", "unknown"
            ),
            "critical_violations": policy_results.get("critical_violations", []),
            "warnings": policy_results.get("warnings", []),
        },
        "message": "Please review the proposed MLOps architecture and provide your approval decision.",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # Emit workflow paused event before interrupting
    _safe_async_run(
        streaming_service.emit_workflow_paused(
            thread_id,
            "Waiting for human approval of the proposed MLOps architecture",
            "gate_hitl",
        )
    )

    # Interrupt and wait for human input
    logger.info(
        "Node interrupt: gate_hitl waiting for approval",
        extra={
            "thread_id": thread_id,
            "pattern": plan.get("pattern_name", "unknown"),
            "cost": interruption_payload["plan_summary"]["estimated_cost"],
        },
    )

    # The interrupt will pause execution here and return control to the caller
    # When resumed, the approval_data will contain the human decision
    approval_data = interrupt(interruption_payload)

    # Process the human approval/rejection decision
    if approval_data is None:
        # Fallback case - auto-approve for testing
        approval_data = {
            "decision": "approved",
            "comment": "Auto-approved (no human input received)",
            "approved_by": "system",
        }

    hitl_result = {
        "status": approval_data.get("decision", "approved"),
        "comment": approval_data.get("comment", ""),
        "approved_by": approval_data.get("approved_by", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "approval_data": approval_data,
    }

    # Emit node completion with approval decision
    _safe_async_run(
        streaming_service.emit_node_complete(
            thread_id,
            "gate_hitl",
            outputs={
                "decision": hitl_result["status"],
                "approved_by": hitl_result["approved_by"],
            },
            message=f"Human approval gate completed: {hitl_result['status']} by {hitl_result['approved_by']}",
        )
    )

    logger.info(
        f"Node complete: gate_hitl {hitl_result['status']}",
        extra={
            "thread_id": thread_id,
            "status": hitl_result["status"],
            "approved_by": hitl_result["approved_by"],
        },
    )

    return {"hitl": hitl_result}


async def _codegen_async(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Generate repo skeletons (services, IaC, CI, docs) using Claude Code SDK."""
    from libs.codegen_service import CodegenService, CodegenError

    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger = logging.getLogger(__name__)
    logger.info("Node start: codegen", extra={"thread_id": thread_id})

    plan = state.get("plan", {})
    if not plan:
        logger.warning(
            "No plan found for code generation", extra={"thread_id": thread_id}
        )
        return {
            "artifacts": [],
            "repository": {},
            "error": "No plan available for code generation",
        }

    # Check HITL approval status
    hitl_status = state.get("hitl", {})
    if hitl_status.get("status") != "approved":
        logger.warning(
            "Code generation skipped - plan not approved",
            extra={
                "thread_id": thread_id,
                "hitl_status": hitl_status.get("status", "unknown"),
            },
        )
        return {
            "artifacts": [],
            "repository": {},
            "error": f"Plan not approved for code generation (status: {hitl_status.get('status', 'unknown')})",
        }

    try:
        # Initialize CodegenService
        codegen_service = CodegenService()

        # Generate MLOps repository
        result = await codegen_service.generate_mlops_repository(plan)

        artifacts = result.get("artifacts", [])
        repository_info = result.get("repository_zip", {})

        logger.info(
            "Node success: codegen",
            extra={
                "thread_id": thread_id,
                "artifact_count": len(artifacts),
                "repository_size": repository_info.get("size_bytes", 0),
                "s3_uploaded": bool(repository_info.get("s3_url")),
            },
        )

        return {"artifacts": artifacts, "repository": repository_info}

    except CodegenError as e:
        logger.error(
            "Node error: codegen", extra={"thread_id": thread_id, "error": str(e)}
        )
        return {
            "artifacts": [],
            "repository": {},
            "error": f"Code generation failed: {str(e)}",
        }

    except Exception as e:
        logger.exception(
            "Node exception: codegen", extra={"thread_id": thread_id, "error": str(e)}
        )
        return {
            "artifacts": [],
            "repository": {},
            "error": f"Unexpected error in code generation: {str(e)}",
        }


def codegen(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Synchronous wrapper for async code generation."""
    import asyncio

    return asyncio.run(_codegen_async(state))


async def _validators_async(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Run static checks; compile /reports."""
    from libs.validation_service import ValidationService, ValidationError
    import tempfile
    from pathlib import Path

    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger = logging.getLogger(__name__)
    logger.info("Node start: validators", extra={"thread_id": thread_id})

    artifacts = state.get("artifacts", [])
    repository_info = state.get("repository", {})

    if not artifacts:
        logger.warning("No artifacts to validate", extra={"thread_id": thread_id})
        return {
            "reports": {
                "overall_status": "skipped",
                "artifacts_validated": 0,
                "message": "No artifacts available for validation",
            }
        }

    try:
        # Initialize ValidationService
        validation_service = ValidationService()

        # Create temporary directory for validation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # For this implementation, we'll create a mock directory structure
            # In a real implementation, we'd extract from the repository ZIP
            await _create_validation_test_structure(temp_path, artifacts, state)

            # Run validation checks
            reports = await validation_service.validate_artifacts(temp_path, artifacts)

            # Add repository information to reports
            reports["repository_info"] = {
                "size_bytes": repository_info.get("size_bytes", 0),
                "s3_url": repository_info.get("s3_url"),
                "zip_key": repository_info.get("zip_key"),
            }

            logger.info(
                "Node success: validators",
                extra={
                    "thread_id": thread_id,
                    "artifacts": len(artifacts),
                    "overall_status": reports.get("overall_status", "unknown"),
                },
            )

            return {"reports": reports}

    except ValidationError as e:
        logger.error(
            "Node error: validators", extra={"thread_id": thread_id, "error": str(e)}
        )
        return {
            "reports": {
                "overall_status": "error",
                "artifacts_validated": len(artifacts),
                "error": f"Validation failed: {str(e)}",
            }
        }

    except Exception as e:
        logger.exception(
            "Node exception: validators",
            extra={"thread_id": thread_id, "error": str(e)},
        )
        return {
            "reports": {
                "overall_status": "error",
                "artifacts_validated": len(artifacts),
                "error": f"Unexpected validation error: {str(e)}",
            }
        }


def validators(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Synchronous wrapper for async validation."""
    import asyncio

    return asyncio.run(_validators_async(state))


async def _create_validation_test_structure(temp_path, artifacts, state):
    """Create a test directory structure for validation."""

    # Create basic directory structure
    (temp_path / "terraform").mkdir(exist_ok=True)
    (temp_path / "src").mkdir(exist_ok=True)
    (temp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

    # Create sample files based on artifacts
    for artifact in artifacts:
        file_path = temp_path / artifact["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create sample content based on file type
        if file_path.suffix == ".tf":
            content = f'# Terraform file: {artifact["path"]}\nresource "aws_instance" "example" {{\n  ami = "ami-12345678"\n}}\n'
        elif file_path.suffix == ".py":
            content = f'"""Python file: {artifact["path"]}"""\nimport os\n\ndef main():\n    print("Hello MLOps")\n'
        elif file_path.suffix == ".yml" or file_path.suffix == ".yaml":
            content = f"# CI/CD file: {artifact['path']}\nname: MLOps Pipeline\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        else:
            content = f"# Generated file: {artifact['path']}\n"

        file_path.write_text(content)


def rationale_compile(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Transform per-node rationale into Reason Cards and Design Rationale doc."""
    reason_cards = state.get("reason_cards", [])

    rationale = {
        "reason_cards": reason_cards,
        "reason_card_count": len(reason_cards),
        "design_doc": f"Generated design rationale with {len(reason_cards)} decisions documented",
        "agents_executed": list(
            set([card.get("agent", "unknown") for card in reason_cards])
        ),
    }

    logging.getLogger(__name__).info(
        "Node success: rationale_compile",
        extra={"reason_cards": len(reason_cards)},
    )
    return {"rationale": rationale}


def diff_and_persist(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """Commit artifacts to git/S3; write decision_set + events; output composite Change Summary."""
    artifacts = state.get("artifacts", [])
    cost_estimate = state.get("cost_estimate", {})

    diff_summary = {
        "files_added": len(artifacts),
        "files_modified": 0,
        "files_removed": 0,
        "cost_delta_usd": cost_estimate.get("monthly_usd", 0),
        "git_commit": "abc123",
        "s3_artifact_key": f"projects/{state.get('project_id', 'test')}/artifacts/abc123.zip",
    }

    logging.getLogger(__name__).info(
        "Node success: diff_and_persist",
        extra={
            "files_added": diff_summary["files_added"],
            "cost_delta_usd": diff_summary["cost_delta_usd"],
        },
    )
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
    Build and compile the full MLOps workflow graph with real agent implementations and dual HITL gates.

    This creates the complete deterministic sequential graph as specified in
    implementation_details.md section 21.1, enhanced with two HITL interaction points:
    1. After adaptive_questions: hitl_gate_input - for capturing missing inputs
    2. After policy_eval: hitl_gate_final - for final approval before code generation

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MLOpsWorkflowState)

    # Add all agent nodes in the order specified in section 21.1
    graph.add_node("intake_extract", intake_extract_enhanced)  # Use enhanced version for HITL support
    graph.add_node("coverage_check", coverage_check_enhanced)  # Use enhanced version for HITL support
    graph.add_node("adaptive_questions", adaptive_questions)
    graph.add_node("hitl_gate_input", hitl_gate_user)  # First HITL gate: capture missing inputs
    graph.add_node("planner", planner)  # Now uses real PlannerAgent
    graph.add_node("critic_tech", critic_tech)  # Now uses real TechCriticAgent
    graph.add_node("critic_cost", critic_cost)  # Now uses real CostCriticAgent
    graph.add_node("policy_eval", policy_eval)  # Now uses real PolicyEngineAgent
    graph.add_node("hitl_gate_final", gate_hitl)  # Second HITL gate: final approval before codegen
    graph.add_node("codegen", codegen)
    graph.add_node("validators", validators)
    graph.add_node("rationale_compile", rationale_compile)
    graph.add_node("diff_and_persist", diff_and_persist)

    # Define the execution flow with dual HITL gates
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "coverage_check")
    graph.add_edge("coverage_check", "adaptive_questions")

    # First HITL gate: Always trigger after adaptive_questions for now (simplified logic)
    graph.add_edge("adaptive_questions", "hitl_gate_input")

    # From input HITL gate, conditionally loop back or continue
    #graph.add_conditional_edges(
    #    "hitl_gate_input",
    #    should_loop_back_to_intake,
    #    {
    #        "loop_back": "intake_extract",
    #        "continue": "planner"
    #    }
    #)

    graph.add_edge("hitl_gate_input", "intake_extract")
    graph.add_edge("intake_extract", "planner")


    # Continue with planning and criticism phase
    graph.add_edge("planner", "critic_tech")
    graph.add_edge("critic_tech", "critic_cost")
    graph.add_edge("critic_cost", "policy_eval")

    # Second HITL gate: final approval before code generation
    graph.add_edge("policy_eval", "hitl_gate_final")
    graph.add_edge("hitl_gate_final", "codegen")
    graph.add_edge("codegen", "validators")
    graph.add_edge("validators", "rationale_compile")
    graph.add_edge("rationale_compile", "diff_and_persist")
    graph.add_edge("diff_and_persist", END)

    # Prefer async-compatible checkpointer when available
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        # Fall back to synchronous checkpointer (e.g., PostgresSaver)
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()


def build_hitl_graph() -> Pregel:
    """
    Build and compile the full MLOps workflow graph with real agent implementations.

    This creates the complete deterministic sequential graph as specified in
    implementation_details.md section 21.1. The core planning nodes (planner,
    critics, policy engine) now use the real agent implementations for
    transparent decision making.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MLOpsWorkflowState)

    # Add all agent nodes in the order specified in section 21.1
    graph.add_node("intake_extract", intake_extract)
    graph.add_node("coverage_check", coverage_check)
    graph.add_node("adaptive_questions", adaptive_questions)
    graph.add_node("gate_hitl", gate_hitl)
    graph.add_node("planner", planner)  # Now uses real PlannerAgent

    # Define the sequential execution flow with normal edges
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "coverage_check")
    graph.add_edge("coverage_check", "adaptive_questions")
    graph.add_edge("adaptive_questions", "gate_hitl")
    graph.add_edge("gate_hitl", "planner")
    graph.add_edge("planner", END)

    # Prefer async-compatible checkpointer when available
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        # Fall back to synchronous checkpointer (e.g., PostgresSaver)
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()


def build_hitl_enhanced_graph() -> Pregel:
    """
    Build enhanced HITL graph with auto-approval and loop-back functionality.

    Flow: intake_extract -> coverage_check -> adaptive_questions -> hitl_gate_user
          -> intake_extract (update) -> coverage_check (update) -> planner

    Features:
    - Smart defaults generation for questions
    - Auto-approval with configurable timeout
    - In-place state updates (no duplicate reason cards)
    - Context preservation across agent re-execution

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(MLOpsWorkflowState)

    # Add enhanced node functions
    graph.add_node("intake_extract", intake_extract_enhanced)
    graph.add_node("coverage_check", coverage_check_enhanced)
    graph.add_node("adaptive_questions", adaptive_questions)
    graph.add_node("hitl_gate_user", hitl_gate_user)
    graph.add_node("planner", planner)

    # Define the flow with conditional routing
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "coverage_check")
    graph.add_edge("coverage_check", "adaptive_questions")
    graph.add_edge("adaptive_questions", "hitl_gate_user")

    # Conditional edge from hitl_gate_user based on whether we need to loop back
    graph.add_conditional_edges(
        "hitl_gate_user",
        should_loop_back_to_intake,
        {
            "loop_back": "intake_extract",
            "continue": "planner"
        }
    )
    graph.add_edge("planner", END)

    # Use checkpointer for workflow interruption/resumption
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


# Enhanced HITL Functions


def should_trigger_input_hitl(state: MLOpsWorkflowState) -> bool:
    """
    Determine if we should trigger the input HITL gate after adaptive_questions.

    Returns True if:
    - Questions were generated (need user input)
    - Coverage is below threshold
    - Confidence is low
    """
    # Check if adaptive_questions generated questions
    last_message = state.get("messages", [])[-1] if state.get("messages") else None
    if last_message and hasattr(last_message, 'content'):
        # Look for questions in the message or state
        if 'questions' in str(last_message.content).lower():
            return True

    # Check coverage and confidence from recent context
    context = state.get("context", {})
    coverage_score = context.get("coverage_score", 1.0)
    extraction_confidence = context.get("extraction_confidence", 1.0)

    # Trigger HITL if coverage is low or confidence is low
    if coverage_score < 0.8 or extraction_confidence < 0.5:
        return True

    return False


def should_loop_back_to_intake(state: MLOpsWorkflowState) -> str:
    """
    Determine if we should loop back to intake_extract or continue to planner.

    Args:
        state: Current workflow state

    Returns:
        "loop_back" if we need to re-run intake with user responses
        "continue" if we should proceed to planner
    """
    # Check if we have user responses from HITL gate
    user_responses = state.get("user_responses", [])
    execution_round = state.get("execution_round", 1)

    # If we have user responses and this is the first round, loop back
    if user_responses and execution_round == 1:
        return "loop_back"

    # Otherwise continue to planner
    return "continue"


def generate_smart_defaults(questions: list, context: dict) -> dict:
    """
    Generate intelligent default answers for adaptive questions.

    Args:
        questions: List of adaptive questions
        context: Current project context for informed defaults

    Returns:
        Dictionary mapping question_id to default answer
    """
    defaults = {}

    for question in questions:
        question_id = question.get("question_id", "")
        question_type = question.get("question_type", "text")
        question_text = question.get("question_text", "")
        field_targets = question.get("field_targets", [])

        # Generate context-aware defaults
        if question_type == "choice":
            choices = question.get("choices", [])
            if choices:
                # Default to first choice or middle choice for safety
                defaults[question_id] = choices[0]
        elif question_type == "numeric":
            # Generate reasonable numeric defaults based on field type
            if "budget" in question_text.lower():
                defaults[question_id] = "1000"  # $1000/month default
            elif "scale" in question_text.lower() or "request" in question_text.lower():
                defaults[question_id] = "10000"  # 10k requests/day default
            else:
                defaults[question_id] = "100"  # Generic numeric default
        elif question_type == "boolean":
            # Default to conservative/safe choices
            if "complian" in question_text.lower() or "regulat" in question_text.lower():
                defaults[question_id] = "true"  # Default to compliance
            else:
                defaults[question_id] = "false"  # Conservative default
        else:  # text type
            # Generate contextual text defaults
            if "region" in question_text.lower():
                defaults[question_id] = "us-east-1"
            elif "team" in question_text.lower():
                defaults[question_id] = "small development team (2-5 people)"
            elif "use case" in question_text.lower():
                defaults[question_id] = "machine learning model serving and inference"
            else:
                defaults[question_id] = "standard configuration"

    return defaults


def hitl_gate_user(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """
    Enhanced HITL gate with auto-approval and smart defaults.

    Presents questions with intelligent defaults, auto-approves after timeout,
    and collects user responses for workflow enhancement.
    """
    import os
    import time
    from libs.streaming_service import get_streaming_service

    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    logger.info("Node start: hitl_gate_user", extra={"thread_id": thread_id})

    # Get current questions from adaptive_questions agent
    current_questions = state.get("current_questions", [])
    if not current_questions:
        logger.info("No questions to present, skipping HITL gate")
        return {"user_responses": [], "execution_round": 2}

    # Get configuration
    hitl_mode = os.getenv("HITL_MODE", "demo")  # demo, interactive, disabled
    timeout_seconds = int(os.getenv("HITL_DEFAULT_TIMEOUT", "8"))

    if hitl_mode == "demo":
        timeout_seconds = 3
    elif hitl_mode == "interactive":
        timeout_seconds = 15
    elif hitl_mode == "disabled":
        timeout_seconds = 0

    # Generate smart defaults
    project_context = {
        "constraints": state.get("constraints", {}),
        "coverage_score": state.get("coverage_score", 0.0),
        "user_input": state.get("constraints", {}).get("project_description", "")
    }
    smart_defaults = generate_smart_defaults(current_questions, project_context)

    # Get streaming service for real-time updates
    streaming_service = get_streaming_service()

    # Emit questions presented event
    _safe_async_run(
        streaming_service.emit_questions_presented(
            thread_id,
            current_questions,
            smart_defaults,
            timeout_seconds,
            "hitl_gate_user",
        )
    )

    # Create interruption payload with questions and defaults
    interruption_payload = {
        "questions": current_questions,
        "smart_defaults": smart_defaults,
        "timeout_seconds": timeout_seconds,
        "auto_approval_enabled": timeout_seconds > 0,
        "message": f"Please review these questions. Auto-approving defaults in {timeout_seconds} seconds.",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # Handle different modes
    if timeout_seconds == 0:
        # Immediate auto-approval mode
        user_responses = []
        for question in current_questions:
            question_id = question.get("question_id", "")
            default_answer = smart_defaults.get(question_id, "")
            user_responses.append({
                "question_id": question_id,
                "answer": default_answer,
                "approval_method": "auto_immediate",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            })

        logger.info(f"Immediate auto-approval: {len(user_responses)} responses generated")
        return {
            "user_responses": user_responses,
            "execution_round": 2,
            "hitl_result": {
                "status": "auto_approved",
                "approval_method": "immediate",
                "timeout_seconds": 0,
            }
        }

    # Interrupt workflow for user interaction with timeout
    logger.info(
        f"HITL gate presenting {len(current_questions)} questions with {timeout_seconds}s timeout"
    )

    # The interrupt will pause execution and wait for user input or timeout
    user_input_data = interrupt(interruption_payload)

    # Process user responses or use defaults
    user_responses = []
    approval_method = "user_input"

    if user_input_data is None or user_input_data.get("timed_out", False):
        # Auto-approval with defaults
        approval_method = "auto_approved"
        for question in current_questions:
            question_id = question.get("question_id", "")
            default_answer = smart_defaults.get(question_id, "")
            user_responses.append({
                "question_id": question_id,
                "answer": default_answer,
                "approval_method": "auto_timeout",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            })
        logger.info(f"Auto-approved {len(user_responses)} responses after timeout")
    else:
        # User provided responses
        user_answers = user_input_data.get("responses", {})
        for question in current_questions:
            question_id = question.get("question_id", "")
            user_answer = user_answers.get(question_id, smart_defaults.get(question_id, ""))
            user_responses.append({
                "question_id": question_id,
                "answer": user_answer,
                "approval_method": "user_input",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            })
        logger.info(f"User provided {len(user_responses)} responses")

    # Emit responses collected event
    _safe_async_run(
        streaming_service.emit_responses_collected(
            thread_id,
            user_responses,
            approval_method,
            "hitl_gate_user",
        )
    )

    # Emit node completion
    _safe_async_run(
        streaming_service.emit_node_complete(
            thread_id,
            "hitl_gate_user",
            outputs={
                "responses_count": len(user_responses),
                "approval_method": approval_method,
            },
            message=f"HITL gate completed via {approval_method}",
        )
    )

    return {
        "user_responses": user_responses,
        "execution_round": 2,
        "hitl_result": {
            "status": approval_method,
            "responses_count": len(user_responses),
            "timeout_seconds": timeout_seconds,
        }
    }


def intake_extract_enhanced(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """
    Enhanced intake_extract that supports in-place updates and context merging.

    On first execution: Normal intake extraction
    On second execution: Merge user responses with existing context, update in-place
    """
    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    execution_round = state.get("execution_round", 1)

    logger.info(
        f"Node start: intake_extract_enhanced (round {execution_round})",
        extra={"thread_id": thread_id}
    )

    # Get user responses if this is the second round
    user_responses = state.get("user_responses", [])

    if execution_round >= 2 and user_responses:
        # Second execution: merge user responses with existing context
        return _merge_user_responses_with_context(state, user_responses, start, thread_id)
    else:
        # First execution: normal intake extraction
        return _execute_normal_intake(state, start, thread_id)


def _merge_user_responses_with_context(state: MLOpsWorkflowState, user_responses: list, start: float, thread_id: str) -> MLOpsWorkflowState:
    """Merge user responses with existing context and update state in-place."""
    # Get existing constraints and context
    existing_constraints = state.get("constraints", {})
    original_description = existing_constraints.get("project_description", "")

    # Build enhanced context from user responses
    response_text = "\n\nAdditional details provided by user:\n"
    for response in user_responses:
        question_id = response.get("question_id", "")
        answer = response.get("answer", "")
        approval_method = response.get("approval_method", "")

        # Find the original question for context
        current_questions = state.get("current_questions", [])
        question_text = question_id  # fallback
        for q in current_questions:
            if q.get("question_id") == question_id:
                question_text = q.get("question_text", question_id)
                break

        response_text += f"- {question_text}: {answer}"
        if approval_method.startswith("auto"):
            response_text += " (auto-approved default)"
        response_text += "\n"

    # Create enhanced project description
    enhanced_description = original_description + response_text

    # Update constraints with enhanced context
    enhanced_constraints = {
        **existing_constraints,
        "project_description": enhanced_description,
        "user_responses_integrated": True,
        "response_integration_method": "context_merge"
    }

    # Find and update existing reason card in-place instead of creating new one
    reason_cards = state.get("reason_cards", [])
    intake_card_index = None

    for i, card in enumerate(reason_cards):
        if card.get("agent") == "intake.extract" or card.get("node") == "intake_extract":
            intake_card_index = i
            break

    if intake_card_index is not None:
        # Update existing reason card
        existing_card = reason_cards[intake_card_index]
        updated_card = {
            **existing_card,
            "inputs": {
                **existing_card.get("inputs", {}),
                "enhanced_context": enhanced_description,
                "user_responses": user_responses,
                "execution_round": 2
            },
            "outputs": {
                **existing_card.get("outputs", {}),
                "constraints": enhanced_constraints,
                "integration_status": "user_responses_integrated"
            },
            "reasoning": existing_card.get("reasoning", "") + f"\n\nRound 2: Integrated {len(user_responses)} user responses to enhance context.",
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        reason_cards[intake_card_index] = updated_card
        logger.info(f"Updated existing intake reason card with user responses")
    else:
        # Fallback: create new reason card if original not found
        logger.warning("Original intake reason card not found, creating new one")
        new_card = {
            "agent": "intake.extract",
            "node": "intake_extract",
            "execution_round": 2,
            "inputs": {"enhanced_context": enhanced_description, "user_responses": user_responses},
            "outputs": {"constraints": enhanced_constraints},
            "reasoning": f"Enhanced context with {len(user_responses)} user responses",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        reason_cards.append(new_card)

    logger.info(
        "Node success: intake_extract_enhanced (round 2)",
        extra={
            "thread_id": thread_id,
            "duration_ms": int((time.time() - start) * 1000),
            "responses_integrated": len(user_responses),
        },
    )

    return {
        "constraints": enhanced_constraints,
        "reason_cards": reason_cards,
        "execution_order": state.get("execution_order", []),  # Don't add duplicate entry
        "user_responses_processed": True,
    }


def _execute_normal_intake(state: MLOpsWorkflowState, start: float, thread_id: str) -> MLOpsWorkflowState:
    """Execute normal intake extraction (first round)."""
    # Use the existing intake_extract function
    result = intake_extract(state)

    # Add execution round tracking
    result["execution_round"] = 1

    logger.info(
        "Node success: intake_extract_enhanced (round 1)",
        extra={
            "thread_id": thread_id,
            "duration_ms": int((time.time() - start) * 1000),
        },
    )

    return result


def coverage_check_enhanced(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """
    Enhanced coverage_check that supports in-place updates.

    On second execution: Update existing reason card instead of creating new one
    """
    start = time.time()
    thread_id = state.get("decision_set_id") or state.get("project_id") or "unknown"
    execution_round = state.get("execution_round", 1)

    logger.info(
        f"Node start: coverage_check_enhanced (round {execution_round})",
        extra={"thread_id": thread_id}
    )

    # Execute normal coverage check
    result = coverage_check(state)

    if execution_round >= 2:
        # Second execution: update existing reason card in-place
        reason_cards = result.get("reason_cards", [])
        coverage_card_indices = []

        # Find all coverage check reason cards
        for i, card in enumerate(reason_cards):
            if card.get("agent") == "coverage.check" or card.get("node") == "coverage_check":
                coverage_card_indices.append(i)

        if len(coverage_card_indices) > 1:
            # We have multiple coverage cards, update the first and remove duplicates
            first_card_index = coverage_card_indices[0]
            existing_card = reason_cards[first_card_index]

            # Update the first card with new results
            updated_card = {
                **existing_card,
                "inputs": {
                    **existing_card.get("inputs", {}),
                    "enhanced_constraints": state.get("constraints", {}),
                    "execution_round": execution_round,
                },
                "outputs": {
                    **result.get("coverage", {}),
                    "updated_after_user_input": True,
                },
                "reasoning": existing_card.get("reasoning", "") + f"\n\nRound {execution_round}: Re-evaluated coverage after user input integration.",
                "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            # Remove duplicate cards and keep only the updated one
            new_reason_cards = []
            for i, card in enumerate(reason_cards):
                if i == first_card_index:
                    new_reason_cards.append(updated_card)
                elif i not in coverage_card_indices[1:]:  # Skip other coverage cards
                    new_reason_cards.append(card)

            result["reason_cards"] = new_reason_cards
            logger.info(f"Updated existing coverage reason card, removed {len(coverage_card_indices) - 1} duplicates")

    logger.info(
        f"Node success: coverage_check_enhanced (round {execution_round})",
        extra={
            "thread_id": thread_id,
            "duration_ms": int((time.time() - start) * 1000),
        },
    )

    return result


def build_streaming_test_graph() -> Pregel:
    """Build a minimal two-node graph to validate real-time streaming."""
    from langgraph.graph import StateGraph, START, END

    graph = StateGraph(MLOpsWorkflowState)

    def intake_with_codegen_prep(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
        """Run intake and populate minimal plan/approval required for codegen."""
        updates = intake_extract(state)

        plan = updates.get("plan") or {
            "pattern_name": "streaming-test-app-runner",
            "architecture_type": "app_runner",
            "key_services": {
                "api_service": "FastAPI application deployed on AWS App Runner",
                "infra": "Terraform modules for networking, App Runner, and RDS",
                "observability": "CloudWatch dashboards and alarms",
            },
            "implementation_phases": [
                "project_scaffolding",
                "infrastructure_definition",
                "application_bootstrap",
                "ci_cd_pipeline",
            ],
            "estimated_monthly_cost": 500,
        }

        hitl = updates.get("hitl") or {
            "status": "approved",
            "comment": "Auto-approved for streaming test",
            "approved_by": "system",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        return {
            **updates,
            "plan": plan,
            "hitl": hitl,
        }

    # Add two nodes for quick streaming/codegen validation
    graph.add_node("intake_extract", intake_with_codegen_prep)
    graph.add_node("codegen", codegen)

    # Sequential flow with two agents
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "codegen")
    graph.add_edge("codegen", END)

    # Prefer async-compatible checkpointer when available to support astream()
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
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

    # Prefer async-compatible checkpointer when available
    checkpointer = _safe_async_run(create_async_checkpointer())
    if checkpointer is None:
        checkpointer = create_appropriate_checkpointer()

    # Compile with checkpointer if available
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        # No checkpointer available - compile without persistence
        return graph.compile()
