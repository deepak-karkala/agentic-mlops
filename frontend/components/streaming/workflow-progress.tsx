/**
 * WorkflowProgress component for displaying real-time workflow execution status
 *
 * Shows current node, completed nodes, progress percentage, and overall status
 */

import React from "react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  PlayCircle,
  CheckCircle2,
  PauseCircle,
  XCircle,
  Clock,
  Activity,
  AlertCircle,
} from "lucide-react";
import { WorkflowProgress as WorkflowProgressType } from "../../hooks/useStreamingEvents";

interface WorkflowProgressProps {
  progress: WorkflowProgressType;
  currentNode?: string | null;
  className?: string;
}

export function WorkflowProgress({
  progress,
  currentNode,
  className = "",
}: WorkflowProgressProps) {
  // Get status icon and color
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "started":
      case "running":
        return PlayCircle;
      case "paused":
        return PauseCircle;
      case "completed":
        return CheckCircle2;
      case "error":
        return XCircle;
      default:
        return Activity;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "started":
      case "running":
        return "text-blue-600 bg-blue-100 border-blue-200";
      case "paused":
        return "text-yellow-600 bg-yellow-100 border-yellow-200";
      case "completed":
        return "text-green-600 bg-green-100 border-green-200";
      case "error":
        return "text-red-600 bg-red-100 border-red-200";
      default:
        return "text-gray-600 bg-gray-100 border-gray-200";
    }
  };

  const getProgressBarColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "error":
        return "bg-red-500";
      case "paused":
        return "bg-yellow-500";
      default:
        return "bg-blue-500";
    }
  };

  // Format estimated time remaining
  const formatTimeRemaining = (timeMs?: number) => {
    if (!timeMs) return null;
    const seconds = Math.ceil(timeMs / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.ceil(seconds / 60);
    return `${minutes}m`;
  };

  // Get node display name
  const getNodeDisplayName = (node: string) => {
    const nodeNames: Record<string, string> = {
      planner: "Planning",
      critic_tech: "Technical Analysis",
      critic_cost: "Cost Analysis",
      policy_eval: "Policy Evaluation",
      gate_hitl: "Human Approval",
      codegen: "Code Generation",
      validators: "Validation",
    };
    return nodeNames[node] || node;
  };

  const StatusIcon = getStatusIcon(progress.status);

  return (
    <Card className={`p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">Workflow Progress</span>
        </div>
        <Badge variant="outline" className={getStatusColor(progress.status)}>
          <StatusIcon className="h-3 w-3 mr-1" />
          {progress.status}
        </Badge>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          <span>Progress</span>
          <span>{progress.progress_percentage.toFixed(0)}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-2 transition-all duration-300 ${getProgressBarColor(progress.status)}`}
            style={{ width: `${progress.progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Current Node */}
      {(currentNode || progress.current_node) && (
        <div className="mb-3">
          <div className="flex items-center space-x-2 mb-1">
            <PlayCircle className="h-3 w-3 text-blue-500" />
            <span className="text-xs font-medium text-muted-foreground">
              Current Task
            </span>
          </div>
          <div className="pl-5">
            <Badge variant="secondary" className="text-xs">
              {getNodeDisplayName(currentNode || progress.current_node!)}
            </Badge>
          </div>
        </div>
      )}

      {/* Completed Nodes */}
      {progress.nodes_completed.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center space-x-2 mb-1">
            <CheckCircle2 className="h-3 w-3 text-green-500" />
            <span className="text-xs font-medium text-muted-foreground">
              Completed ({progress.nodes_completed.length})
            </span>
          </div>
          <div className="pl-5 flex flex-wrap gap-1">
            {progress.nodes_completed.map((node, index) => (
              <Badge
                key={index}
                variant="outline"
                className="text-xs bg-green-50 border-green-200 text-green-700"
              >
                {getNodeDisplayName(node)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Remaining Nodes */}
      {progress.nodes_remaining.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center space-x-2 mb-1">
            <AlertCircle className="h-3 w-3 text-gray-500" />
            <span className="text-xs font-medium text-muted-foreground">
              Remaining ({progress.nodes_remaining.length})
            </span>
          </div>
          <div className="pl-5 flex flex-wrap gap-1">
            {progress.nodes_remaining.map((node, index) => (
              <Badge
                key={index}
                variant="outline"
                className="text-xs text-muted-foreground"
              >
                {getNodeDisplayName(node)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Estimated Time Remaining */}
      {progress.estimated_time_remaining_ms &&
        progress.status === "running" && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>Estimated time remaining</span>
            </div>
            <span className="font-medium">
              {formatTimeRemaining(progress.estimated_time_remaining_ms)}
            </span>
          </div>
        )}

      {/* Status Message */}
      {progress.status === "paused" && (
        <div className="flex items-center space-x-2 pt-2 border-t text-xs text-yellow-600">
          <PauseCircle className="h-3 w-3" />
          <span>Workflow paused - waiting for human input</span>
        </div>
      )}

      {progress.status === "error" && (
        <div className="flex items-center space-x-2 pt-2 border-t text-xs text-red-600">
          <XCircle className="h-3 w-3" />
          <span>Workflow encountered an error</span>
        </div>
      )}

      {progress.status === "completed" && (
        <div className="flex items-center space-x-2 pt-2 border-t text-xs text-green-600">
          <CheckCircle2 className="h-3 w-3" />
          <span>Workflow completed successfully</span>
        </div>
      )}
    </Card>
  );
}
