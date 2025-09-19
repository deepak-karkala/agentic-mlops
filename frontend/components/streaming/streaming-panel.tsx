/**
 * StreamingPanel component that displays real-time workflow events
 *
 * Combines workflow progress, reason cards, and event stream into a cohesive UI
 */

import React, { useState, useEffect, useRef } from "react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Activity,
  Brain,
  AlertCircle,
  RefreshCw,
  Wifi,
  WifiOff,
  ChevronDown,
  ChevronUp,
  Clock,
} from "lucide-react";
import { useStreamingEvents } from "../../hooks/useStreamingEvents";
import { ReasonCard } from "./reason-card";
import { WorkflowProgress } from "./workflow-progress";

interface StreamingPanelProps {
  decisionSetId?: string;
  className?: string;
  autoConnect?: boolean;
  showProgress?: boolean;
  showReasonCards?: boolean;
  showEvents?: boolean;
}

export function StreamingPanel({
  decisionSetId,
  className = "",
  autoConnect = true,
  showProgress = true,
  showReasonCards = true,
  showEvents = true,
}: StreamingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState("progress");
  const reasonCardsEndRef = useRef<HTMLDivElement>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  const {
    isConnected,
    isConnecting,
    connectionError,
    events,
    reasonCards,
    workflowProgress,
    currentNode,
    error,
    hasEvents,
    hasReasonCards,
    isWorkflowActive,
    isWorkflowPaused,
    isWorkflowComplete,
    connect,
    disconnect,
    clearEvents,
  } = useStreamingEvents({
    decisionSetId,
    autoConnect,
    reconnectAttempts: 3,
    reconnectDelay: 2000,
  });

  // Auto-scroll to latest reason card
  useEffect(() => {
    if (activeTab === "reasoning" && reasonCardsEndRef.current) {
      reasonCardsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [reasonCards, activeTab]);

  // Auto-scroll to latest event
  useEffect(() => {
    if (activeTab === "events" && eventsEndRef.current) {
      eventsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events, activeTab]);

  // Auto-switch to reasoning tab when new reason card arrives
  useEffect(() => {
    if (reasonCards.length > 0 && activeTab === "progress") {
      setActiveTab("reasoning");
    }
  }, [reasonCards.length, activeTab]);

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return "Invalid time";
    }
  };

  // Get event type display info
  const getEventTypeInfo = (eventType: string) => {
    const types = {
      "workflow-start": {
        label: "Workflow Started",
        color: "bg-blue-100 text-blue-800",
      },
      "workflow-complete": {
        label: "Workflow Complete",
        color: "bg-green-100 text-green-800",
      },
      "workflow-paused": {
        label: "Workflow Paused",
        color: "bg-yellow-100 text-yellow-800",
      },
      "node-start": {
        label: "Node Start",
        color: "bg-purple-100 text-purple-800",
      },
      "node-complete": {
        label: "Node Complete",
        color: "bg-green-100 text-green-800",
      },
      "reason-card": {
        label: "Reason Card",
        color: "bg-blue-100 text-blue-800",
      },
      error: { label: "Error", color: "bg-red-100 text-red-800" },
      heartbeat: { label: "Heartbeat", color: "bg-gray-100 text-gray-800" },
    };
    return (
      types[eventType as keyof typeof types] || {
        label: eventType,
        color: "bg-gray-100 text-gray-800",
      }
    );
  };

  if (!decisionSetId) {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="text-center text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No active workflow session</p>
          <p className="text-xs mt-1">Start a chat to see real-time progress</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      {/* Header */}
      <div className="border-b p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-4 w-4 text-primary" />
            <span className="font-medium text-sm">Real-time Updates</span>
            {/* Connection Status */}
            <Badge
              variant="outline"
              className={`text-xs ${
                isConnected
                  ? "bg-green-100 text-green-800 border-green-200"
                  : isConnecting
                    ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                    : "bg-red-100 text-red-800 border-red-200"
              }`}
            >
              {isConnected ? (
                <>
                  <Wifi className="h-2 w-2 mr-1" />
                  Connected
                </>
              ) : isConnecting ? (
                <>
                  <RefreshCw className="h-2 w-2 mr-1 animate-spin" />
                  Connecting
                </>
              ) : (
                <>
                  <WifiOff className="h-2 w-2 mr-1" />
                  Disconnected
                </>
              )}
            </Badge>
          </div>
          <div className="flex items-center space-x-1">
            {/* Reconnect Button */}
            {!isConnected && !isConnecting && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => connect(decisionSetId)}
                className="h-6 px-2"
              >
                <RefreshCw className="h-3 w-3" />
              </Button>
            )}
            {/* Expand/Collapse */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-6 px-1"
            >
              {isExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>

        {/* Connection Error */}
        {(error || connectionError) && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs flex items-center space-x-1">
            <AlertCircle className="h-3 w-3" />
            <span>{error || "Connection failed"}</span>
          </div>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-3">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              {showProgress && (
                <TabsTrigger value="progress" className="text-xs">
                  Progress
                  {isWorkflowActive && (
                    <div className="ml-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  )}
                </TabsTrigger>
              )}
              {showReasonCards && (
                <TabsTrigger value="reasoning" className="text-xs">
                  Reasoning
                  {hasReasonCards && (
                    <Badge
                      variant="secondary"
                      className="ml-1 text-xs h-4 px-1"
                    >
                      {reasonCards.length}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              {showEvents && (
                <TabsTrigger value="events" className="text-xs">
                  Events
                  {hasEvents && (
                    <Badge
                      variant="secondary"
                      className="ml-1 text-xs h-4 px-1"
                    >
                      {events.length}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
            </TabsList>

            {/* Progress Tab */}
            {showProgress && (
              <TabsContent value="progress" className="mt-3">
                {workflowProgress ? (
                  <WorkflowProgress
                    progress={workflowProgress}
                    currentNode={currentNode}
                  />
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <Activity className="h-6 w-6 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No workflow in progress</p>
                  </div>
                )}
              </TabsContent>
            )}

            {/* Reasoning Tab */}
            {showReasonCards && (
              <TabsContent value="reasoning" className="mt-3">
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {reasonCards.length > 0 ? (
                    reasonCards.map((card, index) => (
                      <ReasonCard key={index} reasonCard={card} />
                    ))
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <Brain className="h-6 w-6 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No reasoning cards yet</p>
                      <p className="text-xs mt-1">
                        Agent rationale will appear here
                      </p>
                    </div>
                  )}
                  <div ref={reasonCardsEndRef} />
                </div>
              </TabsContent>
            )}

            {/* Events Tab */}
            {showEvents && (
              <TabsContent value="events" className="mt-3">
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {events.length > 0 ? (
                    events.map((event, index) => {
                      const eventInfo = getEventTypeInfo(event.type);
                      return (
                        <div
                          key={index}
                          className="flex items-start space-x-2 p-2 bg-muted/50 rounded text-xs"
                        >
                          <div className="flex items-center space-x-1 min-w-0 flex-1">
                            <Badge
                              variant="outline"
                              className={`${eventInfo.color} text-xs`}
                            >
                              {eventInfo.label}
                            </Badge>
                            {event.message && (
                              <span className="text-muted-foreground truncate">
                                {event.message}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-1 text-muted-foreground flex-shrink-0">
                            <Clock className="h-2 w-2" />
                            <span>{formatTimestamp(event.timestamp)}</span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <AlertCircle className="h-6 w-6 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No events yet</p>
                      <p className="text-xs mt-1">
                        System events will appear here
                      </p>
                    </div>
                  )}
                  <div ref={eventsEndRef} />
                </div>
              </TabsContent>
            )}
          </Tabs>
        </div>
      )}
    </Card>
  );
}
