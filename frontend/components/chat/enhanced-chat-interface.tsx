/**
 * Enhanced chat interface with real-time streaming support
 *
 * Integrates with the async API and displays streaming events in real-time
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Message, ChatState } from "../../types/chat";
import { WorkflowContainer } from "../streaming/workflow-container";

// Extended message type for async workflow tracking
interface EnhancedMessage extends Message {
  decisionSetId?: string;
  jobId?: string;
  jobStatus?: string;
  isStreamingActive?: boolean;
}

interface EnhancedChatState extends Omit<ChatState, "messages"> {
  messages: EnhancedMessage[];
  currentDecisionSetId?: string;
}

export default function EnhancedChatInterface() {
  const [chatState, setChatState] = useState<EnhancedChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const jobPollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (jobPollingIntervalRef.current) {
        clearInterval(jobPollingIntervalRef.current);
        jobPollingIntervalRef.current = null;
      }
    };
  }, []);

  // Poll job status
  const pollJobStatus = async (jobId: string, decisionSetId: string) => {
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${apiBaseUrl}/api/jobs/${jobId}/status`);
      if (!response.ok) {
        throw new Error(`Job status check failed: ${response.status}`);
      }

      const jobStatus = await response.json();

      // Update message with job status
      setChatState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.jobId === jobId
            ? {
                ...msg,
                jobStatus: jobStatus.status,
                isStreamingActive: jobStatus.status === "processing",
              }
            : msg,
        ),
      }));

      // Stop polling if job is complete or failed
      if (jobStatus.status === "completed" || jobStatus.status === "failed") {
        // Clear the interval immediately to stop further polling
        if (jobPollingIntervalRef.current) {
          clearInterval(jobPollingIntervalRef.current);
          jobPollingIntervalRef.current = null;
        }

        setChatState((prev) => ({
          ...prev,
          isLoading: false,
        }));

        // If completed, add a completion message (only if not already added)
        if (jobStatus.status === "completed") {
          setChatState((prev) => {
            // Check if completion message already exists for this jobId
            const hasCompletionMessage = prev.messages.some(
              (msg) =>
                msg.content.includes("MLOps architecture design completed") &&
                msg.decisionSetId === decisionSetId,
            );

            if (!hasCompletionMessage) {
              const completionMessage: EnhancedMessage = {
                id: Date.now().toString(),
                role: "assistant",
                content:
                  "✅ MLOps architecture design completed! The workflow has finished successfully.",
                timestamp: new Date(),
                decisionSetId,
              };

              return {
                ...prev,
                messages: [...prev.messages, completionMessage],
              };
            }

            return prev;
          });
        }
      }
    } catch (error) {
      console.error("Job status polling failed:", error);
      // Stop polling on error
      if (jobPollingIntervalRef.current) {
        clearInterval(jobPollingIntervalRef.current);
        jobPollingIntervalRef.current = null;
      }

      setChatState((prev) => ({
        ...prev,
        isLoading: false,
        error: `Job tracking failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      }));
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || chatState.isLoading) return;

    const userMessage: EnhancedMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setChatState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    setInputValue("");

    try {
      // Call the async API
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${apiBaseUrl}/api/chat/async`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [{ role: "user", content: content.trim() }],
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API request failed: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();
      const { decision_set_id, thread_id, job_id, status } = data;

      // Create system message about job creation
      const systemMessage: EnhancedMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `🚀 Started MLOps architecture design workflow! You can track real-time progress in the panel below.

**Job Details:**
- Decision Set ID: ${decision_set_id}
- Job ID: ${job_id}
- Status: ${status}

Watch the Real-time Updates panel for live agent reasoning and progress updates.`,
        timestamp: new Date(),
        decisionSetId: decision_set_id,
        jobId: job_id,
        jobStatus: status,
        isStreamingActive: true,
      };

      setChatState((prev) => ({
        ...prev,
        messages: [...prev.messages, systemMessage],
        currentDecisionSetId: decision_set_id,
        isLoading: status === "completed", // Keep loading if not yet completed
      }));

      // Start job status polling
      jobPollingIntervalRef.current = setInterval(() => {
        pollJobStatus(job_id, decision_set_id);
      }, 3000); // Poll every 3 seconds
    } catch (error) {
      console.error("API call failed:", error);
      setChatState((prev) => ({
        ...prev,
        isLoading: false,
        error: `Failed to send message: ${error instanceof Error ? error.message : "Unknown error"}`,
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  // Get job status badge info
  const getJobStatusBadge = (status?: string) => {
    switch (status) {
      case "pending":
        return {
          variant: "outline" as const,
          color: "text-yellow-600",
          text: "Pending",
        };
      case "processing":
        return {
          variant: "default" as const,
          color: "text-blue-600",
          text: "Processing",
        };
      case "completed":
        return {
          variant: "outline" as const,
          color: "text-green-600",
          text: "Completed",
        };
      case "failed":
        return {
          variant: "destructive" as const,
          color: "text-red-600",
          text: "Failed",
        };
      default:
        return {
          variant: "secondary" as const,
          color: "text-gray-600",
          text: status || "Unknown",
        };
    }
  };

  return (
    <div className="flex flex-col h-full max-w-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatState.messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-center">
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold text-muted-foreground">
                Welcome to Agentic MLOps
              </h2>
              <p className="text-muted-foreground">
                Start a conversation to design your MLOps infrastructure
              </p>
              <p className="text-sm text-muted-foreground">
                Watch real-time agent reasoning and progress updates below
              </p>
            </div>
          </div>
        )}

        {chatState.messages.map((message, index) => {
          // Track which decisionSetIds we've already shown WorkflowContainers for
          const isFirstMessageWithDecisionSetId =
            message.role === "assistant" &&
            message.decisionSetId &&
            !chatState.messages
              .slice(0, index)
              .some((m) => m.decisionSetId === message.decisionSetId);

          return (
            <div key={message.id} className="space-y-2">
              <div
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <Card
                  className={`max-w-[80%] p-4 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs opacity-60">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.jobStatus && (
                      <Badge
                        variant={getJobStatusBadge(message.jobStatus).variant}
                        className="text-xs"
                      >
                        {message.isStreamingActive && (
                          <div className="w-2 h-2 bg-current rounded-full animate-pulse mr-1" />
                        )}
                        {getJobStatusBadge(message.jobStatus).text}
                      </Badge>
                    )}
                  </div>
                </Card>
              </div>

              {/* Show workflow container only for the first assistant message with each decisionSetId */}
              {isFirstMessageWithDecisionSetId && (
                <div className="ml-4">
                  <WorkflowContainer
                    decisionSetId={message.decisionSetId}
                    className="mt-3"
                  />
                </div>
              )}
            </div>
          );
        })}

        {chatState.isLoading && (
          <div className="flex justify-start">
            <Card className="bg-muted p-4 flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">
                Processing workflow...
              </span>
            </Card>
          </div>
        )}

        {chatState.error && (
          <div className="flex justify-center">
            <Card className="bg-destructive/10 border-destructive/20 p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <p className="text-destructive text-sm">{chatState.error}</p>
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t bg-background p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your MLOps requirements..."
            disabled={chatState.isLoading}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!inputValue.trim() || chatState.isLoading}
            size="icon"
          >
            {chatState.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2">
          Real-time agent reasoning will appear above during workflow execution
        </p>
      </div>
    </div>
  );
}
