"""
Mock agents for testing HITL functionality without API calls.

This module provides mock implementations of agents that generate realistic
test data for development and testing purposes, avoiding expensive API calls.
"""

import os
import random
import time
from typing import Dict, List, Any
from datetime import datetime, timezone

from libs.agent_framework import MLOpsWorkflowState
from libs.constraint_schema import AdaptiveQuestion, AdaptiveQuestioningResult


class MockAdaptiveQuestionsAgent:
    """
    Mock implementation of adaptive questions agent for testing.

    Generates realistic questions based on project context without LLM calls.
    """

    def __init__(self):
        self.question_templates = {
            "budget": {
                "question_text": "What's your monthly budget range for this MLOps platform?",
                "question_type": "choice",
                "field_targets": ["budget_band", "monthly_budget_limit"],
                "priority": "high",
                "choices": [
                    "Startup budget (under $500/month)",
                    "Growth budget ($500-1500/month)",
                    "Enterprise budget ($1500+/month)"
                ]
            },
            "scale": {
                "question_text": "What's your expected daily request volume?",
                "question_type": "choice",
                "field_targets": ["expected_requests_per_day", "scale_requirements"],
                "priority": "high",
                "choices": [
                    "Light usage (under 1,000 requests/day)",
                    "Moderate usage (1,000-10,000 requests/day)",
                    "Heavy usage (10,000+ requests/day)"
                ]
            },
            "team_size": {
                "question_text": "How many people are on your development team?",
                "question_type": "choice",
                "field_targets": ["team_size", "operational_complexity"],
                "priority": "medium",
                "choices": [
                    "Solo developer (1 person)",
                    "Small team (2-5 people)",
                    "Medium team (6-15 people)",
                    "Large team (15+ people)"
                ]
            },
            "data_sensitivity": {
                "question_text": "Do you handle any regulated or sensitive data?",
                "question_type": "boolean",
                "field_targets": ["data_classification", "compliance_requirements"],
                "priority": "high"
            },
            "deployment_preference": {
                "question_text": "What's your preferred deployment approach?",
                "question_type": "choice",
                "field_targets": ["deployment_preference", "infrastructure_preference"],
                "priority": "medium",
                "choices": [
                    "Fully managed services (least operations)",
                    "Containerized deployment (moderate control)",
                    "Custom infrastructure (full control)"
                ]
            },
            "region": {
                "question_text": "Which AWS region should we target for deployment?",
                "question_type": "choice",
                "field_targets": ["aws_region", "latency_requirements"],
                "priority": "low",
                "choices": [
                    "US East (us-east-1) - Default",
                    "US West (us-west-2) - West Coast",
                    "Europe (eu-west-1) - Ireland",
                    "Asia Pacific (ap-southeast-1) - Singapore"
                ]
            }
        }

    def generate_mock_questions(self, state: MLOpsWorkflowState) -> AdaptiveQuestioningResult:
        """
        Generate realistic mock questions based on current state.

        Args:
            state: Current workflow state

        Returns:
            AdaptiveQuestioningResult with mock questions
        """
        # Determine what questions to ask based on coverage
        coverage_score = state.get("coverage_score", 0.0)
        constraints = state.get("constraints", {})

        # Select 1-3 questions based on what's missing
        selected_questions = []

        # Always ask budget if missing and coverage is low
        if coverage_score < 0.6 and not constraints.get("budget_band"):
            selected_questions.append("budget")

        # Ask scale if missing
        if coverage_score < 0.7 and not constraints.get("expected_requests_per_day"):
            selected_questions.append("scale")

        # Ask about team if we have room for more questions
        if len(selected_questions) < 2 and not constraints.get("team_size"):
            selected_questions.append("team_size")

        # Ask about data sensitivity for compliance
        if len(selected_questions) < 3 and not constraints.get("data_classification"):
            selected_questions.append("data_sensitivity")

        # Fallback questions if we need more
        if len(selected_questions) == 0:
            selected_questions = ["deployment_preference", "region"][:2]
        elif len(selected_questions) < 2:
            remaining = [k for k in self.question_templates.keys() if k not in selected_questions]
            selected_questions.extend(random.sample(remaining, min(1, len(remaining))))

        # Generate question objects
        questions = []
        for i, question_key in enumerate(selected_questions[:3]):  # Max 3 questions
            template = self.question_templates[question_key]
            question = AdaptiveQuestion(
                question_id=f"mock_q_{i+1}_{question_key}",
                question_text=template["question_text"],
                field_targets=template["field_targets"],
                priority=template["priority"],
                question_type=template["question_type"],
                choices=template.get("choices")
            )
            questions.append(question)

        # Determine if questioning should be complete
        questioning_complete = coverage_score >= 0.75 or len(questions) == 0

        # Calculate improved coverage score
        new_coverage = min(coverage_score + (len(questions) * 0.15), 1.0)

        return AdaptiveQuestioningResult(
            questions=questions,
            questioning_complete=questioning_complete,
            current_coverage=coverage_score,
            target_coverage=0.75,
            questioning_rationale=f"Generated {len(questions)} mock questions to improve coverage from {coverage_score:.1%} to ~{new_coverage:.1%}"
        )


def create_mock_adaptive_questions_agent() -> MockAdaptiveQuestionsAgent:
    """Factory function to create mock adaptive questions agent."""
    return MockAdaptiveQuestionsAgent()


def enable_mock_mode() -> bool:
    """Check if mock mode is enabled via environment variable."""
    return os.getenv("ENABLE_MOCK_AGENTS", "false").lower() in {"1", "true", "yes"}


def create_mock_state_for_testing() -> MLOpsWorkflowState:
    """Create a mock workflow state for testing HITL functionality."""
    return {
        "decision_set_id": f"test_hitl_{int(time.time())}",
        "project_id": "test_project",
        "constraints": {
            "project_description": "Build a machine learning model serving platform for real-time predictions",
            "workload_type": "ml_serving",
            "deployment_target": "cloud"
        },
        "coverage_score": 0.45,  # Low coverage to trigger questions
        "coverage_analysis": {
            "score": 0.45,
            "threshold_met": False,
            "critical_gaps": ["budget_band", "expected_requests_per_day"],
            "optional_gaps": ["team_size", "data_classification"],
            "ambiguous_fields": []
        },
        "reason_cards": [],
        "execution_order": ["intake_extract", "coverage_check"],
        "execution_round": 1,
        "questioning_history": [],
        "questioning_complete": False
    }


def create_demo_questions() -> List[Dict]:
    """Create realistic demo questions for frontend testing."""
    return [
        {
            "question_id": "demo_q1_budget",
            "question_text": "What's your monthly budget range for this MLOps platform?",
            "field_targets": ["budget_band", "monthly_budget_limit"],
            "priority": "high",
            "question_type": "choice",
            "choices": [
                "Startup budget (under $500/month)",
                "Growth budget ($500-1500/month)",
                "Enterprise budget ($1500+/month)"
            ]
        },
        {
            "question_id": "demo_q2_scale",
            "question_text": "What's your expected daily request volume?",
            "field_targets": ["expected_requests_per_day", "scale_requirements"],
            "priority": "high",
            "question_type": "choice",
            "choices": [
                "Light usage (under 1,000 requests/day)",
                "Moderate usage (1,000-10,000 requests/day)",
                "Heavy usage (10,000+ requests/day)"
            ]
        },
        {
            "question_id": "demo_q3_compliance",
            "question_text": "Do you handle any regulated or sensitive data (GDPR, HIPAA, financial)?",
            "field_targets": ["data_classification", "compliance_requirements"],
            "priority": "high",
            "question_type": "boolean"
        }
    ]


def create_demo_smart_defaults() -> Dict[str, str]:
    """Create realistic smart defaults for demo questions."""
    return {
        "demo_q1_budget": "Growth budget ($500-1500/month)",
        "demo_q2_scale": "Moderate usage (1,000-10,000 requests/day)",
        "demo_q3_compliance": "false"
    }


# Mock agent response simulation
def simulate_agent_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """Simulate realistic agent processing time."""
    if enable_mock_mode():
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)