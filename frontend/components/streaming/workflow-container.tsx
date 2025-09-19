/**
 * Workflow Container - Claude-style unified workflow display
 *
 * Manages and displays workflow steps inline with chat messages
 */

import React, { useState, useEffect } from "react";
import { Activity, AlertCircle } from "lucide-react";
import { Badge } from "../ui/badge";
import { WorkflowStep } from "./workflow-step";
import { QuestionForm } from "../hitl/question-form";
import {
  useStreamingEvents,
  ReasonCard,
  WorkflowProgress,
} from "../../hooks/useStreamingEvents";

export interface WorkflowContainerProps {
  decisionSetId: string;
  className?: string;
}

interface WorkflowStepData {
  id: string;
  title: string;
  status: "pending" | "running" | "completed" | "error";
  startTime?: string;
  endTime?: string;
  reasonCard?: ReasonCard;
  stepType: "node-event" | "reasoning";
}

export function WorkflowContainer({
  decisionSetId,
  className = "",
}: WorkflowContainerProps) {
  const [steps, setSteps] = useState<WorkflowStepData[]>([]);
  const [collapsedSteps, setCollapsedSteps] = useState<Set<string>>(new Set());

  const {
    isConnected,
    events,
    reasonCards,
    workflowProgress,
    error,
    isWorkflowActive,
    isWorkflowComplete,
    hitlState,
  } = useStreamingEvents({
    decisionSetId,
    autoConnect: true,
    reconnectAttempts: 3,
    reconnectDelay: 2000,
  });

  // Process events to build workflow steps
  useEffect(() => {
    const processedSteps = new Map<string, WorkflowStepData>();

    // Process node start/complete events to create steps
    events.forEach((event) => {
      if (event.type === "node-start") {
        const nodeId = event.data.node as string;
        const stepTitle = getStepTitle(nodeId);

        // Create only the reasoning step (human-readable title)
        processedSteps.set(`${nodeId}-reasoning`, {
          id: `${nodeId}-reasoning`,
          title: stepTitle,
          status: "running",
          startTime: event.timestamp,
          stepType: "reasoning",
        });
      }

      if (event.type === "node-complete") {
        const nodeId = event.data.node as string;

        // Update reasoning step
        const reasoningStep = processedSteps.get(`${nodeId}-reasoning`);
        if (reasoningStep) {
          processedSteps.set(`${nodeId}-reasoning`, {
            ...reasoningStep,
            status: "completed",
            endTime: event.timestamp,
          });
        }
      }
    });

    // Attach reason cards to reasoning steps
    reasonCards.forEach((reasonCard) => {
      const nodeId = reasonCard.node;
      const reasoningStepId = `${nodeId}-reasoning`;
      const existing = processedSteps.get(reasoningStepId);
      if (existing) {
        processedSteps.set(reasoningStepId, {
          ...existing,
          reasonCard,
        });
      } else {
        // Create reasoning step from reason card if no node event found
        const stepTitle = getStepTitle(nodeId);
        processedSteps.set(reasoningStepId, {
          id: reasoningStepId,
          title: stepTitle,
          status: "completed",
          startTime: reasonCard.timestamp,
          reasonCard,
          stepType: "reasoning",
        });
      }
    });

    setSteps(
      Array.from(processedSteps.values()).sort((a, b) => {
        // Sort by start time
        if (!a.startTime || !b.startTime) return 0;
        return (
          new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
        );
      }),
    );
  }, [events, reasonCards]);

  // Auto-collapse only very old completed steps (keep last 3 expanded)
  useEffect(() => {
    if (steps.length > 3) {
      const completedSteps = steps
        .filter((step) => step.status === "completed")
        .slice(0, -3) // Keep the latest 3 completed steps expanded
        .map((step) => step.id);

      setCollapsedSteps((prev) => new Set([...prev, ...completedSteps]));
    }
  }, [steps]);

  const getStepTitle = (nodeId: string): string => {
    const titles: Record<string, string> = {
      intake_extract: "Extracting and structuring project requirements",
      coverage_check: "Checking requirement coverage and gaps",
      adaptive_questions: "Generating targeted follow-up questions",
      planner: "Analyzing requirements and designing MLOps architecture",
      critic_tech: "Performing technical feasibility analysis",
      critic_cost: "Analyzing costs and budget compliance",
      policy_eval: "Evaluating architecture against policies",
      gate_hitl: "Human-in-the-loop review gate",
      architecture_agent: "Designing system architecture",
      codegen_agent: "Generating infrastructure code",
      validation_agent: "Validating generated code",
    };
    return titles[nodeId] || `Processing ${nodeId.replace(/_/g, " ")}`;
  };

  const handleStepToggle = (stepId: string) => {
    setCollapsedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stepId)) {
        newSet.delete(stepId);
      } else {
        newSet.add(stepId);
      }
      return newSet;
    });
  };

  const getWorkflowStatus = () => {
    if (error) return "error";
    if (isWorkflowComplete) return "completed";
    if (isWorkflowActive) return "running";
    return "pending";
  };

  const getStatusColor = () => {
    const status = getWorkflowStatus();
    switch (status) {
      case "running":
        return "border-blue-200 bg-blue-50";
      case "completed":
        return "border-green-200 bg-green-50";
      case "error":
        return "border-red-200 bg-red-50";
      default:
        return "border-gray-200 bg-gray-50";
    }
  };

  if (!isConnected) {
    return (
      <div
        className={`p-3 border border-yellow-200 bg-yellow-50 rounded-lg ${className}`}
      >
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-700">
            Connecting to workflow stream...
          </span>
        </div>
      </div>
    );
  }

  if (steps.length === 0) {
    return (
      <div
        className={`p-3 border border-gray-200 bg-gray-50 rounded-lg ${className}`}
      >
        <div className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-600">
            Waiting for workflow to start...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Workflow Header */}
      <div className={`p-3 border rounded-lg ${getStatusColor()}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span className="font-medium text-sm">MLOps Workflow Progress</span>
          </div>
          <div className="flex items-center space-x-2">
            {workflowProgress && (
              <Badge variant="secondary" className="text-xs">
                {workflowProgress.progress_percentage}%
              </Badge>
            )}
            <Badge
              variant="outline"
              className={`text-xs ${
                getWorkflowStatus() === "running"
                  ? "border-blue-200 text-blue-700"
                  : getWorkflowStatus() === "completed"
                    ? "border-green-200 text-green-700"
                    : getWorkflowStatus() === "error"
                      ? "border-red-200 text-red-700"
                      : "border-gray-200 text-gray-700"
              }`}
            >
              {getWorkflowStatus()}
            </Badge>
          </div>
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="space-y-2">
        {steps.map((step) => (
          <WorkflowStep
            key={step.id}
            title={step.title}
            status={step.status}
            startTime={step.startTime}
            endTime={step.endTime}
            reasonCard={step.reasonCard}
            isCollapsed={collapsedSteps.has(step.id)}
            onToggle={() => handleStepToggle(step.id)}
            stepType={step.stepType}
          />
        ))}
      </div>

      {/* HITL Questions Form */}
      {hitlState.isActive && hitlState.questions.length > 0 && (
        <div className="mt-4">
          <QuestionForm
            questions={hitlState.questions}
            smartDefaults={hitlState.smartDefaults}
            timeoutSeconds={hitlState.countdownTime || hitlState.timeoutSeconds}
            onSubmit={(responses) => {
              console.log("HITL responses submitted:", responses);
              // TODO: Send responses to backend
            }}
            onAutoApprove={() => {
              console.log("HITL auto-approved with defaults");
              // TODO: Send auto-approval to backend
            }}
          />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 border border-red-200 bg-red-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowContainer;
