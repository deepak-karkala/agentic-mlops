/**
 * ReasonCard component for displaying agent reasoning in real-time
 *
 * Shows detailed rationale from agents including confidence scores,
 * alternatives considered, and structured decision outputs
 */

import React from "react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Brain,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { ReasonCard as ReasonCardType } from "../../hooks/useStreamingEvents";

interface ReasonCardProps {
  reasonCard: ReasonCardType;
  className?: string;
}

export function ReasonCard({ reasonCard, className = "" }: ReasonCardProps) {
  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return "Invalid time";
    }
  };

  // Format duration
  const formatDuration = (durationMs?: number) => {
    if (!durationMs) return null;
    if (durationMs < 1000) return `${durationMs}ms`;
    return `${(durationMs / 1000).toFixed(1)}s`;
  };

  // Get agent color
  const getAgentColor = (agent: string) => {
    const colors = {
      planner: "bg-blue-100 text-blue-800 border-blue-200",
      tech_critic: "bg-purple-100 text-purple-800 border-purple-200",
      cost_critic: "bg-green-100 text-green-800 border-green-200",
      policy_engine: "bg-red-100 text-red-800 border-red-200",
      codegen: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
    return (
      colors[agent as keyof typeof colors] ||
      "bg-gray-100 text-gray-800 border-gray-200"
    );
  };

  // Get priority color
  const getPriorityColor = (
    priority: string,
  ): "secondary" | "destructive" | "default" | "outline" => {
    const colors: Record<
      string,
      "secondary" | "destructive" | "default" | "outline"
    > = {
      critical: "destructive",
      high: "default",
      medium: "secondary",
      low: "outline",
    };
    return colors[priority] || "secondary";
  };

  // Get confidence color
  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "text-gray-500";
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  // Get confidence icon
  const getConfidenceIcon = (confidence?: number) => {
    if (!confidence) return AlertCircle;
    if (confidence >= 0.8) return CheckCircle;
    if (confidence >= 0.6) return Target;
    return AlertCircle;
  };

  const ConfidenceIcon = getConfidenceIcon(reasonCard.confidence);

  return (
    <Card className={`p-4 space-y-3 ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="h-4 w-4 text-muted-foreground" />
          <Badge variant="outline" className={getAgentColor(reasonCard.agent)}>
            {reasonCard.agent}
          </Badge>
          <Badge variant={getPriorityColor(reasonCard.priority)}>
            {reasonCard.priority}
          </Badge>
        </div>
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{formatTimestamp(reasonCard.timestamp)}</span>
          {reasonCard.duration_ms && (
            <span>• {formatDuration(reasonCard.duration_ms)}</span>
          )}
        </div>
      </div>

      {/* Decision */}
      <div>
        <div className="flex items-center space-x-2 mb-1">
          <Target className="h-4 w-4 text-primary" />
          <span className="font-medium text-sm">Decision</span>
        </div>
        <p className="text-sm pl-6 font-medium text-foreground">
          {reasonCard.decision}
        </p>
      </div>

      {/* Reasoning */}
      <div>
        <div className="flex items-center space-x-2 mb-1">
          <Brain className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">Reasoning</span>
        </div>
        <p className="text-sm pl-6 text-muted-foreground leading-relaxed">
          {reasonCard.reasoning}
        </p>
      </div>

      {/* Confidence */}
      {reasonCard.confidence !== undefined && (
        <div className="flex items-center justify-between pl-6">
          <div className="flex items-center space-x-2">
            <ConfidenceIcon
              className={`h-4 w-4 ${getConfidenceColor(reasonCard.confidence)}`}
            />
            <span className="text-sm text-muted-foreground">Confidence</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-16 h-2 bg-gray-200 rounded-full">
              <div
                className={`h-2 rounded-full ${
                  reasonCard.confidence >= 0.8
                    ? "bg-green-500"
                    : reasonCard.confidence >= 0.6
                      ? "bg-yellow-500"
                      : "bg-red-500"
                }`}
                style={{ width: `${reasonCard.confidence * 100}%` }}
              />
            </div>
            <span
              className={`text-xs font-medium ${getConfidenceColor(reasonCard.confidence)}`}
            >
              {(reasonCard.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}

      {/* Alternatives Considered */}
      {reasonCard.alternatives_considered &&
        reasonCard.alternatives_considered.length > 0 && (
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">
                Alternatives Considered
              </span>
            </div>
            <div className="pl-6">
              <ul className="text-sm text-muted-foreground space-y-1">
                {reasonCard.alternatives_considered.map((alt, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-xs text-muted-foreground mt-0.5">
                      •
                    </span>
                    <span>{alt}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

      {/* Key Outputs */}
      {reasonCard.outputs && Object.keys(reasonCard.outputs).length > 0 && (
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="font-medium text-sm">Key Outputs</span>
          </div>
          <div className="pl-6 space-y-1">
            {Object.entries(reasonCard.outputs).map(([key, value]) => (
              <div key={key} className="flex items-start space-x-2 text-sm">
                <span className="text-muted-foreground min-w-0 flex-shrink-0">
                  {key}:
                </span>
                <span className="text-foreground break-words">
                  {typeof value === "object"
                    ? JSON.stringify(value, null, 2)
                    : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category */}
      <div className="flex items-center justify-between pt-2 border-t">
        <Badge variant="outline" className="text-xs">
          {reasonCard.category}
        </Badge>
        {reasonCard.node && (
          <span className="text-xs text-muted-foreground">
            Node: {reasonCard.node}
          </span>
        )}
      </div>
    </Card>
  );
}
