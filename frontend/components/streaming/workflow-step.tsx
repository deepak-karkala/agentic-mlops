/**
 * Workflow Step component - Claude-style collapsible sections for inline workflow display
 *
 * Shows real-time reasoning and progress as expandable cards within the chat flow
 */

import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Clock,
  Brain,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { ReasonCard } from "../../hooks/useStreamingEvents";

export interface WorkflowStepProps {
  title: string;
  status: "pending" | "running" | "completed" | "error";
  startTime?: string;
  endTime?: string;
  reasonCard?: ReasonCard;
  isCollapsed?: boolean;
  onToggle?: () => void;
  stepType?: "node-event" | "reasoning"; // New prop to differentiate step types
}

export function WorkflowStep({
  title,
  status,
  startTime,
  endTime,
  reasonCard,
  isCollapsed = false,
  onToggle,
  stepType = "reasoning",
}: WorkflowStepProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(isCollapsed);

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4 text-gray-400" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    const baseColors = {
      pending: "border-gray-200 bg-gray-50",
      running: "border-blue-200 bg-blue-50",
      completed: "border-green-200 bg-green-50",
      error: "border-red-200 bg-red-50",
    };

    // Different styling for node events vs reasoning steps
    if (stepType === "node-event") {
      switch (status) {
        case "pending":
          return "border-slate-200 bg-slate-50";
        case "running":
          return "border-indigo-200 bg-indigo-50";
        case "completed":
          return "border-emerald-200 bg-emerald-50";
        case "error":
          return "border-rose-200 bg-rose-50";
        default:
          return "border-slate-200 bg-slate-50";
      }
    }

    return baseColors[status] || baseColors["pending"];
  };

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return "";
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return "";
    }
  };

  const isExpanded = onToggle ? !isCollapsed : !internalCollapsed;
  const hasExpandableContent = reasonCard !== undefined;

  return (
    <Card className={`transition-all duration-200 ${getStatusColor()}`}>
      {/* Step Header */}
      <div
        className={`flex items-center justify-between p-3 transition-colors ${
          hasExpandableContent
            ? "cursor-pointer hover:bg-white/50"
            : "cursor-default"
        }`}
        onClick={hasExpandableContent ? handleToggle : undefined}
      >
        <div className="flex items-center space-x-3 flex-1">
          {getStatusIcon()}
          <div className="flex items-center space-x-2 flex-1">
            {/* Visual indicator for step type */}
            {stepType === "node-event" ? (
              <div className="w-2 h-2 rounded-full bg-slate-400"></div>
            ) : reasonCard ? (
              <Brain className="h-4 w-4 text-purple-500" />
            ) : (
              <div className="w-2 h-2 rounded-full bg-purple-400"></div>
            )}
            <span
              className={`text-sm ${
                stepType === "node-event"
                  ? "text-slate-600 font-normal"
                  : "font-medium"
              }`}
            >
              {title}
            </span>
            {status === "running" && (
              <Badge
                variant="secondary"
                className={`text-xs px-2 py-1 ${
                  stepType === "node-event"
                    ? "bg-indigo-100 text-indigo-800"
                    : "bg-blue-100 text-blue-800"
                }`}
              >
                Processing...
              </Badge>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {startTime && (
            <span className="text-xs text-muted-foreground">
              {formatTime(startTime)}
            </span>
          )}
          {/* Only show arrow if there's expandable content */}
          {hasExpandableContent &&
            (isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            ))}
        </div>
      </div>

      {/* Expandable Content */}
      {isExpanded && reasonCard && (
        <div className="px-3 pb-3">
          <div className="border-t pt-3 space-y-3">
            {/* Reasoning Section */}
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Reasoning
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {reasonCard.reasoning}
              </p>
            </div>

            {/* Decision Section */}
            {reasonCard.decision && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                  Decision
                </h4>
                <p className="text-sm font-medium text-gray-900">
                  {reasonCard.decision}
                </p>
              </div>
            )}

            {/* Confidence & Priority */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {reasonCard.confidence && (
                  <Badge variant="outline" className="text-xs">
                    Confidence: {Math.round(reasonCard.confidence * 100)}%
                  </Badge>
                )}
                <Badge
                  variant="outline"
                  className={`text-xs ${
                    reasonCard.priority === "critical"
                      ? "border-red-200 text-red-700"
                      : reasonCard.priority === "high"
                        ? "border-yellow-200 text-yellow-700"
                        : "border-gray-200 text-gray-700"
                  }`}
                >
                  {reasonCard.priority}
                </Badge>
              </div>

              {reasonCard.duration_ms && (
                <span className="text-xs text-muted-foreground">
                  {reasonCard.duration_ms}ms
                </span>
              )}
            </div>

            {/* Alternatives Considered */}
            {reasonCard.alternatives_considered &&
              reasonCard.alternatives_considered.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    Alternatives Considered
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {reasonCard.alternatives_considered.map((alt, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-muted-foreground">•</span>
                        <span>{alt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Agent Info */}
            <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
              <span>Agent: {reasonCard.agent}</span>
              <span>Node: {reasonCard.node}</span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

export default WorkflowStep;
